# 🚀 DocXL AI - Production Deployment Guide

## 📋 Pre-Deployment Checklist

### ✅ Required Services & Credentials

Before deploying, ensure you have:

- [ ] **Supabase Project** (PostgreSQL + Storage + Auth)
  - Database schema applied
  - Storage bucket created
  - API keys ready
  
- [ ] **OpenAI API Key** (gpt-4o access)
  - Billing enabled
  - Key starts with `sk-proj-`
  
- [ ] **Razorpay Account** (India Payments)
  - KYC completed
  - Live API keys
  
- [ ] **Paddle Account** (Optional - Global Payments)
  - Product & pricing configured
  - Webhook endpoint ready
  
- [ ] **Vercel Account** (Free tier works)
  - GitHub repo connected

---

## 🗄️ Step 1: Database Setup (Supabase)

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Choose a region close to your users (e.g., `ap-south-1` for India)
3. Wait for provisioning (~2 minutes)

### 1.2 Run SQL Schema

In the Supabase SQL Editor, run these files in order:

```sql
-- File: /scripts/supabase-schema.sql
-- This creates all tables, triggers, and RPC functions
```

```sql
-- File: /scripts/migration-usage-logs.sql
-- This updates the usage_logs constraint for new action types
```

### 1.3 Create Storage Bucket

1. Go to **Storage** in Supabase dashboard
2. Click **New Bucket**
3. Name: `uploads`
4. **Public:** ❌ No (Keep private)
5. Click **Create bucket**

### 1.4 Get API Keys

Go to **Settings → API** and copy:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (⚠️ Keep secret!)

---

## 🤖 Step 2: OpenAI Setup

1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Go to **Billing** → Add payment method
3. Go to **API Keys** → Create new key
4. Copy the key (starts with `sk-proj-...`)
5. ⚠️ **Save it immediately** - you won't see it again!

**Pricing:** ~$0.01-0.05 per document depending on complexity

---

## 💳 Step 3: Payment Providers

### 3.1 Razorpay (India - Required)

1. Sign up at [razorpay.com](https://razorpay.com)
2. Complete KYC (Aadhaar + PAN required)
3. Wait for approval (~24-48 hours)
4. Go to **Settings → API Keys** → Generate Live Keys
5. Copy:
   - `RAZORPAY_KEY_ID` (e.g., `rzp_live_xxxxx`)
   - `RAZORPAY_KEY_SECRET`

**Pricing:** ₹699/transaction → Razorpay charges 2% (~₹14)

### 3.2 Paddle (Global - Optional)

1. Sign up at [paddle.com](https://paddle.com/signup)
2. Complete business verification
3. Create a **Product**: DocXL AI Pro
4. Create a **Price**: $9.00 USD (recurring: monthly or one-time)
5. Copy the `PADDLE_PRICE_ID` (e.g., `pri_01xxxxx`)
6. Go to **Developer Tools → Authentication** → Create API key
7. Copy `PADDLE_API_KEY`
8. Go to **Webhooks** → Add endpoint:
   - URL: `https://your-app.vercel.app/api/webhooks/paddle`
   - Events: Select `transaction.completed`
   - Copy the `PADDLE_WEBHOOK_SECRET`

**Pricing:** $9/transaction → Paddle charges 5% + $0.50 (~$1)

---

## ☁️ Step 4: Vercel Deployment

### 4.1 Connect Repository

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. **Framework Preset:** Next.js (auto-detected)
4. **Root Directory:** `./` (default)

### 4.2 Add Environment Variables

In Vercel dashboard → **Settings → Environment Variables**, add:

```bash
# Required
NEXT_PUBLIC_BASE_URL=https://your-app.vercel.app
OPENAI_API_KEY=sk-proj-your-key-here
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
RAZORPAY_KEY_ID=rzp_live_xxxxx
RAZORPAY_KEY_SECRET=your-secret
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_live_xxxxx
CRON_SECRET=generate-random-32-char-string

# Optional (add when you have them)
PADDLE_API_KEY=your-paddle-api-key
PADDLE_PRICE_ID=pri_01xxxxx
PADDLE_WEBHOOK_SECRET=pdl_whsec_xxxxx
NEXT_PUBLIC_FORMSPREE_FORM_ID=your-form-id
```

**Generate `CRON_SECRET`:**
```bash
openssl rand -hex 32
# Or use: https://randomkeygen.com/
```

### 4.3 Build Settings

Vercel auto-detects Next.js, but verify:

- **Build Command:** `yarn build`
- **Output Directory:** `.next`
- **Install Command:** `yarn install`
- **Node Version:** 20.x (auto)

### 4.4 Deploy

1. Click **Deploy**
2. Wait ~2-3 minutes for build
3. Once live, update `NEXT_PUBLIC_BASE_URL` to your actual Vercel URL
4. Trigger a redeploy

---

## ⏰ Step 5: Configure Cron Jobs

### 5.1 Enable Vercel Cron

Cron jobs are defined in `/vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/cron/cleanup",
      "schedule": "0 */6 * * *"  // Every 6 hours
    },
    {
      "path": "/api/cron/reset-credits",
      "schedule": "0 0 1 * *"  // 1st of every month
    }
  ]
}
```

### 5.2 Test Cron Endpoints

```bash
# Test cleanup (deletes files >48h old)
curl -X POST https://your-app.vercel.app/api/cron/cleanup \
  -H "Authorization: Bearer YOUR_CRON_SECRET"

# Test credit reset (resets Pro users to 300 credits)
curl -X POST https://your-app.vercel.app/api/cron/reset-credits \
  -H "Authorization: Bearer YOUR_CRON_SECRET"
```

Expected response:
```json
{
  "success": true,
  "deleted": 5,  // cleanup
  "reset_count": 12  // credit reset
}
```

---

## 🧪 Step 6: Production Testing

### 6.1 Smoke Tests

- [ ] User Registration works
- [ ] Login works  
- [ ] File upload succeeds (try PDF + image)
- [ ] AI extraction completes (<2 min for simple docs)
- [ ] Excel export downloads
- [ ] Razorpay payment flow (test with ₹1 first!)
- [ ] Credits deduct correctly
- [ ] Timeout refund works (test with huge PDF)

### 6.2 Load Testing (Optional)

Use [k6](https://k6.io/) or [Artillery](https://www.artillery.io/):

```bash
# Test 100 concurrent users
artillery quick --count 100 --num 10 https://your-app.vercel.app
```

Vercel free tier supports ~100 concurrent users.

---

## 📊 Step 7: Monitoring & Observability

### 7.1 Vercel Analytics

Enable in: **Project Settings → Analytics**

- [ ] Web Analytics (pageviews, bounce rate)
- [ ] Speed Insights (Core Web Vitals)

### 7.2 Supabase Logs

Monitor database queries:
- Go to **Logs** → **Postgres Logs**
- Watch for slow queries (>1s)

### 7.3 Error Tracking

Recommended: [Sentry](https://sentry.io/welcome/) (free tier: 5K errors/month)

```bash
yarn add @sentry/nextjs
npx @sentry/wizard -i nextjs
```

---

## 🔒 Step 8: Security Hardening

### 8.1 Environment Variable Audit

- [ ] All secrets in Vercel environment variables (NOT in code)
- [ ] `.env` added to `.gitignore`
- [ ] `CRON_SECRET` is strong (32+ chars)
- [ ] Supabase Row Level Security (RLS) enabled

### 8.2 Supabase RLS Policies

Check policies are active:

```sql
-- Verify RLS is ON
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- All tables should show: rowsecurity = true
```

### 8.3 Rate Limiting

Already implemented in code:
- ✅ 5 requests/min per user on `/api/process`
- Consider adding Vercel Firewall (paid) for DDoS protection

---

## 🚨 Step 9: Incident Response Plan

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 500 errors on upload | Supabase storage full | Increase quota or run cleanup cron |
| AI extraction fails | OpenAI API key exhausted | Add billing or upgrade plan |
| Slow processing | Large PDFs | Increase Vercel timeout (paid plans) |
| Payment not reflecting | Webhook failed | Check Razorpay/Paddle webhook logs |

### Emergency Contacts

- **Vercel Support:** support@vercel.com (Pro plan required)
- **Supabase Support:** Dashboard → Support
- **OpenAI:** help.openai.com

---

## ✅ Post-Deployment Checklist

- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (auto via Vercel)
- [ ] Analytics tracking added
- [ ] First 10 test users signed up successfully
- [ ] Payment flow tested end-to-end
- [ ] Backup strategy documented (Supabase auto-backups)
- [ ] Team has access to Vercel/Supabase dashboards

---

## 📈 Scaling Considerations

### Current Limits (Free Tiers)

- **Vercel:** 100GB bandwidth, 100 serverless function calls/hour
- **Supabase:** 500MB database, 1GB storage, 2GB bandwidth
- **OpenAI:** Pay-as-you-go (no limit)

### When to Upgrade

| Metric | Free Limit | Upgrade Trigger |
|--------|-----------|-----------------|
| Users | ~500 | >500 MAU |
| Database | 500MB | >400MB used |
| Storage | 1GB | >800MB files |
| API calls | 100/hr | Consistent throttling |

**Recommended Paid Plans:**
- Vercel Pro: $20/month (unlimited bandwidth)
- Supabase Pro: $25/month (8GB DB, 100GB storage)

---

## 🎉 You're Live!

Your DocXL AI app is now production-ready. Monitor the following for the first week:

- Error rates (should be <1%)
- Average processing time (should be <30s)
- Payment success rate (should be >95%)
- User complaints (should be minimal)

**Need Help?** Open an issue on GitHub or contact support.

---

**Last Updated:** January 2025  
**Next Review:** March 2025 (or after 1000 users)
