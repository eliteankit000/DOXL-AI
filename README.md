# 📊 DocXL AI - AI-Powered Document to Excel Converter

> Transform PDFs, invoices, bank statements, and images into structured Excel spreadsheets **with EXACT VISUAL LAYOUT PRESERVATION** using GPT-4o.

[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green)](https://supabase.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-blue)](https://openai.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🚀 Features

### ✨ Core Functionality - **NEW v6.0: Layout Reconstruction Engine**
- **🎯 VISUAL LAYOUT PRESERVATION**: Recreates document inside Excel with EXACT original layout
- **📐 Bounding Box Detection**: Uses GPT-4o Vision to analyze element positioning (X/Y coordinates)
- **🧩 Smart Block Classification**: Detects headers, titles, key-value sections, tables, paragraphs, totals, footers
- **📍 Positional Mapping**: Maps document coordinates to Excel grid (X→column, Y→row)
- **📄 Multi-Page Support**: Handles up to 10 pages with separate Excel sheets (Page 1, Page 2, Page 3...)
- **🎨 Style Preservation**: Bold headers, text alignment (left/center/right), merged cells, spacing
- **📊 Multi-Format Support**: PDF, JPG, PNG, WEBP (up to 100MB)
- **✏️ Real-Time Editing**: Edit extracted data before downloading
- **🎯 User-Guided Extraction**: Specify custom requirements for targeted data extraction

### 🔒 Security & Privacy
- ✅ End-to-end encryption (TLS + AES-256)
- ✅ Auto-deletion of files after 48 hours
- ✅ No data sharing or AI training
- ✅ Supabase Row-Level Security (RLS)
- ✅ JWT-based authentication
- ✅ Shell injection protection
- ✅ Rate limiting (5 req/min per user)

### 💳 Payments
- **India**: Razorpay (₹699 for Pro)
- **Global**: Paddle ($9 for Pro)
- **Credits**: Free (5) | Pro (300/month)

### ⚙️ Production-Ready
- ✅ Vercel deployment with serverless functions
- ✅ Automated cron jobs (file cleanup + credit reset)
- ✅ Timeout handling with credit refunds
- ✅ Comprehensive error handling
- ✅ Scalable architecture

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, React, TailwindCSS, shadcn/ui |
| **Backend** | Next.js API Routes (serverless) |
| **Database** | Supabase (PostgreSQL) |
| **Storage** | Supabase Storage |
| **Auth** | Supabase Auth (JWT) |
| **AI** | OpenAI GPT-4o Vision (direct API) |
| **Payments** | Razorpay (IN), Paddle (Global) |
| **Hosting** | Vercel |

---

## 🧠 v6.0 Architecture: 11-Stage Layout Reconstruction Pipeline

### **Stage 1: Page Detection & Multi-Page Handling**
- Extracts individual pages from PDFs (max 10 pages)
- Converts each page to high-resolution image
- Returns list of base64-encoded page images

### **Stage 2-3: Full Document Layout Analysis**
- GPT-4o Vision analyzes visual structure
- Detects bounding boxes for all elements
- Identifies text alignment, spacing, hierarchy
- Classifies sections (header/title/key-value/table/paragraph/totals/footer)

### **Stage 4-5: Positional Reconstruction**
- Maps X coordinates → Excel columns (0-100 scale → A-L columns)
- Maps Y coordinates → Excel rows (vertical positioning)
- Detects spacing between elements → empty rows/columns
- Preserves reading flow (top-to-bottom, left-to-right)

### **Stage 6-7: Text & Data Extraction**
- Extracts text content from each block
- Normalizes data (removes currency symbols, standardizes dates)
- Maintains original values for layout preservation

### **Stage 8-9: Style & Merge Detection**
- Detects bold text (headers, titles, totals)
- Identifies alignment (left/center/right)
- Determines merged cell regions for titles/headers

### **Stage 10: Excel Grid Generation**
- Converts layout analysis to Excel cell instructions
- Format: `{row: N, col: M, value: "text", merge: [start, end], style: {...}}`
- Each cell positioned exactly based on document layout

### **Stage 11: Multi-Sheet Assembly**
- Creates separate worksheet per page
- Assembles final output: `{sheets: [{name: "Page 1", cells: [...]}]}`
- Returns layout-preserved structure for Excel export

### **Excel Export Engine**
- Renders from layout instructions (not sequential rows)
- Places cells at exact row/column positions
- Applies merged cells, styles, column widths
- Generates multi-sheet workbook for multi-page documents

**Result:** Excel file that LOOKS like the original document, not just extracted data.

---

## 📦 Quick Start

### Prerequisites

- Node.js 20+
- Yarn package manager
- Supabase account
- OpenAI API key
- Razorpay account (India payments)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/docxl-ai.git
cd docxl-ai
```

### 2. Install Dependencies

```bash
yarn install
pip install -r requirements.txt  # Python dependencies for AI extraction
```

### 3. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
NEXT_PUBLIC_BASE_URL=http://localhost:3000
OPENAI_API_KEY=sk-proj-your-key-here
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=your-secret
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_test_xxxxx
CRON_SECRET=generate-random-string
```

### 4. Database Setup

Run these SQL files in Supabase SQL Editor:

```bash
# 1. Create schema
/scripts/supabase-schema.sql

# 2. Update constraints
/scripts/migration-usage-logs.sql
```

Create storage bucket:
- Name: `uploads`
- Access: Private

### 5. Run Development Server

```bash
yarn dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## 🗂️ Project Structure

```
docxl-ai/
├── app/
│   ├── api/[[...path]]/route.js   # Main API router
│   ├── page.js                    # Landing + Dashboard
│   ├── contact/page.js            # Contact form
│   ├── terms/page.js              # Terms of Service
│   ├── privacy/page.js            # Privacy Policy
│   └── globals.css                # Global styles
├── scripts/
│   ├── extract.py                 # AI extraction (GPT-4o)
│   ├── supabase-schema.sql        # Database schema
│   └── migration-usage-logs.sql   # DB migration
├── components/
│   ├── ui/                        # shadcn components
│   └── Footer.js                  # Footer component
├── lib/
│   ├── supabase-server.js         # Server-side Supabase
│   └── supabase-browser.js        # Client-side Supabase
├── vercel.json                    # Vercel config + crons
├── next.config.js                 # Next.js config
├── .env.example                   # Environment template
├── DEPLOYMENT.md                  # Deployment guide
└── README.md                      # This file
```

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Sign in
- `GET /api/auth/me` - Get current user

### File Operations
- `POST /api/upload` - Upload file to Supabase Storage
- `GET /api/uploads` - List user's uploads
- `DELETE /api/file/:id` - Delete upload + results

### AI Processing
- `POST /api/process` - Extract data from document (1 credit)
  - Body: `{ upload_id, user_requirements? }`
  - Returns: `{ result: { rows, document_type, confidence } }`

### Results
- `GET /api/result/:id` - Get extraction result
- `PUT /api/result/:id` - Update edited data
- `GET /api/export/excel/:id` - Download Excel

### Payments
- `POST /api/payment/create-order` - Razorpay order (India)
- `POST /api/payment/verify` - Verify Razorpay payment
- `POST /api/payment/paddle/checkout` - Paddle checkout (Global)
- `POST /api/webhooks/paddle` - Paddle webhook

### Cron (Protected by `CRON_SECRET`)
- `POST /api/cron/cleanup` - Delete files >48h old
- `POST /api/cron/reset-credits` - Reset Pro users to 300 credits

---

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://localhost:3000/api/health

# Register
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Automated Testing

```bash
# Run backend tests (if implemented)
yarn test

# Run linting
yarn lint
```

---

## 🚀 Deployment

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for comprehensive production deployment guide.

### Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/docxl-ai)

1. Click the button above
2. Add environment variables
3. Deploy!

---

## 📊 Performance

| Metric | Target | Actual |
|--------|--------|--------|
| Upload time (10MB) | <5s | ~3s |
| AI extraction (invoice) | <30s | ~15-20s |
| Excel export | <2s | ~1s |
| Concurrent users (free) | 100 | ✅ |
| Uptime | 99.9% | Via Vercel SLA |

---

## 🔐 Security

### Implemented Protections

- ✅ **Shell Injection**: Uses `execFile` instead of `exec`
- ✅ **SQL Injection**: Parameterized queries via Supabase
- ✅ **XSS**: React's auto-escaping + CSP headers
- ✅ **CSRF**: JWT tokens + SameSite cookies
- ✅ **Rate Limiting**: 5 req/min on AI processing
- ✅ **Payment Security**: HMAC signature verification
- ✅ **Data Exposure**: RLS policies + auto-deletion

### Recommendations

- Run `npm audit` regularly
- Enable Vercel Firewall (paid) for DDoS protection
- Rotate API keys quarterly
- Monitor Supabase logs for suspicious queries

---

## 💰 Pricing & Credits

### Free Plan
- 5 credits (lifetime)
- All features
- 48h file retention

### Pro Plan
- ₹699/month (India) or $9/month (Global)
- 300 credits/month (resets on 1st)
- Priority support
- Same 48h retention

### Credit Usage
- 1 credit = 1 document processed
- Failed extractions = credit refunded
- Exports = free

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 📞 Support

- **Email**: support@docxl.ai
- **Contact Form**: [docxl.ai/contact](https://docxl.ai/contact)
- **Documentation**: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) for GPT-4o API
- [Supabase](https://supabase.com) for backend infrastructure
- [Vercel](https://vercel.com) for hosting
- [shadcn/ui](https://ui.shadcn.com) for beautiful components
- [Razorpay](https://razorpay.com) & [Paddle](https://paddle.com) for payments

---

**Built with ❤️ for accountants, finance teams, and anyone drowning in paperwork.**
