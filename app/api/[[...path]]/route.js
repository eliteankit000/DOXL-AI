/*
 * DocXL AI — API Route Handler v3.0
 * Supabase-backed, production-hardened
 *
 * ═══════════════════════════════════════════════════════════════════
 * SUPABASE SQL — Run ONCE in Supabase SQL Editor:
 * ═══════════════════════════════════════════════════════════════════
 *
 * -- 1. Drop and rewrite the credit deduction RPC
 * DROP FUNCTION IF EXISTS deduct_credit_if_available(UUID);
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
 * -- 2. Rate limits table
 * CREATE TABLE IF NOT EXISTS rate_limits (
 *   id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 *   user_id uuid REFERENCES auth.users ON DELETE CASCADE,
 *   action text NOT NULL,
 *   window_start timestamptz NOT NULL DEFAULT now(),
 *   request_count integer NOT NULL DEFAULT 1,
 *   UNIQUE(user_id, action)
 * );
 * ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;
 * CREATE POLICY "service role full access" ON rate_limits
 *   USING (auth.role() = 'service_role');
 *
 * -- 3. Terms acceptance columns
 * ALTER TABLE profiles
 *   ADD COLUMN IF NOT EXISTS terms_accepted_at timestamptz,
 *   ADD COLUMN IF NOT EXISTS terms_accepted_ip text;
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

let Sentry = null;
try {
  Sentry = require('@sentry/nextjs');
} catch (e) {
  // Sentry not configured yet — silently skip
}

const execFileAsync = promisify(execFile);

// =============================================
// DYNAMIC PYTHON PATH DETECTION
// =============================================
let _cachedPythonPath = null;
async function getPythonPath() {
  if (_cachedPythonPath) return _cachedPythonPath;
  const candidates = [
    '/root/.venv/bin/python3',
    '/usr/local/bin/python3',
    '/usr/bin/python3',
    'python3',
    'python',
  ];
  for (const candidate of candidates) {
    try {
      await execFileAsync(candidate, ['--version'], { timeout: 5000 });
      _cachedPythonPath = candidate;
      console.log(`[getPythonPath] using: ${candidate}`);
      return candidate;
    } catch (_) { continue; }
  }
  throw new Error('Python3 not found on this system.');
}

// =============================================
// AUTO-INSTALL PYTHON DEPENDENCIES
// =============================================
let _depsInstalled = false;
async function ensurePythonDeps() {
  if (_depsInstalled) return;
  const pythonExec = await getPythonPath();
  const deps = ['openai', 'pdfplumber', 'python-dateutil', 'Pillow'];
  try {
    await execFileAsync(pythonExec, ['-m', 'pip', 'install', '--quiet', ...deps], {
      timeout: 120000,
      env: { PATH: process.env.PATH },
    });
    _depsInstalled = true;
    console.log('[ensurePythonDeps] deps ready');
  } catch (e) {
    console.error('[ensurePythonDeps] install error (non-fatal):', e.message?.substring(0, 200));
    _depsInstalled = true; // Don't retry on every request
  }
}

const TEMP_DIR = '/tmp/docxl_processing';

export const maxDuration = 300;
export const runtime = 'nodejs';

// =============================================
// ZOD VALIDATION SCHEMAS
// =============================================

const registerSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  name: z.string().optional(),
  terms_accepted: z.boolean().optional(),
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

const contactSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  message: z.string().min(1, 'Message is required'),
});

const forgotPasswordSchema = z.object({
  email: z.string().email('Invalid email'),
});

const adminCreditsSchema = z.object({
  userId: z.string().uuid('Invalid user ID'),
  newCredits: z.number().int().min(0),
});

function validate(schema, data) {
  const result = schema.safeParse(data);
  if (!result.success) return { error: result.error.errors[0].message, data: null };
  return { error: null, data: result.data };
}

// =============================================
// ADMIN EMAIL CONSTANT
// =============================================
const ADMIN_EMAIL = 'aniketar111@gmail.com';

// =============================================
// SUPABASE-BACKED RATE LIMITING (persistent)
// =============================================

async function checkRateLimit(userId, maxRequests = 5, windowMs = 60000) {
  try {
    const supabase = getSupabaseAdmin();
    const windowStart = new Date(Date.now() - windowMs).toISOString();

    const { data: existing } = await supabase
      .from('rate_limits')
      .select('id, request_count, window_start')
      .eq('user_id', userId)
      .eq('action', 'process')
      .gte('window_start', windowStart)
      .single();

    if (!existing) {
      await supabase
        .from('rate_limits')
        .upsert({
          user_id: userId,
          action: 'process',
          window_start: new Date().toISOString(),
          request_count: 1,
        }, { onConflict: 'user_id,action' });
      return true;
    }

    if (existing.request_count >= maxRequests) {
      return false;
    }

    await supabase
      .from('rate_limits')
      .update({ request_count: existing.request_count + 1 })
      .eq('id', existing.id);

    return true;
  } catch (e) {
    console.error('[checkRateLimit] error:', e.message);
    return true;
  }
}

// =============================================
// HELPERS
// =============================================

async function ensureTempDir() {
  try { await access(TEMP_DIR); } catch { await mkdir(TEMP_DIR, { recursive: true }); }
}

function corsHeaders() {
  const origin = process.env.NODE_ENV === 'development'
    ? 'http://localhost:3000'
    : (process.env.CORS_ORIGINS || '*');
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}

function jsonResponse(body, status = 200) {
  return NextResponse.json(body, { status, headers: corsHeaders() });
}

function captureException(error) {
  if (Sentry && typeof Sentry.captureException === 'function') {
    Sentry.captureException(error);
  }
}

// =============================================
// ADMIN JWT VERIFICATION HELPER
// =============================================

async function verifyAdmin(request) {
  const user = await getAuthUser(request);
  if (!user) return { user: null, error: jsonResponse({ error: 'Unauthorized' }, 401) };
  if (user.email !== ADMIN_EMAIL) return { user: null, error: jsonResponse({ error: 'Forbidden' }, 403) };
  return { user, error: null };
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

    const { email, password, name, terms_accepted } = validationResult.data;

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

    if (terms_accepted && data.user) {
      const clientIp = request.headers.get('x-forwarded-for')
        || request.headers.get('x-real-ip')
        || 'unknown';
      await supabase
        .from('profiles')
        .update({
          terms_accepted_at: new Date().toISOString(),
          terms_accepted_ip: clientIp.split(',')[0].trim(),
        })
        .eq('id', data.user.id);
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
    captureException(error);
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
    captureException(error);
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
// FORGOT PASSWORD (Brevo API)
// =============================================

async function handleForgotPassword(request) {
  try {
    const body = await request.json();
    const validationResult = validate(forgotPasswordSchema, body);
    if (validationResult.error) {
      return jsonResponse({ error: validationResult.error }, 400);
    }

    const { email } = validationResult.data;
    const supabase = getSupabaseAdmin();

    const successResponse = jsonResponse({
      success: true,
      message: 'If an account exists for this email, a reset link has been sent. Check your inbox and spam folder.',
    });

    try {
      const { data: userData } = await supabase.auth.admin.listUsers();
      const targetUser = userData?.users?.find(u => u.email?.toLowerCase() === email.toLowerCase());
      if (!targetUser) return successResponse;

      const { data: linkData, error: linkError } = await supabase.auth.admin.generateLink({
        type: 'recovery',
        email: email.toLowerCase(),
      });

      if (linkError || !linkData) {
        console.error('[handleForgotPassword] link error:', linkError);
        return successResponse;
      }

      const resetLink = linkData.properties?.action_link || linkData.properties?.hashed_token;

      const brevoKey = process.env.BREVO_API_KEY;
      if (!brevoKey) {
        console.error('[handleForgotPassword] BREVO_API_KEY not configured');
        return successResponse;
      }

      const brevoResponse = await fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: {
          'api-key': brevoKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender: { name: 'DocXL AI', email: 'hello@docxlai.com' },
          to: [{ email: email.toLowerCase() }],
          subject: 'Reset your DocXL AI password',
          htmlContent: `<p>Click the link below to reset your password. This link expires in 1 hour.</p><p><a href="${resetLink}">Reset Password</a></p><p>If you did not request this, ignore this email.</p>`,
        }),
      });

      if (!brevoResponse.ok) {
        const errText = await brevoResponse.text();
        console.error('[handleForgotPassword] Brevo error:', errText);
      }
    } catch (innerErr) {
      console.error('[handleForgotPassword] inner error:', innerErr);
    }

    return successResponse;
  } catch (error) {
    console.error('[handleForgotPassword] error:', error);
    captureException(error);
    return jsonResponse({
      success: true,
      message: 'If an account exists for this email, a reset link has been sent. Check your inbox and spam folder.',
    });
  }
}

// =============================================
// CONTACT FORM (Brevo API)
// =============================================

async function handleContact(request) {
  try {
    const body = await request.json();
    const validationResult = validate(contactSchema, body);
    if (validationResult.error) {
      return jsonResponse({ error: validationResult.error }, 400);
    }

    const { name, email, message } = validationResult.data;

    const brevoKey = process.env.BREVO_API_KEY;
    if (!brevoKey) {
      console.error('[handleContact] BREVO_API_KEY not configured');
      return jsonResponse({ error: 'Failed to send message. Please email us directly at hello@docxlai.com' }, 500);
    }

    const brevoResponse = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: {
        'api-key': brevoKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sender: { name: 'DocXL AI Contact Form', email: 'hello@docxlai.com' },
        to: [{ email: 'hello@docxlai.com' }],
        replyTo: { email, name },
        subject: 'New Contact Form Submission — DocXL AI',
        htmlContent: `<p><strong>Name:</strong> ${name}</p><p><strong>Email:</strong> ${email}</p><p><strong>Message:</strong></p><p>${message}</p>`,
      }),
    });

    if (!brevoResponse.ok) {
      const errText = await brevoResponse.text();
      console.error('[handleContact] Brevo error:', errText);
      return jsonResponse({ error: 'Failed to send message' }, 500);
    }

    return jsonResponse({ success: true });
  } catch (error) {
    console.error('[handleContact] error:', error);
    captureException(error);
    return jsonResponse({ error: 'Failed to send message' }, 500);
  }
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

    const maxSize = 100 * 1024 * 1024;
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
    captureException(error);
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

    const allowed = await checkRateLimit(user.id);
    if (!allowed) {
      return new NextResponse(JSON.stringify({ error: 'Too many requests. Please wait a minute.' }), {
        status: 429,
        headers: { ...corsHeaders(), 'Retry-After': '60', 'Content-Type': 'application/json' },
      });
    }

    const supabase = getSupabaseAdmin();

    const { data: canProcess, error: rpcError } = await supabase.rpc('deduct_credit_if_available', { user_uuid: user.id });
    if (rpcError || !canProcess) {
      if (rpcError) console.error('[handleProcess] RPC error:', rpcError);
      return jsonResponse({ error: 'No credits remaining. Please upgrade to Pro.' }, 403);
    }

    const { data: upload, error: fetchErr } = await supabase
      .from('uploads')
      .select('*')
      .eq('id', upload_id)
      .eq('user_id', user.id)
      .single();

    if (fetchErr || !upload) return jsonResponse({ error: 'Upload not found' }, 404);
    if (upload.status === 'processing') return jsonResponse({ error: 'Already processing' }, 400);

    await supabase.from('uploads').update({ status: 'processing' }).eq('id', upload_id);

    let tempFilePath = null;
    try {
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

      // =============================================
      // FIX: Dynamic Python path + safe stderr check
      // =============================================
      const pythonExec = await getPythonPath();
      const projectRoot = process.cwd();
      const scriptPath = path.join(projectRoot, 'scripts', 'extract.py');

      // ── CHANGE 2: ensure Python deps are installed ──
      await ensurePythonDeps();

      console.log(`[handleProcess] python:${pythonExec} | cwd:${projectRoot} | file:${tempFilePath}`);

      const rawResult = await execFileAsync(
        pythonExec,
        [scriptPath, tempFilePath, user_requirements || ''],
        {
          cwd: projectRoot,
          timeout: 180000,
          maxBuffer: 10 * 1024 * 1024,
          env: {
            OPENAI_API_KEY: process.env.OPENAI_API_KEY,
            PATH: process.env.PATH,
          },
        }
      ).catch(err => {
        const out = (err.stdout || '').trim();
        const errStr = err.stderr || err.message || '';
        console.error('[handleProcess] execFile error:', errStr.substring(0, 400));
        // If the script still produced valid JSON on stdout despite non-zero exit, use it
        if (out) return { stdout: out, stderr: errStr };
        throw new Error('Script failed: ' + errStr.substring(0, 300));
      });

      const { stdout, stderr } = rawResult;

      // Only treat stderr as fatal when it contains real Python-level errors
      // AND there is no usable stdout. This prevents false failures caused by
      // informational messages from the OpenAI SDK that contain the word "Error".
      // ── CHANGE 3a: added 'No module named' ──
      const FATAL_STDERR_PATTERNS = [
        'Traceback (most recent call last)',
        'ModuleNotFoundError',
        'ImportError',
        'SyntaxError',
        'FileNotFoundError',
        'PermissionError',
        'OPENAI_API_KEY not configured',
        'No module named',
      ];
      const isFatalStderr = stderr &&
        !stdout.trim() &&
        FATAL_STDERR_PATTERNS.some(p => stderr.includes(p));

      if (isFatalStderr) {
        console.error('[handleProcess] fatal stderr:', stderr.substring(0, 400));
        // ── CHANGE 3b: reset dep cache so next request re-installs ──
        if (stderr.includes('No module named')) {
          _depsInstalled = false;
          _cachedPythonPath = null;
        }
        throw new Error('Extraction script error: ' + stderr.substring(0, 200));
      }
      if (stderr) {
        // Non-fatal — OpenAI SDK and pdfplumber write info/warnings to stderr
        console.error('[handleProcess] stderr (non-fatal):', stderr.substring(0, 300));
      }

      if (!stdout || !stdout.trim()) {
        throw new Error('No output from extraction script — document may be empty or corrupted');
      }
      // =============================================

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

      const responsePayload = {
        document_type: result.document_type || 'other',
        rows: normalizedRows,
        summary,
        confidence_score: result.confidence || 0.85,
      };

      if (result.page_warning) {
        responsePayload.warning = result.page_warning;
      }

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

      await supabase.from('uploads').update({ status: 'completed' }).eq('id', upload_id);

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
          ...responsePayload,
        },
      });
    } catch (execError) {
      console.error('[handleProcess] extraction error:', execError);
      captureException(execError);
      await supabase.from('uploads').update({ status: 'failed', error_message: 'Processing failed' }).eq('id', upload_id);

      // Refund credit on timeout or processing failure
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
    captureException(error);
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
    captureException(error);
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
    captureException(error);
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
    captureException(error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
  }
}

// =============================================
// UPDATE RESULT
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
    captureException(error);
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
    captureException(error);
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
    captureException(error);
    return jsonResponse({ error: 'Could not initiate payment. Please try again.' }, 500);
  }
}

async function handlePaymentVerify(request) {
  try {
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
    captureException(error);
    return jsonResponse({ error: 'Payment verification failed.' }, 500);
  }
}

// =============================================
// PADDLE PAYMENT HANDLERS
// =============================================

async function handlePaddleCheckout(request) {
  const user = await getAuthUser(request);
  if (!user) return jsonResponse({ error: 'Unauthorized' }, 401);

  try {
    if (!process.env.PADDLE_API_KEY || !process.env.PADDLE_PRICE_ID) {
      return jsonResponse({ error: 'Paddle payment not configured. Please use Razorpay (India) or contact support.' }, 503);
    }

    return jsonResponse({
      priceId: process.env.PADDLE_PRICE_ID,
      customData: {
        user_id: user.id,
        email: user.email,
      },
    });
  } catch (error) {
    console.error('[handlePaddleCheckout] error:', error);
    captureException(error);
    return jsonResponse({ error: 'Could not initiate payment. Please try again.' }, 500);
  }
}

async function handlePaddleWebhook(request) {
  try {
    const signature = request.headers.get('paddle-signature');
    if (!signature || !process.env.PADDLE_WEBHOOK_SECRET) {
      return jsonResponse({ error: 'Invalid webhook' }, 401);
    }

    const body = await request.text();
    const crypto = await import('crypto');

    const sigParts = signature.split(';').reduce((acc, part) => {
      const [key, value] = part.split('=');
      acc[key] = value;
      return acc;
    }, {});

    const expectedSig = crypto.createHmac('sha256', process.env.PADDLE_WEBHOOK_SECRET)
      .update(`${sigParts.ts}:${body}`)
      .digest('hex');

    if (expectedSig !== sigParts.h1) {
      return jsonResponse({ error: 'Invalid signature' }, 401);
    }

    const event = JSON.parse(body);

    if (event.event_type === 'transaction.completed') {
      const userId = event.data?.custom_data?.user_id;
      if (!userId) return jsonResponse({ error: 'Missing user_id' }, 400);

      const supabase = getSupabaseAdmin();
      await supabase.from('profiles').update({ plan: 'pro', credits: 300 }).eq('id', userId);
      await supabase.from('usage_logs').insert({ user_id: userId, action: 'upgrade', credits_used: 0, upload_id: null });
    }

    return jsonResponse({ received: true });
  } catch (error) {
    console.error('[handlePaddleWebhook] error:', error);
    captureException(error);
    return jsonResponse({ error: 'Webhook processing failed' }, 500);
  }
}

// =============================================
// CRON AUTOMATION HANDLERS
// =============================================

async function handleCleanupCron(request) {
  const startTime = Date.now();
  try {
    const authHeader = request.headers.get('authorization');
    const cronSecret = authHeader?.replace('Bearer ', '');

    if (!cronSecret || cronSecret !== process.env.CRON_SECRET) {
      return jsonResponse({ error: 'Unauthorized' }, 401);
    }

    const supabase = getSupabaseAdmin();
    const cutoffDate = new Date(Date.now() - 48 * 60 * 60 * 1000);

    const { data: oldUploads, error: fetchError } = await supabase
      .from('uploads')
      .select('id, file_path')
      .lt('created_at', cutoffDate.toISOString())
      .limit(100);

    if (fetchError) throw fetchError;

    let deletedCount = 0;
    if (oldUploads && oldUploads.length > 0) {
      const filePaths = oldUploads.map(u => u.file_path).filter(Boolean);
      if (filePaths.length > 0) {
        await supabase.storage.from('uploads').remove(filePaths);
      }
      const uploadIds = oldUploads.map(u => u.id);
      await supabase.from('results').delete().in('upload_id', uploadIds);
      await supabase.from('uploads').delete().in('id', uploadIds);
      deletedCount = oldUploads.length;
    }

    const rateLimitCutoff = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    await supabase.from('rate_limits').delete().lt('window_start', rateLimitCutoff);

    return jsonResponse({ success: true, deleted: deletedCount, duration_ms: Date.now() - startTime });
  } catch (error) {
    console.error('[CRON] cleanup error:', error);
    captureException(error);
    return jsonResponse({ error: 'Cleanup failed' }, 500);
  }
}

async function handleResetCreditsCron(request) {
  const startTime = Date.now();
  try {
    const authHeader = request.headers.get('authorization');
    const cronSecret = authHeader?.replace('Bearer ', '');

    if (!cronSecret || cronSecret !== process.env.CRON_SECRET) {
      return jsonResponse({ error: 'Unauthorized' }, 401);
    }

    const supabase = getSupabaseAdmin();
    const { data: updated, error: updateError } = await supabase
      .from('profiles')
      .update({ credits: 300 })
      .eq('plan', 'pro')
      .select('id');

    if (updateError) throw updateError;

    return jsonResponse({ success: true, reset_count: updated?.length || 0, duration_ms: Date.now() - startTime });
  } catch (error) {
    console.error('[CRON] reset error:', error);
    captureException(error);
    return jsonResponse({ error: 'Credit reset failed' }, 500);
  }
}

// =============================================
// ADMIN HANDLERS
// =============================================

async function handleAdminGetUsers(request) {
  const { user, error } = await verifyAdmin(request);
  if (error) return error;

  try {
    const supabase = getSupabaseAdmin();
    const { data: profiles } = await supabase
      .from('profiles')
      .select('id, plan, credits, created_at, full_name')
      .order('created_at', { ascending: false });

    const { data: authData } = await supabase.auth.admin.listUsers();
    const emailMap = {};
    if (authData?.users) {
      authData.users.forEach(u => { emailMap[u.id] = u.email; });
    }

    const users = (profiles || []).map(p => ({
      id: p.id,
      email: emailMap[p.id] || 'unknown',
      plan: p.plan,
      credits: p.credits,
      name: p.full_name,
      created_at: p.created_at,
    }));

    return jsonResponse({ users });
  } catch (error) {
    console.error('[adminGetUsers] error:', error);
    captureException(error);
    return jsonResponse({ error: 'Failed to fetch users' }, 500);
  }
}

async function handleAdminUpdateCredits(request) {
  const { user, error: authError } = await verifyAdmin(request);
  if (authError) return authError;

  try {
    const body = await request.json();
    const validationResult = validate(adminCreditsSchema, body);
    if (validationResult.error) return jsonResponse({ error: validationResult.error }, 400);

    const { userId, newCredits } = validationResult.data;
    const supabase = getSupabaseAdmin();

    const { error } = await supabase
      .from('profiles')
      .update({ credits: newCredits })
      .eq('id', userId);

    if (error) return jsonResponse({ error: 'Failed to update credits' }, 500);

    return jsonResponse({ success: true });
  } catch (error) {
    console.error('[adminUpdateCredits] error:', error);
    captureException(error);
    return jsonResponse({ error: 'Failed to update credits' }, 500);
  }
}

async function handleAdminGetStats(request) {
  const { user, error } = await verifyAdmin(request);
  if (error) return error;

  try {
    const supabase = getSupabaseAdmin();

    const { count: totalUsers } = await supabase.from('profiles').select('id', { count: 'exact', head: true });
    const { count: totalProUsers } = await supabase.from('profiles').select('id', { count: 'exact', head: true }).eq('plan', 'pro');

    const todayStart = new Date(); todayStart.setHours(0, 0, 0, 0);
    const monthStart = new Date(); monthStart.setDate(1); monthStart.setHours(0, 0, 0, 0);

    const { count: filesToday } = await supabase.from('usage_logs').select('id', { count: 'exact', head: true })
      .eq('action', 'process').gte('created_at', todayStart.toISOString());
    const { count: filesMonth } = await supabase.from('usage_logs').select('id', { count: 'exact', head: true })
      .eq('action', 'process').gte('created_at', monthStart.toISOString());

    return jsonResponse({
      total_users: totalUsers || 0,
      total_pro_users: totalProUsers || 0,
      files_processed_today: filesToday || 0,
      files_processed_this_month: filesMonth || 0,
    });
  } catch (error) {
    console.error('[adminGetStats] error:', error);
    captureException(error);
    return jsonResponse({ error: 'Failed to fetch stats' }, 500);
  }
}

async function handleAdminGetActivity(request) {
  const { user, error } = await verifyAdmin(request);
  if (error) return error;

  try {
    const supabase = getSupabaseAdmin();
    const { data: logs } = await supabase
      .from('usage_logs')
      .select('id, user_id, action, credits_used, created_at')
      .order('created_at', { ascending: false })
      .limit(20);

    const { data: authData } = await supabase.auth.admin.listUsers();
    const emailMap = {};
    if (authData?.users) {
      authData.users.forEach(u => { emailMap[u.id] = u.email; });
    }

    const activity = (logs || []).map(l => ({
      ...l,
      email: emailMap[l.user_id] || 'unknown',
    }));

    return jsonResponse({ activity });
  } catch (error) {
    console.error('[adminGetActivity] error:', error);
    captureException(error);
    return jsonResponse({ error: 'Something went wrong. Please try again.' }, 500);
  }
}

async function handleAdminSearch(request) {
  const { user, error } = await verifyAdmin(request);
  if (error) return error;

  try {
    const url = new URL(request.url);
    const searchEmail = url.searchParams.get('email');
    if (!searchEmail) return jsonResponse({ error: 'Email query required' }, 400);

    const supabase = getSupabaseAdmin();
    const { data: authData } = await supabase.auth.admin.listUsers();
    const matchedUser = authData?.users?.find(u => u.email?.toLowerCase().includes(searchEmail.toLowerCase()));

    if (!matchedUser) return jsonResponse({ user: null, uploads: [] });

    const profile = await getUserProfile(matchedUser.id);
    const { data: uploads } = await supabase
      .from('uploads')
      .select('id, file_name, status, created_at')
      .eq('user_id', matchedUser.id)
      .order('created_at', { ascending: false })
      .limit(20);

    return jsonResponse({
      user: {
        id: matchedUser.id,
        email: matchedUser.email,
        plan: profile?.plan,
        credits: profile?.credits,
        created_at: profile?.created_at,
      },
      uploads: uploads || [],
    });
  } catch (error) {
    console.error('[adminSearch] error:', error);
    captureException(error);
    return jsonResponse({ error: 'Search failed' }, 500);
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

  if (routePath === 'admin/users') return handleAdminGetUsers(request);
  if (routePath === 'admin/stats') return handleAdminGetStats(request);
  if (routePath === 'admin/activity') return handleAdminGetActivity(request);
  if (routePath === 'admin/search') return handleAdminSearch(request);

  return jsonResponse({ error: 'Not found' }, 404);
}

export async function POST(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath === 'auth/register') return handleRegister(request);
  if (routePath === 'auth/login') return handleLogin(request);
  if (routePath === 'auth/forgot-password') return handleForgotPassword(request);
  if (routePath === 'upload') return handleUpload(request);
  if (routePath === 'process') return handleProcess(request);
  if (routePath === 'contact') return handleContact(request);
  if (routePath === 'payment/create-order') return handleCreateOrder(request);
  if (routePath === 'payment/verify') return handlePaymentVerify(request);
  if (routePath === 'payment/paddle/checkout') return handlePaddleCheckout(request);
  if (routePath === 'webhooks/paddle') return handlePaddleWebhook(request);
  if (routePath === 'cron/cleanup-files' || routePath === 'cron/cleanup') return handleCleanupCron(request);
  if (routePath === 'cron/reset-credits') return handleResetCreditsCron(request);

  if (routePath === 'admin/credits') return handleAdminUpdateCredits(request);

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
