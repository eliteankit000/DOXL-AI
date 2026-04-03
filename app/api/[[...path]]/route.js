/*
 * ═══════════════════════════════════════════════════════════════════
 * SUPABASE SQL — Run this ONCE in Supabase SQL Editor before deploy:
 * ═══════════════════════════════════════════════════════════════════
 *
 * CREATE OR REPLACE FUNCTION deduct_credit_if_available(user_uuid UUID)
 * RETURNS BOOLEAN AS $$
 * DECLARE
 *   current_credits INTEGER;
 * BEGIN
 *   SELECT credits INTO current_credits
 *   FROM profiles
 *   WHERE id = user_uuid
 *   FOR UPDATE;
 *   IF current_credits IS NULL OR current_credits <= 0 THEN
 *     RETURN FALSE;
 *   END IF;
 *   UPDATE profiles SET credits = credits - 1 WHERE id = user_uuid;
 *   RETURN TRUE;
 * END;
 * $$ LANGUAGE plpgsql SECURITY DEFINER;
 *
 * ═══════════════════════════════════════════════════════════════════
 */

import { NextResponse } from 'next/server';
import { getSupabaseAdmin, getAuthUser, getUserProfile } from '@/lib/supabase-server';
import { writeFile, unlink, mkdir, access } from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { z } from 'zod';

const execAsync = promisify(exec);
const TEMP_DIR = '/tmp/docxl_processing';

// =============================================
// ZOD VALIDATION SCHEMAS
// =============================================

const registerSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  name: z.string().optional(),
});

const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(1, 'Password required'),
});

const processSchema = z.object({
  upload_id: z.string().uuid('Invalid upload ID'),
  user_requirements: z.string().max(500).optional(),
});

const updateResultSchema = z.object({
  rows: z.array(z.object({
    date: z.string().optional(),
    description: z.string().optional(),
    amount: z.number().optional(),
    type: z.string().optional(),
    category: z.string().optional(),
    gst: z.number().optional(),
    reference: z.string().optional(),
  })),
});

function validate(schema, data) {
  const result = schema.safeParse(data);
  if (!result.success) return { error: result.error.errors[0].message, data: null };
  return { error: null, data: result.data };
}

// =============================================
// RATE LIMITING (module-level, no packages)
// =============================================

const rateLimitMap = new Map();

function checkRateLimit(userId, maxRequests = 5, windowMs = 60000) {
  const now = Date.now();
  const entry = rateLimitMap.get(userId) || { count: 0, windowStart: now };
  if (now - entry.windowStart > windowMs) {
    entry.count = 0;
    entry.windowStart = now;
  }
  if (entry.count >= maxRequests) return false;
  entry.count++;
  rateLimitMap.set(userId, entry);
  return true;
}

// =============================================
// HELPERS
// =============================================

async function ensureTempDir() {
  try { await access(TEMP_DIR); } catch { await mkdir(TEMP_DIR, { recursive: true }); }
}

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
// AUTH HANDLERS
// =============================================

async function handleRegister(request) {
  try {
    const body = await request.json();
    const validationResult = validate(registerSchema, body);
    if (validationResult.error) {
      return jsonResponse({ error: validationResult.error }, 400);
    }

    const { email, password, name } = validationResult.data;

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
      console.error('[handleRegister] error:', error);
      return jsonResponse({ error: 'Registration failed. Please try again.' }, 400);
    }

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
    console.error('[handleRegister] error:', error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
  }
}

async function handleLogin(request) {
  try {
    const body = await request.json();
    const validationResult = validate(loginSchema, body);
    if (validationResult.error) {
      return jsonResponse({ error: validationResult.error }, 400);
    }

    const { email, password } = validationResult.data;

    const supabase = getSupabaseAdmin();
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
    console.error('[handleLogin] error:', error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
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

    const { data: storageData, error: storageError } = await supabase.storage
      .from('uploads')
      .upload(storagePath, buffer, {
        contentType: file.type || 'application/octet-stream',
        upsert: false,
      });

    if (storageError) {
      console.error('[handleUpload] storage error:', storageError);
      return jsonResponse({ error: 'Upload failed. Please try again.' }, 500);
    }

    let fileType = 'other';
    if (ext === '.pdf') fileType = 'invoice';
    else fileType = 'image';

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
      console.error('[handleUpload] db error:', dbError);
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
    console.error('[handleUpload] error:', error);
    return jsonResponse({ error: 'Upload failed. Please try again.' }, 500);
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
    const validationResult = validate(processSchema, body);
    if (validationResult.error) {
      return jsonResponse({ error: validationResult.error }, 400);
    }

    const { upload_id, user_requirements = '' } = validationResult.data;

    // Rate limit check
    if (!checkRateLimit(user.id)) {
      return new NextResponse(JSON.stringify({ error: 'Too many requests. Please wait a minute.' }), {
        status: 429,
        headers: { ...corsHeaders(), 'Retry-After': '60', 'Content-Type': 'application/json' },
      });
    }

    const supabase = getSupabaseAdmin();

    // Atomic credit deduction via Supabase RPC
    const { data: canProcess, error: rpcError } = await supabase.rpc('deduct_credit_if_available', { user_uuid: user.id });
    if (rpcError || !canProcess) {
      return jsonResponse({ error: 'No credits remaining. Please upgrade to Pro.' }, 403);
    }

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

    let tempFilePath = null;
    try {
      // Download file from Supabase Storage to temp
      const { data: fileBlob, error: dlErr } = await supabase.storage
        .from('uploads')
        .download(upload.file_path);

      if (dlErr || !fileBlob) {
        throw new Error('Failed to download file from storage');
      }

      await ensureTempDir();

      // Stale file cleanup
      try {
        const { readdir, stat } = await import('fs/promises');
        const tmpFiles = await readdir(TEMP_DIR);
        const now = Date.now();
        for (const f of tmpFiles) {
          const fp = path.join(TEMP_DIR, f);
          const s = await stat(fp);
          if (now - s.mtimeMs > 3600000) await unlink(fp).catch(() => {});
        }
      } catch (e) {}

      tempFilePath = path.join(TEMP_DIR, `${upload_id}${path.extname(upload.file_name)}`);
      const fileBuffer = Buffer.from(await fileBlob.arrayBuffer());
      await writeFile(tempFilePath, fileBuffer);

      // Call Python extraction script with user_requirements
      const escapedReqs = (user_requirements || '').replace(/"/g, '\\"').replace(/`/g, '\\`');
      const { stdout, stderr } = await execAsync(
        `cd /app && EMERGENT_LLM_KEY="${process.env.EMERGENT_LLM_KEY}" /root/.venv/bin/python3 scripts/extract.py "${tempFilePath}" "${escapedReqs}"`,
        { timeout: 120000, maxBuffer: 10 * 1024 * 1024 }
      );

      if (stderr) console.error('[handleProcess] extract stderr:', stderr);

      let result;
      try {
        result = JSON.parse(stdout.trim());
      } catch (parseError) {
        throw new Error('Failed to parse extraction result');
      }

      if (result.error) {
        await supabase.from('uploads').update({ status: 'failed', error_message: result.error }).eq('id', upload_id);
        // Only pass error through if it does NOT contain a file path
        const safeError = /[/\\]/.test(result.error)
          ? 'Could not extract data from this document. Please try a clearer image or PDF.'
          : result.error;
        return jsonResponse({ error: safeError }, 422);
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
          confidence_score: result.confidence || 0.85,
        })
        .select()
        .single();

      if (resultErr) {
        console.error('[handleProcess] result insert error:', resultErr);
        throw new Error('Failed to save extraction result');
      }

      // Update upload status
      await supabase.from('uploads').update({ status: 'completed' }).eq('id', upload_id);

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
      console.error('[handleProcess] extraction error:', execError);
      await supabase.from('uploads').update({ status: 'failed', error_message: 'Processing failed' }).eq('id', upload_id);
      return jsonResponse({ error: 'Document processing failed. Please try again or use a clearer image.' }, 500);
    } finally {
      if (tempFilePath) {
        try { await unlink(tempFilePath); } catch (e) {}
      }
    }
  } catch (error) {
    console.error('[handleProcess] error:', error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
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
    console.error('[handleGetResult] error:', error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
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
    console.error('[handleGetUploads] error:', error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
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

    if (upload.file_path) {
      await supabase.storage.from('uploads').remove([upload.file_path]);
    }

    await supabase.from('results').delete().eq('upload_id', id);
    await supabase.from('uploads').delete().eq('id', id);

    return jsonResponse({ message: 'File deleted' });
  } catch (error) {
    console.error('[handleDeleteFile] error:', error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
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
    const validationResult = validate(updateResultSchema, body);
    if (validationResult.error) {
      return jsonResponse({ error: validationResult.error }, 400);
    }

    const { rows } = validationResult.data;
    const supabase = getSupabaseAdmin();

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
    console.error('[handleUpdateResult] error:', error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
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
    console.error('[handleExportExcel] error:', error);
    return jsonResponse({ error: 'Export failed. Please try again.' }, 500);
  }
}

// =============================================
// RAZORPAY PAYMENT HANDLERS
// =============================================

async function handleCreateOrder(request) {
  const user = await getAuthUser(request);
  if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);
  try {
    const Razorpay = (await import('razorpay')).default;
    const rzp = new Razorpay({
      key_id: process.env.RAZORPAY_KEY_ID,
      key_secret: process.env.RAZORPAY_KEY_SECRET,
    });
    const order = await rzp.orders.create({
      amount: 69900,
      currency: 'INR',
      receipt: `docxl_${Date.now().toString().slice(-8)}`,
    });
    return jsonResponse({
      orderId: order.id,
      amount: order.amount,
      currency: order.currency,
      keyId: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
    });
  } catch (error) {
    console.error('[handleCreateOrder] error:', error);
    return jsonResponse({ error: 'Could not initiate payment. Please try again.' }, 500);
  }
}

async function handlePaymentVerify(request) {
  try {
    const body = await request.json();
    const { razorpay_order_id, razorpay_payment_id, razorpay_signature, user_id } = body;
    if (!razorpay_order_id || !razorpay_payment_id || !razorpay_signature || !user_id) {
      return jsonResponse({ error: 'Missing payment fields' }, 400);
    }
    const crypto = await import('crypto');
    const expectedSig = crypto.createHmac('sha256', process.env.RAZORPAY_KEY_SECRET)
      .update(`${razorpay_order_id}|${razorpay_payment_id}`).digest('hex');
    if (expectedSig !== razorpay_signature) return jsonResponse({ error: 'Invalid payment signature' }, 400);
    const supabase = getSupabaseAdmin();
    await supabase.from('profiles').update({ plan: 'pro', credits: 300 }).eq('id', user_id);
    await supabase.from('usage_logs').insert({ user_id, action: 'upgrade', credits_used: 0, upload_id: null });
    return jsonResponse({ success: true });
  } catch (error) {
    console.error('[handlePaymentVerify] error:', error);
    return jsonResponse({ error: 'Payment verification failed.' }, 500);
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
  if (routePath === 'payment/create-order') return handleCreateOrder(request);
  if (routePath === 'payment/verify') return handlePaymentVerify(request);

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
