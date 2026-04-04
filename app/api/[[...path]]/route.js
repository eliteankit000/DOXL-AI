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
import { execFile } from 'child_process';
import { promisify } from 'util';
import { z } from 'zod';

const execFileAsync = promisify(execFile);
const TEMP_DIR = '/tmp/docxl_processing';

// Export config for Vercel serverless functions
export const maxDuration = 300; // 5 minutes for AI processing
export const runtime = 'nodejs';

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
    amount: z.union([z.number(), z.string()]).optional(),
    type: z.string().optional(),
    category: z.string().optional(),
    gst: z.union([z.number(), z.string()]).optional(),
    reference: z.string().optional(),
    confidence: z.number().optional(),
    row_number: z.number().optional(),
  }).passthrough()),
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

    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
      return jsonResponse({ error: 'File too large. Maximum 100MB allowed.' }, 400);
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

    // Atomic credit deduction via Supabase RPC (with fallback)
    let creditDeducted = false;
    try {
      const { data: canProcess, error: rpcError } = await supabase.rpc('deduct_credit_if_available', { user_uuid: user.id });
      if (!rpcError && canProcess) {
        creditDeducted = true;
      }
    } catch (e) {
      console.error('[handleProcess] RPC fallback:', e.message);
    }

    // Fallback: manual credit check and deduction
    if (!creditDeducted) {
      const profile = await getUserProfile(user.id);
      if (!profile || profile.credits <= 0) {
        return jsonResponse({ error: 'No credits remaining. Please upgrade to Pro.' }, 403);
      }
      const { error: deductErr } = await supabase
        .from('profiles')
        .update({ credits: Math.max(0, profile.credits - 1) })
        .eq('id', user.id);
      if (deductErr) {
        console.error('[handleProcess] credit deduction error:', deductErr);
        return jsonResponse({ error: 'Credit deduction failed. Please try again.' }, 500);
      }
      creditDeducted = true;
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

      // Call Python extraction script with user_requirements (using execFile to prevent shell injection)
      const { stdout, stderr } = await execFileAsync(
        '/root/.venv/bin/python3',
        ['scripts/extract.py', tempFilePath, user_requirements || ''],
        {
          cwd: '/app',
          timeout: 180000,
          maxBuffer: 10 * 1024 * 1024,
          env: { ...process.env, OPENAI_API_KEY: process.env.OPENAI_API_KEY }
        }
      );

      if (stderr && stderr.includes('Error') && !stdout.trim()) {
        console.error('[handleProcess] extract stderr:', stderr);
        throw new Error('Extraction script error: ' + stderr.substring(0, 200));
      }
      if (stderr) console.error('[handleProcess] extract stderr:', stderr);

      if (!stdout || !stdout.trim()) {
        throw new Error('No output from extraction script — document may be empty or corrupted');
      }

      let result;
      const trimmedOutput = stdout.trim();
      const jsonStart = trimmedOutput.lastIndexOf('\n{');
      const cleanOutput = jsonStart >= 0 ? trimmedOutput.substring(jsonStart + 1) : trimmedOutput;
      try {
        result = JSON.parse(cleanOutput);
      } catch (parseError) {
        console.error('[handleProcess] parse error, raw output:', trimmedOutput.substring(0, 500));
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
        confidence: row.confidence !== undefined ? parseFloat(row.confidence) : 0.85,
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
      
      // Refund credit on timeout or processing failure
      if (creditDeducted) {
        const profile = await getUserProfile(user.id);
        if (profile) {
          await supabase.from('profiles').update({ credits: profile.credits + 1 }).eq('id', user.id);
          await supabase.from('usage_logs').insert({
            user_id: user.id,
            action: 'timeout_refund',
            credits_used: -1,
            upload_id,
          });
        }
      }
      
      // Check if timeout error
      if (execError.killed || execError.signal === 'SIGTERM') {
        return jsonResponse({ error: 'Processing timed out. Please try with a smaller or clearer document. Your credit has been refunded.' }, 408);
      }
      
      return jsonResponse({ error: 'Document processing failed. Please try again or use a clearer image. Your credit has been refunded.' }, 500);
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
      { header: 'Confidence', key: 'confidence', width: 12 },
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
        confidence: row.confidence !== undefined ? row.confidence : '',
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
    // SECURITY FIX: Extract user from JWT, don't trust user_id from frontend
    const user = await getAuthUser(request);
    if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);
    
    const body = await request.json();
    const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = body;
    if (!razorpay_order_id || !razorpay_payment_id || !razorpay_signature) {
      return jsonResponse({ error: 'Missing payment fields' }, 400);
    }
    const crypto = await import('crypto');
    const expectedSig = crypto.createHmac('sha256', process.env.RAZORPAY_KEY_SECRET)
      .update(`${razorpay_order_id}|${razorpay_payment_id}`).digest('hex');
    if (expectedSig !== razorpay_signature) return jsonResponse({ error: 'Invalid payment signature' }, 400);
    const supabase = getSupabaseAdmin();
    await supabase.from('profiles').update({ plan: 'pro', credits: 300 }).eq('id', user.id);
    await supabase.from('usage_logs').insert({ user_id: user.id, action: 'upgrade', credits_used: 0, upload_id: null });
    return jsonResponse({ success: true });
  } catch (error) {
    console.error('[handlePaymentVerify] error:', error);
    return jsonResponse({ error: 'Payment verification failed.' }, 500);
  }
}

// =============================================
// PADDLE PAYMENT HANDLERS (GLOBAL)
// =============================================

async function handlePaddleCheckout(request) {
  const user = await getAuthUser(request);
  if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);
  
  try {
    // Check if Paddle is configured
    if (!process.env.PADDLE_API_KEY || !process.env.PADDLE_PRICE_ID) {
      return jsonResponse({ error: 'Paddle payment not configured. Please use Razorpay (India) or contact support.' }, 503);
    }

    // Return Paddle checkout data
    return jsonResponse({
      priceId: process.env.PADDLE_PRICE_ID,
      customData: {
        user_id: user.id,
        email: user.email,
      },
    });
  } catch (error) {
    console.error('[handlePaddleCheckout] error:', error);
    return jsonResponse({ error: 'Could not initiate payment. Please try again.' }, 500);
  }
}

async function handlePaddleWebhook(request) {
  try {
    // Verify Paddle webhook signature
    const signature = request.headers.get('paddle-signature');
    if (!signature || !process.env.PADDLE_WEBHOOK_SECRET) {
      return jsonResponse({ error: 'Invalid webhook' }, 401);
    }

    const body = await request.text();
    const crypto = await import('crypto');
    
    // Parse signature header: ts=timestamp;h1=signature
    const sigParts = signature.split(';').reduce((acc, part) => {
      const [key, value] = part.split('=');
      acc[key] = value;
      return acc;
    }, {});

    const expectedSig = crypto.createHmac('sha256', process.env.PADDLE_WEBHOOK_SECRET)
      .update(`${sigParts.ts}:${body}`)
      .digest('hex');

    if (expectedSig !== sigParts.h1) {
      console.error('[handlePaddleWebhook] Invalid signature');
      return jsonResponse({ error: 'Invalid signature' }, 401);
    }

    const event = JSON.parse(body);

    // Handle transaction.completed event
    if (event.event_type === 'transaction.completed') {
      const userId = event.data?.custom_data?.user_id;
      if (!userId) {
        console.error('[handlePaddleWebhook] Missing user_id in custom_data');
        return jsonResponse({ error: 'Missing user_id' }, 400);
      }

      const supabase = getSupabaseAdmin();
      await supabase.from('profiles').update({ plan: 'pro', credits: 300 }).eq('id', userId);
      await supabase.from('usage_logs').insert({
        user_id: userId,
        action: 'upgrade',
        credits_used: 0,
        upload_id: null,
      });

      console.log(`[handlePaddleWebhook] Upgraded user ${userId} to Pro via Paddle`);
    }

    return jsonResponse({ received: true });
  } catch (error) {
    console.error('[handlePaddleWebhook] error:', error);
    return jsonResponse({ error: 'Webhook processing failed' }, 500);
  }
}

// =============================================
// CRON AUTOMATION HANDLERS
// =============================================

async function handleCleanupCron(request) {
  const startTime = Date.now();
  console.log('[CRON] cleanup-files: Execution started at', new Date().toISOString());
  
  try {
    // Verify CRON_SECRET
    const authHeader = request.headers.get('authorization');
    const cronSecret = authHeader?.replace('Bearer ', '');
    
    if (!cronSecret || cronSecret !== process.env.CRON_SECRET) {
      console.log('[CRON] cleanup-files: Unauthorized request rejected');
      return jsonResponse({ error: 'Unauthorized' }, 401);
    }

    const supabase = getSupabaseAdmin();
    const cutoffDate = new Date(Date.now() - 48 * 60 * 60 * 1000); // 48 hours ago
    console.log('[CRON] cleanup-files: Cutoff date =', cutoffDate.toISOString());

    // Get old uploads
    const { data: oldUploads, error: fetchError } = await supabase
      .from('uploads')
      .select('id, file_path')
      .lt('created_at', cutoffDate.toISOString())
      .limit(100);

    if (fetchError) {
      console.error('[CRON] cleanup-files: Error fetching old uploads:', fetchError);
      throw fetchError;
    }

    let deletedCount = 0;
    if (oldUploads && oldUploads.length > 0) {
      console.log('[CRON] cleanup-files: Found', oldUploads.length, 'files to delete');
      
      // Delete from storage
      const filePaths = oldUploads.map(u => u.file_path).filter(Boolean);
      if (filePaths.length > 0) {
        const { error: storageError } = await supabase.storage.from('uploads').remove(filePaths);
        if (storageError) {
          console.error('[CRON] cleanup-files: Storage delete error:', storageError);
        }
      }

      // Delete from database
      const uploadIds = oldUploads.map(u => u.id);
      await supabase.from('results').delete().in('upload_id', uploadIds);
      await supabase.from('uploads').delete().in('id', uploadIds);
      
      deletedCount = oldUploads.length;
    }

    const duration = Date.now() - startTime;
    console.log(`[CRON] cleanup-files: Completed. Deleted ${deletedCount} files in ${duration}ms`);

    return jsonResponse({
      success: true,
      deleted: deletedCount,
      cutoff: cutoffDate.toISOString(),
      duration_ms: duration,
    });
  } catch (error) {
    console.error('[CRON] cleanup-files: Error:', error);
    return jsonResponse({ error: 'Cleanup failed' }, 500);
  }
}

async function handleResetCreditsCron(request) {
  const startTime = Date.now();
  console.log('[CRON] reset-credits: Execution started at', new Date().toISOString());
  
  try {
    // Verify CRON_SECRET
    const authHeader = request.headers.get('authorization');
    const cronSecret = authHeader?.replace('Bearer ', '');
    
    if (!cronSecret || cronSecret !== process.env.CRON_SECRET) {
      console.log('[CRON] reset-credits: Unauthorized request rejected');
      return jsonResponse({ error: 'Unauthorized' }, 401);
    }

    const supabase = getSupabaseAdmin();

    // Reset all Pro users to 300 credits
    const { data: updated, error: updateError } = await supabase
      .from('profiles')
      .update({ credits: 300 })
      .eq('plan', 'pro')
      .select('id');

    if (updateError) {
      console.error('[CRON] reset-credits: Update error:', updateError);
      throw updateError;
    }

    const resetCount = updated?.length || 0;
    const duration = Date.now() - startTime;
    console.log(`[CRON] reset-credits: Completed. Reset ${resetCount} Pro users in ${duration}ms`);

    return jsonResponse({
      success: true,
      reset_count: resetCount,
      duration_ms: duration,
    });
  } catch (error) {
    console.error('[CRON] reset-credits: Error:', error);
    return jsonResponse({ error: 'Credit reset failed' }, 500);
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
  if (routePath === 'payment/paddle/checkout') return handlePaddleCheckout(request);
  if (routePath === 'webhooks/paddle') return handlePaddleWebhook(request);
  if (routePath === 'cron/cleanup-files' || routePath === 'cron/cleanup') return handleCleanupCron(request);
  if (routePath === 'cron/reset-credits') return handleResetCreditsCron(request);

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
