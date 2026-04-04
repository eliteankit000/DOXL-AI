import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'DocXL AI — Convert PDF, Invoice & Bank Statement to Excel with AI',
  description: 'Upload any PDF, invoice, bank statement, receipt, or image and instantly convert it to structured Excel data using AI. Free 5 extractions. Fast, accurate, secure.',
  keywords: [
    'PDF to Excel', 'convert PDF to Excel', 'invoice to Excel', 'bank statement to Excel',
    'AI document extraction', 'PDF data extraction', 'image to spreadsheet', 'receipt to Excel',
    'OCR PDF to Excel', 'financial document parser', 'AI invoice reader', 'extract table from PDF',
    'DocXL AI', 'document to structured data', 'PDF to CSV', 'automated data entry',
    'bank statement parser', 'invoice data extractor', 'AI powered OCR', 'document processing AI',
  ].join(', '),
  authors: [{ name: 'DocXL AI' }],
  creator: 'DocXL AI',
  publisher: 'DocXL AI',
  robots: { index: true, follow: true, googleBot: { index: true, follow: true } },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'DocXL AI',
    title: 'DocXL AI — Convert PDF, Invoice & Bank Statement to Excel with AI',
    description: 'Upload any PDF, invoice, bank statement, or image and instantly convert it to structured Excel data using AI. Free 5 extractions.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'DocXL AI — PDF to Excel with AI',
    description: 'Convert PDFs, invoices, bank statements & images to structured Excel data instantly with AI.',
    creator: '@docxlai',
  },
  alternates: {
    canonical: '/',
  },
  category: 'Technology',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#1D4ED8" />
        <link rel="canonical" href="https://docxl.ai" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'SoftwareApplication',
              name: 'DocXL AI',
              applicationCategory: 'BusinessApplication',
              operatingSystem: 'Web',
              description: 'AI-powered document to Excel converter. Upload PDFs, invoices, bank statements, or images and get structured Excel data instantly.',
              offers: [
                { '@type': 'Offer', price: '0', priceCurrency: 'USD', name: 'Free Plan — 5 extractions' },
                { '@type': 'Offer', price: '9', priceCurrency: 'USD', name: 'Pro Plan — 300 extractions/month' },
              ],
              aggregateRating: { '@type': 'AggregateRating', ratingValue: '4.8', ratingCount: '120' },
              featureList: [
                'PDF to Excel conversion',
                'Invoice data extraction',
                'Bank statement parsing',
                'Image and receipt OCR',
                'Editable results table',
                'AI-powered accuracy',
                'XLSX and JSON export',
              ],
            }),
          }}
        />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
