import { NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';
import { v4 as uuidv4 } from 'uuid';
import { writeFile, unlink, readFile, mkdir, access } from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

const execAsync = promisify(exec);
const JWT_SECRET = process.env.JWT_SECRET || 'docxl-ai-secret-key-2025';
const UPLOAD_DIR = '/tmp/uploads';

// MongoDB connection
let client = null;
let db = null;

async function getDb() {
  if (!db) {
    client = new MongoClient(process.env.MONGO_URL);
    await client.connect();
    db = client.db(process.env.DB_NAME);
  }
  return db;
}

// Ensure upload directory exists
async function ensureUploadDir() {
  try {
    await access(UPLOAD_DIR);
  } catch {
    await mkdir(UPLOAD_DIR, { recursive: true });
  }
}

// Auth middleware
function getTokenFromRequest(request) {
  const authHeader = request.headers.get('authorization');
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }
  return null;
}

function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch {
    return null;
  }
}

async function getAuthUser(request) {
  const token = getTokenFromRequest(request);
  if (!token) return null;
  const decoded = verifyToken(token);
  if (!decoded) return null;
  const database = await getDb();
  const user = await database.collection('users').findOne({ id: decoded.userId });
  return user;
}

// CORS headers
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}

// === AUTH HANDLERS ===
async function handleRegister(request) {
  try {
    const body = await request.json();
    const { email, password, name } = body;
    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password required' }, { status: 400, headers: corsHeaders() });
    }
    const database = await getDb();
    const existing = await database.collection('users').findOne({ email: email.toLowerCase() });
    if (existing) {
      return NextResponse.json({ error: 'Email already registered' }, { status: 409, headers: corsHeaders() });
    }
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = {
      id: uuidv4(),
      email: email.toLowerCase(),
      name: name || email.split('@')[0],
      password: hashedPassword,
      plan: 'free',
      credits_remaining: 5,
      country: 'unknown',
      created_at: new Date().toISOString(),
    };
    await database.collection('users').insertOne(user);
    const token = jwt.sign({ userId: user.id, email: user.email }, JWT_SECRET, { expiresIn: '7d' });
    const { password: _, ...userWithoutPassword } = user;
    return NextResponse.json({ token, user: userWithoutPassword }, { status: 201, headers: corsHeaders() });
  } catch (error) {
    console.error('Register error:', error);
    return NextResponse.json({ error: 'Registration failed' }, { status: 500, headers: corsHeaders() });
  }
}

async function handleLogin(request) {
  try {
    const body = await request.json();
    const { email, password } = body;
    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password required' }, { status: 400, headers: corsHeaders() });
    }
    const database = await getDb();
    const user = await database.collection('users').findOne({ email: email.toLowerCase() });
    if (!user) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401, headers: corsHeaders() });
    }
    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401, headers: corsHeaders() });
    }
    const token = jwt.sign({ userId: user.id, email: user.email }, JWT_SECRET, { expiresIn: '7d' });
    const { password: _, ...userWithoutPassword } = user;
    return NextResponse.json({ token, user: userWithoutPassword }, { status: 200, headers: corsHeaders() });
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json({ error: 'Login failed' }, { status: 500, headers: corsHeaders() });
  }
}

async function handleGetMe(request) {
  const user = await getAuthUser(request);
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders() });
  }
  const { password: _, ...userWithoutPassword } = user;
  return NextResponse.json({ user: userWithoutPassword }, { headers: corsHeaders() });
}

// === UPLOAD HANDLER ===
async function handleUpload(request) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders() });
    }
    if (user.credits_remaining <= 0) {
      return NextResponse.json({ error: 'No credits remaining. Please upgrade to Pro.' }, { status: 403, headers: corsHeaders() });
    }
    await ensureUploadDir();
    const formData = await request.formData();
    const file = formData.get('file');
    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400, headers: corsHeaders() });
    }
    const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
    const ext = path.extname(file.name).toLowerCase();
    const validExts = ['.pdf', '.jpg', '.jpeg', '.png', '.webp'];
    if (!validExts.includes(ext)) {
      return NextResponse.json({ error: 'Invalid file type. Supported: PDF, JPG, PNG, WEBP' }, { status: 400, headers: corsHeaders() });
    }
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return NextResponse.json({ error: 'File too large. Maximum 10MB allowed.' }, { status: 400, headers: corsHeaders() });
    }
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const fileName = `${user.id}/${Date.now()}_${file.name.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
    const userDir = path.join(UPLOAD_DIR, user.id);
    await mkdir(userDir, { recursive: true });
    const filePath = path.join(UPLOAD_DIR, fileName);
    await writeFile(filePath, buffer);
    let fileType = 'other';
    if (ext === '.pdf') fileType = 'invoice';
    else fileType = 'image';
    const upload = {
      id: uuidv4(),
      user_id: user.id,
      file_name: file.name,
      file_path: filePath,
      file_size: file.size,
      file_type: fileType,
      mime_type: file.type || 'application/octet-stream',
      status: 'uploaded',
      error_message: null,
      created_at: new Date().toISOString(),
    };
    const database = await getDb();
    await database.collection('uploads').insertOne(upload);
    return NextResponse.json({ upload: { id: upload.id, file_name: upload.file_name, status: upload.status, file_type: upload.file_type, created_at: upload.created_at } }, { status: 201, headers: corsHeaders() });
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json({ error: 'Upload failed: ' + error.message }, { status: 500, headers: corsHeaders() });
  }
}

// === PROCESS HANDLER ===
async function handleProcess(request) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders() });
    }
    const body = await request.json();
    const { upload_id } = body;
    if (!upload_id) {
      return NextResponse.json({ error: 'upload_id required' }, { status: 400, headers: corsHeaders() });
    }
    const database = await getDb();
    const upload = await database.collection('uploads').findOne({ id: upload_id, user_id: user.id });
    if (!upload) {
      return NextResponse.json({ error: 'Upload not found' }, { status: 404, headers: corsHeaders() });
    }
    if (upload.status === 'processing') {
      return NextResponse.json({ error: 'Already processing' }, { status: 400, headers: corsHeaders() });
    }
    // Set status to processing
    await database.collection('uploads').updateOne({ id: upload_id }, { $set: { status: 'processing' } });
    // Call Python extraction script
    try {
      const { stdout, stderr } = await execAsync(
        `cd /app && EMERGENT_LLM_KEY="${process.env.EMERGENT_LLM_KEY}" /root/.venv/bin/python3 scripts/extract.py "${upload.file_path}"`,
        { timeout: 120000, maxBuffer: 10 * 1024 * 1024 }
      );
      if (stderr) {
        console.error('Extract stderr:', stderr);
      }
      let result;
      try {
        result = JSON.parse(stdout.trim());
      } catch (parseError) {
        throw new Error('Failed to parse extraction result: ' + stdout.substring(0, 200));
      }
      if (result.error) {
        await database.collection('uploads').updateOne(
          { id: upload_id },
          { $set: { status: 'failed', error_message: result.error } }
        );
        return NextResponse.json({ error: result.error }, { status: 422, headers: corsHeaders() });
      }
      // Normalize the result
      const normalizedRows = (result.rows || []).map((row, index) => ({
        id: uuidv4(),
        row_number: index + 1,
        date: row.date || '',
        description: row.description || '',
        amount: parseFloat(row.amount) || 0,
        type: row.type || 'debit',
        category: row.category || '',
        gst: parseFloat(row.gst) || 0,
        reference: row.reference || '',
      }));
      const extractedData = {
        id: uuidv4(),
        upload_id: upload_id,
        document_type: result.document_type || 'other',
        structured_json: { rows: normalizedRows },
        summary: result.summary || { total_rows: normalizedRows.length, total_amount: normalizedRows.reduce((sum, r) => sum + r.amount, 0) },
        confidence_score: 0.85,
        created_at: new Date().toISOString(),
      };
      await database.collection('extracted_data').insertOne(extractedData);
      await database.collection('uploads').updateOne(
        { id: upload_id },
        { $set: { status: 'completed' } }
      );
      // Deduct credit
      await database.collection('users').updateOne(
        { id: user.id },
        { $inc: { credits_remaining: -1 } }
      );
      return NextResponse.json({
        result: {
          id: extractedData.id,
          upload_id: upload_id,
          document_type: extractedData.document_type,
          rows: normalizedRows,
          summary: extractedData.summary,
          confidence_score: extractedData.confidence_score,
        }
      }, { headers: corsHeaders() });
    } catch (execError) {
      console.error('Extraction error:', execError);
      await database.collection('uploads').updateOne(
        { id: upload_id },
        { $set: { status: 'failed', error_message: execError.message } }
      );
      return NextResponse.json({ error: 'AI extraction failed: ' + execError.message }, { status: 500, headers: corsHeaders() });
    }
  } catch (error) {
    console.error('Process error:', error);
    return NextResponse.json({ error: 'Processing failed' }, { status: 500, headers: corsHeaders() });
  }
}

// === RESULT HANDLER ===
async function handleGetResult(request, id) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders() });
    }
    const database = await getDb();
    // Try by extracted_data id first
    let extractedData = await database.collection('extracted_data').findOne({ id: id });
    if (!extractedData) {
      // Try by upload_id
      extractedData = await database.collection('extracted_data').findOne({ upload_id: id });
    }
    if (!extractedData) {
      return NextResponse.json({ error: 'Result not found' }, { status: 404, headers: corsHeaders() });
    }
    // Verify ownership
    const upload = await database.collection('uploads').findOne({ id: extractedData.upload_id, user_id: user.id });
    if (!upload) {
      return NextResponse.json({ error: 'Not authorized to view this result' }, { status: 403, headers: corsHeaders() });
    }
    return NextResponse.json({
      result: {
        id: extractedData.id,
        upload_id: extractedData.upload_id,
        document_type: extractedData.document_type,
        rows: extractedData.structured_json?.rows || [],
        summary: extractedData.summary,
        confidence_score: extractedData.confidence_score,
        file_name: upload.file_name,
        created_at: extractedData.created_at,
      }
    }, { headers: corsHeaders() });
  } catch (error) {
    console.error('Get result error:', error);
    return NextResponse.json({ error: 'Failed to get result' }, { status: 500, headers: corsHeaders() });
  }
}

// === UPLOADS LIST HANDLER ===
async function handleGetUploads(request) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders() });
    }
    const database = await getDb();
    const uploads = await database.collection('uploads')
      .find({ user_id: user.id })
      .sort({ created_at: -1 })
      .limit(50)
      .toArray();
    const uploadsClean = uploads.map(u => ({
      id: u.id,
      file_name: u.file_name,
      file_type: u.file_type,
      status: u.status,
      error_message: u.error_message,
      created_at: u.created_at,
    }));
    return NextResponse.json({ uploads: uploadsClean }, { headers: corsHeaders() });
  } catch (error) {
    console.error('Get uploads error:', error);
    return NextResponse.json({ error: 'Failed to get uploads' }, { status: 500, headers: corsHeaders() });
  }
}

// === DELETE FILE HANDLER ===
async function handleDeleteFile(request, id) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders() });
    }
    const database = await getDb();
    const upload = await database.collection('uploads').findOne({ id: id, user_id: user.id });
    if (!upload) {
      return NextResponse.json({ error: 'File not found' }, { status: 404, headers: corsHeaders() });
    }
    // Delete physical file
    try {
      await unlink(upload.file_path);
    } catch (e) {
      console.error('File delete error:', e);
    }
    // Delete from DB
    await database.collection('uploads').deleteOne({ id: id });
    await database.collection('extracted_data').deleteMany({ upload_id: id });
    return NextResponse.json({ message: 'File deleted' }, { headers: corsHeaders() });
  } catch (error) {
    console.error('Delete file error:', error);
    return NextResponse.json({ error: 'Delete failed' }, { status: 500, headers: corsHeaders() });
  }
}

// === EXPORT EXCEL HANDLER ===
async function handleExportExcel(request, id) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders() });
    }
    const database = await getDb();
    let extractedData = await database.collection('extracted_data').findOne({ id: id });
    if (!extractedData) {
      extractedData = await database.collection('extracted_data').findOne({ upload_id: id });
    }
    if (!extractedData) {
      return NextResponse.json({ error: 'Result not found' }, { status: 404, headers: corsHeaders() });
    }
    // Verify ownership
    const upload = await database.collection('uploads').findOne({ id: extractedData.upload_id, user_id: user.id });
    if (!upload) {
      return NextResponse.json({ error: 'Not authorized' }, { status: 403, headers: corsHeaders() });
    }
    const ExcelJS = (await import('exceljs')).default;
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Extracted Data');
    // Define columns
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
    // Style header
    worksheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } };
    worksheet.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1D4ED8' } };
    // Add data
    const rows = extractedData.structured_json?.rows || [];
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
    // Add summary row
    const lastRow = worksheet.addRow({});
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
    // Generate buffer
    const buffer = await workbook.xlsx.writeBuffer();
    const headers = {
      ...corsHeaders(),
      'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'Content-Disposition': `attachment; filename="docxl_export_${Date.now()}.xlsx"`,
    };
    return new NextResponse(buffer, { status: 200, headers });
  } catch (error) {
    console.error('Export error:', error);
    return NextResponse.json({ error: 'Export failed: ' + error.message }, { status: 500, headers: corsHeaders() });
  }
}

// === UPDATE RESULT HANDLER ===
async function handleUpdateResult(request, id) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders() });
    }
    const body = await request.json();
    const { rows } = body;
    if (!rows) {
      return NextResponse.json({ error: 'rows required' }, { status: 400, headers: corsHeaders() });
    }
    const database = await getDb();
    let extractedData = await database.collection('extracted_data').findOne({ id: id });
    if (!extractedData) {
      extractedData = await database.collection('extracted_data').findOne({ upload_id: id });
    }
    if (!extractedData) {
      return NextResponse.json({ error: 'Result not found' }, { status: 404, headers: corsHeaders() });
    }
    // Verify ownership
    const upload = await database.collection('uploads').findOne({ id: extractedData.upload_id, user_id: user.id });
    if (!upload) {
      return NextResponse.json({ error: 'Not authorized' }, { status: 403, headers: corsHeaders() });
    }
    await database.collection('extracted_data').updateOne(
      { id: extractedData.id },
      { $set: { 'structured_json.rows': rows, updated_at: new Date().toISOString() } }
    );
    return NextResponse.json({ message: 'Updated successfully' }, { headers: corsHeaders() });
  } catch (error) {
    console.error('Update result error:', error);
    return NextResponse.json({ error: 'Update failed' }, { status: 500, headers: corsHeaders() });
  }
}

// === ROUTE HANDLERS ===
export async function GET(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath === '' || routePath === 'health') {
    return NextResponse.json({ status: 'ok', service: 'DocXL AI API' }, { headers: corsHeaders() });
  }
  if (routePath === 'auth/me') {
    return handleGetMe(request);
  }
  if (routePath === 'uploads') {
    return handleGetUploads(request);
  }
  if (routePath.startsWith('result/')) {
    return handleGetResult(request, pathSegments[1]);
  }
  if (routePath.startsWith('export/excel/')) {
    return handleExportExcel(request, pathSegments[2]);
  }
  return NextResponse.json({ error: 'Not found' }, { status: 404, headers: corsHeaders() });
}

export async function POST(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath === 'auth/register') {
    return handleRegister(request);
  }
  if (routePath === 'auth/login') {
    return handleLogin(request);
  }
  if (routePath === 'upload') {
    return handleUpload(request);
  }
  if (routePath === 'process') {
    return handleProcess(request);
  }
  return NextResponse.json({ error: 'Not found' }, { status: 404, headers: corsHeaders() });
}

export async function PUT(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath.startsWith('result/')) {
    return handleUpdateResult(request, pathSegments[1]);
  }
  return NextResponse.json({ error: 'Not found' }, { status: 404, headers: corsHeaders() });
}

export async function DELETE(request, context) {
  const params = context?.params || {};
  const pathSegments = params.path || [];
  const routePath = pathSegments.join('/');

  if (routePath.startsWith('file/')) {
    return handleDeleteFile(request, pathSegments[1]);
  }
  return NextResponse.json({ error: 'Not found' }, { status: 404, headers: corsHeaders() });
}

export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders() });
}
