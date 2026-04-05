# DocXL AI - PRD

## Product Overview
DocXL AI is a SaaS platform that converts PDFs, invoices, bank statements, and images into structured Excel spreadsheets using AI (GPT-4o Vision).

## Architecture
- **Frontend**: Next.js 14 with Tailwind CSS + shadcn/ui
- **Backend**: Next.js API routes (route.js)
- **Database**: Supabase (PostgreSQL + Auth + Storage)
- **AI Engine**: Python script (extract.py) - GPT-4o via OpenAI API
- **Payment**: Razorpay (India) + Paddle (planned for global)

## Key Features
1. **Document Upload**: PDF, JPG, PNG, WEBP (up to 100MB)
2. **AI Extraction Pipeline v3**: 
   - 3-layer: OCR → Structured Parsing → Normalization
   - 3-attempt retry with escalating strategies
   - Rule-based parsers for bank statements + invoices
   - Never-fail guarantee: always returns partial results
3. **Post-Processing Instruction Engine**:
   - Remove/filter by amount thresholds
   - Only include specific types (debits/credits/GST)
   - Rename columns, group by field, sort
   - Applied AFTER full extraction
4. **Editable Data Table**: Edit, add, delete, duplicate rows
5. **Export**: Excel (.xlsx) and JSON
6. **Location-Based Pricing**: Auto-detect via GeoIP (₹699 India, $9 global)
7. **User Flow**: Upload → Review & Instruct → Start Extraction → Edit → Export

## API Endpoints
- GET /api/health - Health check
- GET /api/geo - GeoIP location + pricing detection
- POST /api/auth/register - User registration
- POST /api/auth/login - User login
- GET /api/auth/me - Get user profile
- POST /api/upload - Upload document
- POST /api/process - Process document (never fails)
- GET /api/result/:id - Get extraction result
- PUT /api/result/:id - Update result (save edits)
- GET /api/export/excel/:id - Download Excel
- GET /api/uploads - List user uploads
- DELETE /api/file/:id - Delete upload
- POST /api/payment/create-order - Razorpay order
- POST /api/payment/verify - Verify payment
- POST /api/contact - Contact form (Brevo)
- POST /api/auth/forgot-password - Password reset
- Admin endpoints (5 endpoints)
