import { NextResponse } from 'next/server';
import { getSupabaseAdmin, getAuthUser, getUserProfile } from '@/lib/supabase-server';
import { writeFile, unlink, mkdir, access } from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const TEMP_DIR = '/tmp/docxl_processing';

// Ensure temp directory exists
async function ensureTempDir() {
  try { await access(TEMP_DIR); } catch { await mkdir(TEMP_DIR, { recursive: true }); }
}

// CORS headers
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}

function jsonResponse(body, status = 200) {
  return NextResponse.json(body, { status, headers: corsHeaders() });
}

// =============================================
// AUTH HANDLERS (Supabase Auth - no more JWT/bcrypt)
// =============================================

async function handleRegister(request) {
  try {
    const body = await request.json();
    const { email, password, name } = body;
    if (!email || !password) return jsonResponse({ error: 'Email and password required' }, 400);

    const supabase = getSupabaseAdmin();
    const { data, error } = await supabase.auth.admin.createUser({
      email: email.toLowerCase(),
      password,
      email_confirm: true,
      user_metadata: { full_name: name || email.split('@')[0] },
    });

    if (error) {
      if (error.message?.includes('already been registered') || error.message?.includes('already exists')) {
        return jsonResponse({ error: 'Email already registered' }, 409);
      }
      return jsonResponse({ error: error.message }, 400);
    }

    // Generate a session token for the new user
    const { data: signInData, error: signInError } = await supabase.auth.admin.generateLink({
      type: 'magiclink',
      email: email.toLowerCase(),
    });

    // Sign in the user to get a session
    // We use admin.createUser with email_confirm:true so the user can sign in immediately
    // The frontend will sign in right after register
    const profile = await getUserProfile(data.user.id);

    return jsonResponse({
      user: {
        id: data.user.id,
        email: data.user.email,
        name: name || email.split('@')[0],
        plan: profile?.plan || 'free',
        credits_remaining: profile?.credits ?? 5,
      },
      message: 'Account created. Please sign in.',
    }, 201);
  } catch (error) {
    console.error('Register error:', error);
    return jsonResponse({ error: 'Registration failed' }, 500);
  }
}

async function handleLogin(request) {
  try {
    const body = await request.json();
    const { email, password } = body;
    if (!email || !password) return jsonResponse({ error: 'Email and password required' }, 400);

    const supabase = getSupabaseAdmin();

    // Use the anon client approach: create a temporary client to sign in
    const { createClient } = await import('@supabase/supabase-js');
    const anonClient = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
      { auth: { autoRefreshToken: false, persistSession: false } }
    );

    const { data, error } = await anonClient.auth.signInWithPassword({
      email: email.toLowerCase(),
      password,
    });

    if (error) {
      return jsonResponse({ error: 'Invalid credentials' }, 401);
    }

    const profile = await getUserProfile(data.user.id);

    return jsonResponse({
      token: data.session.access_token,
      refresh_token: data.session.refresh_token,
      user: {
        id: data.user.id,
        email: data.user.email,
        name: profile?.full_name || data.user.user_metadata?.full_name || data.user.email,
        plan: profile?.plan || 'free',
        credits_remaining: profile?.credits ?? 5,
      },
    });
  } catch (error) {
    console.error('Login error:', error);
    return jsonResponse({ error: 'Login failed' }, 500);
  }
}

async function handleGetMe(request) {
  const user = await getAuthUser(request);
  if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

  const profile = await getUserProfile(user.id);
  if (!profile) return jsonResponse({ error: 'Profile not found' }, 404);

  return jsonResponse({
    user: {
      id: user.id,
      email: user.email,
      name: profile.full_name || user.user_metadata?.full_name || user.email,
      plan: profile.plan,
      credits_remaining: profile.credits,
      created_at: profile.created_at,
    },
  });
}

// =============================================
// FILE UPLOAD (Supabase Storage)
// =============================================

async function handleUpload(request) {
  try {
    const user = await getAuthUser(request);
    if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

    const profile = await getUserProfile(user.id);
    if (!profile || profile.credits <= 0) {
      return jsonResponse({ error: 'No credits remaining. Please upgrade to Pro.' }, 403);
    }

    const formData = await request.formData();
    const file = formData.get('file');
    if (!file) return jsonResponse({ error: 'No file provided' }, 400);

    const ext = path.extname(file.name).toLowerCase();
    const validExts = ['.pdf', '.jpg', '.jpeg', '.png', '.webp'];
    if (!validExts.includes(ext)) {
      return jsonResponse({ error: 'Invalid file type. Supported: PDF, JPG, PNG, WEBP' }, 400);
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      return jsonResponse({ error: 'File too large. Maximum 10MB allowed.' }, 400);
    }

    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const sanitized = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
    const storagePath = `${user.id}/${Date.now()}_${sanitized}`;

    const supabase = getSupabaseAdmin();

    // Upload to Supabase Storage
    const { data: storageData, error: storageError } = await supabase.storage
      .from('uploads')
      .upload(storagePath, buffer, {
        contentType: file.type || 'application/octet-stream',
        upsert: false,
      });

    if (storageError) {
      console.error('Storage upload error:', storageError);
      return jsonResponse({ error: 'File upload failed: ' + storageError.message }, 500);
    }

    // Determine file type
    let fileType = 'other';
    if (ext === '.pdf') fileType = 'invoice';
    else fileType = 'image';

    // Insert upload record
    const { data: uploadRecord, error: dbError } = await supabase
      .from('uploads')
      .insert({
        user_id: user.id,
        file_name: file.name,
        file_path: storagePath,
        file_size: file.size,
        file_type: fileType,
        mime_type: file.type || 'application/octet-stream',
        status: 'uploaded',
      })
      .select()
      .single();

    if (dbError) {
      console.error('DB insert error:', dbError);
      // Cleanup storage
      await supabase.storage.from('uploads').remove([storagePath]);
      return jsonResponse({ error: 'Failed to create upload record' }, 500);
    }

    return jsonResponse({
      upload: {
        id: uploadRecord.id,
        file_name: uploadRecord.file_name,
        status: uploadRecord.status,
        file_type: uploadRecord.file_type,
        created_at: uploadRecord.created_at,
      },
    }, 201);
  } catch (error) {
    console.error('Upload error:', error);
    return jsonResponse({ error: 'Upload failed: ' + error.message }, 500);
  }
}

// =============================================
// AI PROCESSING
// =============================================

async function handleProcess(request) {
  try {
    const user = await getAuthUser(request);
    if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

    const body = await request.json();
    const { upload_id } = body;
    if (!upload_id) return jsonResponse({ error: 'upload_id required' }, 400);

    const supabase = getSupabaseAdmin();

    // Fetch upload record
    const { data: upload, error: fetchErr } = await supabase
      .from('uploads')
      .select('*')
      .eq('id', upload_id)
      .eq('user_id', user.id)
      .single();

    if (fetchErr || !upload) return jsonResponse({ error: 'Upload not found' }, 404);
    if (upload.status === 'processing') return jsonResponse({ error: 'Already processing' }, 400);

    // Set status to processing
    await supabase.from('uploads').update({ status: 'processing' }).eq('id', upload_id);

    try {
      // Download file from Supabase Storage to temp
      const { data: fileBlob, error: dlErr } = await supabase.storage
        .from('uploads')
        .download(upload.file_path);

      if (dlErr || !fileBlob) {
        throw new Error('Failed to download file from storage: ' + (dlErr?.message || 'unknown'));
      }

      await ensureTempDir();
      const tempFilePath = path.join(TEMP_DIR, `${upload_id}${path.extname(upload.file_name)}`);
      const fileBuffer = Buffer.from(await fileBlob.arrayBuffer());
      await writeFile(tempFilePath, fileBuffer);

      // Call Python extraction script
      const { stdout, stderr } = await execAsync(
        `cd /app && EMERGENT_LLM_KEY="${process.env.EMERGENT_LLM_KEY}" /root/.venv/bin/python3 scripts/extract.py "${tempFilePath}"`,
        { timeout: 120000, maxBuffer: 10 * 1024 * 1024 }
      );

      // Cleanup temp file
      try { await unlink(tempFilePath); } catch (e) { /* ignore */ }

      if (stderr) console.error('Extract stderr:', stderr);

      let result;
      try {
        result = JSON.parse(stdout.trim());
      } catch (parseError) {
        throw new Error('Failed to parse extraction result');
      }

      if (result.error) {
        await supabase.from('uploads').update({ status: 'failed', error_message: result.error }).eq('id', upload_id);
        return jsonResponse({ error: result.error }, 422);
      }

      // Normalize rows
      const normalizedRows = (result.rows || []).map((row, index) => ({
        row_number: index + 1,
        date: row.date || '',
        description: row.description || '',
        amount: parseFloat(row.amount) || 0,
        type: row.type || 'debit',
        category: row.category || '',
        gst: parseFloat(row.gst) || 0,
        reference: row.reference || '',
      }));

      const summary = result.summary || {
        total_rows: normalizedRows.length,
        total_amount: normalizedRows.reduce((sum, r) => sum + r.amount, 0),
      };

      // Insert result record
      const { data: resultRecord, error: resultErr } = await supabase
        .from('results')
        .insert({
          upload_id,
          document_type: result.document_type || 'other',
          structured_json: { rows: normalizedRows },
          summary,
          confidence_score: 0.85,
        })
        .select()
        .single();

      if (resultErr) {
        console.error('Result insert error:', resultErr);
        throw new Error('Failed to save extraction result');
      }

      // Update upload status
      await supabase.from('uploads').update({ status: 'completed' }).eq('id', upload_id);

      // Deduct credit
      const profile = await getUserProfile(user.id);
      if (profile) {
        await supabase
          .from('profiles')
          .update({ credits: Math.max(0, profile.credits - 1) })
          .eq('id', user.id);
      }

      // Log usage
      await supabase.from('usage_logs').insert({
        user_id: user.id,
        action: 'process',
        credits_used: 1,
        upload_id,
      });

      return jsonResponse({
        result: {
          id: resultRecord.id,
          upload_id,
          document_type: resultRecord.document_type,
          rows: normalizedRows,
          summary,
          confidence_score: resultRecord.confidence_score,
        },
      });
    } catch (execError) {
      console.error('Extraction error:', execError);
      await supabase.from('uploads').update({
        status: 'failed',
        error_message: execError.message,
      }).eq('id', upload_id);
      return jsonResponse({ error: 'AI extraction failed: ' + execError.message }, 500);
    }
  } catch (error) {
    console.error('Process error:', error);
    return jsonResponse({ error: 'Processing failed' }, 500);
  }
}

// =============================================
// GET RESULT
// =============================================

async function handleGetResult(request, id) {
  try {
    const user = await getAuthUser(request);
    if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

    const supabase = getSupabaseAdmin();

    // Try by result id first, then by upload_id
    let { data: resultData } = await supabase
      .from('results')
      .select('*, uploads!inner(user_id, file_name)')
      .eq('id', id)
      .single();

    if (!resultData) {
      const { data } = await supabase
        .from('results')
        .select('*, uploads!inner(user_id, file_name)')
        .eq('upload_id', id)
        .single();
      resultData = data;
    }

    if (!resultData) return jsonResponse({ error: 'Result not found' }, 404);
    if (resultData.uploads.user_id !== user.id) return jsonResponse({ error: 'Not authorized' }, 403);

    const rows = resultData.edited_json?.rows || resultData.structured_json?.rows || [];

    return jsonResponse({
      result: {
        id: resultData.id,
        upload_id: resultData.upload_id,
        document_type: resultData.document_type,
        rows,
        summary: resultData.summary,
        confidence_score: resultData.confidence_score,
        file_name: resultData.uploads.file_name,
        created_at: resultData.created_at,
      },
    });
  } catch (error) {
    console.error('Get result error:', error);
    return jsonResponse({ error: 'Failed to get result' }, 500);
  }
}

// =============================================
// LIST UPLOADS
// =============================================

async function handleGetUploads(request) {
  try {
    const user = await getAuthUser(request);
    if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

    const supabase = getSupabaseAdmin();
    const { data: uploads, error } = await supabase
      .from('uploads')
      .select('id, file_name, file_type, status, error_message, created_at')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(50);

    if (error) return jsonResponse({ error: 'Failed to fetch uploads' }, 500);

    return jsonResponse({ uploads: uploads || [] });
  } catch (error) {
    console.error('Get uploads error:', error);
    return jsonResponse({ error: 'Failed to get uploads' }, 500);
  }
}

// =============================================
// DELETE FILE
// =============================================

async function handleDeleteFile(request, id) {
  try {
    const user = await getAuthUser(request);
    if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

    const supabase = getSupabaseAdmin();

    const { data: upload } = await supabase
      .from('uploads')
      .select('*')
      .eq('id', id)
      .eq('user_id', user.id)
      .single();

    if (!upload) return jsonResponse({ error: 'File not found' }, 404);

    // Delete from Supabase Storage
    if (upload.file_path) {
      await supabase.storage.from('uploads').remove([upload.file_path]);
    }

    // Delete results
    await supabase.from('results').delete().eq('upload_id', id);

    // Delete upload record
    await supabase.from('uploads').delete().eq('id', id);

    return jsonResponse({ message: 'File deleted' });
  } catch (error) {
    console.error('Delete file error:', error);
    return jsonResponse({ error: 'Delete failed' }, 500);
  }
}

// =============================================
// UPDATE RESULT (edited rows)
// =============================================

async function handleUpdateResult(request, id) {
  try {
    const user = await getAuthUser(request);
    if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

    const body = await request.json();
    const { rows } = body;
    if (!rows) return jsonResponse({ error: 'rows required' }, 400);

    const supabase = getSupabaseAdmin();

    // Find result and verify ownership
    let { data: resultData } = await supabase
      .from('results')
      .select('*, uploads!inner(user_id)')
      .eq('id', id)
      .single();

    if (!resultData) {
      const { data } = await supabase
        .from('results')
        .select('*, uploads!inner(user_id)')
        .eq('upload_id', id)
        .single();
      resultData = data;
    }

    if (!resultData) return jsonResponse({ error: 'Result not found' }, 404);
    if (resultData.uploads.user_id !== user.id) return jsonResponse({ error: 'Not authorized' }, 403);

    await supabase
      .from('results')
      .update({
        edited_json: { rows },
        updated_at: new Date().toISOString(),
      })
      .eq('id', resultData.id);

    return jsonResponse({ message: 'Updated successfully' });
  } catch (error) {
    console.error('Update result error:', error);
    return jsonResponse({ error: 'Update failed' }, 500);
  }
}

// =============================================
// EXPORT EXCEL
// =============================================

async function handleExportExcel(request, id) {
  try {
    const user = await getAuthUser(request);
    if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

    const supabase = getSupabaseAdmin();

    let { data: resultData } = await supabase
      .from('results')
      .select('*, uploads!inner(user_id, file_name)')
      .eq('id', id)
      .single();

    if (!resultData) {
      const { data } = await supabase
        .from('results')
        .select('*, uploads!inner(user_id, file_name)')
        .eq('upload_id', id)
        .single();
      resultData = data;
    }

    if (!resultData) return jsonResponse({ error: 'Result not found' }, 404);
    if (resultData.uploads.user_id !== user.id) return jsonResponse({ error: 'Not authorized' }, 403);

    const ExcelJS = (await import('exceljs')).default;
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Extracted Data');

    worksheet.columns = [
      { header: '#', key: 'row_number', width: 6 },
      { header: 'Date', key: 'date', width: 15 },
      { header: 'Description', key: 'description', width: 40 },
      { header: 'Amount', key: 'amount', width: 15 },
      { header: 'Type', key: 'type', width: 10 },
      { header: 'Category', key: 'category', width: 20 },
      { header: 'GST', key: 'gst', width: 12 },
      { header: 'Reference', key: 'reference', width: 20 },
    ];

    worksheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } };
    worksheet.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1D4ED8' } };

    const rows = resultData.edited_json?.rows || resultData.structured_json?.rows || [];
    rows.forEach((row, index) => {
      worksheet.addRow({
        row_number: index + 1,
        date: row.date || '',
        description: row.description || '',
        amount: row.amount || 0,
        type: row.type || '',
        category: row.category || '',
        gst: row.gst || 0,
        reference: row.reference || '',
      });
    });

    worksheet.addRow({});
    const summaryRow = worksheet.addRow({
      row_number: '',
      date: '',
      description: 'TOTAL',
      amount: rows.reduce((sum, r) => sum + (parseFloat(r.amount) || 0), 0),
      type: '',
      category: '',
      gst: rows.reduce((sum, r) => sum + (parseFloat(r.gst) || 0), 0),
      reference: '',
    });
    summaryRow.font = { bold: true };

    // Log export usage
    await supabase.from('usage_logs').insert({
      user_id: user.id,
      action: 'export',
      credits_used: 0,
      upload_id: resultData.upload_id,
    });

    const excelBuffer = await workbook.xlsx.writeBuffer();

    return new NextResponse(excelBuffer, {
      status: 200,
      headers: {
        ...corsHeaders(),
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': `attachment; filename="docxl_export_${Date.now()}.xlsx"`,
      },
    });
  } catch (error) {
    console.error('Export error:', error);
    return jsonResponse({ error: 'Export failed: ' + error.message }, 500);
  }
}

// =============================================
// ROUTE HANDLERS
// =============================================

export async function GET(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath === '' || routePath === 'health') {
    return jsonResponse({ status: 'ok', service: 'DocXL AI API', backend: 'supabase' });
  }
  if (routePath === 'auth/me') return handleGetMe(request);
  if (routePath === 'uploads') return handleGetUploads(request);
  if (routePath.startsWith('result/')) return handleGetResult(request, pathSegments[1]);
  if (routePath.startsWith('export/excel/')) return handleExportExcel(request, pathSegments[2]);

  return jsonResponse({ error: 'Not found' }, 404);
}

export async function POST(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath === 'auth/register') return handleRegister(request);
  if (routePath === 'auth/login') return handleLogin(request);
  if (routePath === 'upload') return handleUpload(request);
  if (routePath === 'process') return handleProcess(request);

  return jsonResponse({ error: 'Not found' }, 404);
}

export async function PUT(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath.startsWith('result/')) return handleUpdateResult(request, pathSegments[1]);

  return jsonResponse({ error: 'Not found' }, 404);
}

export async function DELETE(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath.startsWith('file/')) return handleDeleteFile(request, pathSegments[1]);

  return jsonResponse({ error: 'Not found' }, 404);
}

export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders() });
}
