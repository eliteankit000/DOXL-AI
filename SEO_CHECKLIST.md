# Post-Deployment SEO Checklist

## Step 1 — Google Search Console
1. Go to https://search.google.com/search-console
2. Add property: https://docxl.ai
3. Verify via HTML meta tag — copy the content value and set as
   NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION in Vercel
4. Redeploy the app after setting the env variable
5. Go to Sitemaps → Submit: https://docxl.ai/sitemap.xml
6. Go to URL Inspection → test https://docxl.ai → Request Indexing
7. Repeat URL Inspection for /pricing, /blog, all 3 blog articles

## Step 2 — Google Analytics 4 (optional but recommended)
1. Create GA4 property at analytics.google.com
2. Add NEXT_PUBLIC_GA_MEASUREMENT_ID to Vercel env variables
3. Add to app/layout.js:
   `<Script src={\`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID}\`} strategy="afterInteractive" />`

## Step 3 — Bing Webmaster Tools
1. Go to https://www.bing.com/webmasters
2. Import from Google Search Console (one click)

## Step 4 — Check these scores after deploy
- PageSpeed Insights: https://pagespeed.web.dev/ → target 90+ mobile
- Lighthouse in Chrome DevTools → target 90+ SEO score
- https://validator.schema.org/ → paste https://docxl.ai → verify
  no errors in JSON-LD
- https://www.heymeta.com/ → paste https://docxl.ai → verify
  OG tags render correctly
- https://www.xml-sitemaps.com/validate-xml-sitemap.html →
  paste https://docxl.ai/sitemap.xml → no errors
