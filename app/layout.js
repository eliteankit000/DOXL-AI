import { Inter } from 'next/font/google';
import './globals.css';
import JsonLd from '@/components/JsonLd';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  metadataBase: new URL('https://docxl.ai'),
  title: {
    default: 'DocXL AI — Convert PDF to Excel Free Online',
    template: '%s | DocXL AI',
  },
  description:
    'DocXL AI converts PDFs, invoices, bank statements, and images to ' +
    'editable Excel spreadsheets in seconds using GPT-4o AI. Free to try. ' +
    'No signup required for first conversion.',
  keywords: [
    'pdf to excel converter',
    'convert pdf to excel',
    'pdf to excel free',
    'pdf table to excel',
    'invoice to excel',
    'bank statement to excel',
    'image to excel',
    'AI pdf converter',
    'extract table from pdf',
    'pdf data extraction',
    'convert pdf to spreadsheet',
    'pdf to xlsx',
    'ocr to excel',
    'gpt4 pdf converter',
    'docxl ai',
  ],
  authors: [{ name: 'DocXL AI', url: 'https://docxl.ai' }],
  creator: 'DocXL AI',
  publisher: 'DocXL AI',
  category: 'Productivity',
  classification: 'Business/Productivity',
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  alternates: {
    canonical: 'https://docxl.ai',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://docxl.ai',
    siteName: 'DocXL AI',
    title: 'DocXL AI — Convert PDF to Excel Free Online Using AI',
    description:
      'Upload any PDF, invoice, or image and get a perfectly formatted ' +
      'Excel file in seconds. Powered by GPT-4o. Try free today.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'DocXL AI — PDF to Excel Converter powered by GPT-4o',
        type: 'image/png',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@docxlai',
    creator: '@docxlai',
    title: 'DocXL AI — Convert PDF to Excel Free Online Using AI',
    description:
      'Upload any PDF, invoice, or image and get a perfectly formatted ' +
      'Excel file in seconds. Powered by GPT-4o.',
    images: ['/og-image.png'],
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION || '',
  },
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/icon.png', type: 'image/png', sizes: '32x32' },
      { url: '/icon-16.png', type: 'image/png', sizes: '16x16' },
      { url: '/icon-192.png', type: 'image/png', sizes: '192x192' },
      { url: '/icon-512.png', type: 'image/png', sizes: '512x512' },
    ],
    apple: [
      { url: '/apple-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    shortcut: '/favicon.ico',
  },
  other: {
    'application-name': 'DocXL AI',
  },
};

const webAppSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebApplication',
  name: 'DocXL AI',
  url: 'https://docxl.ai',
  logo: 'https://docxl.ai/logo.png',
  description: 'AI-powered PDF to Excel converter using GPT-4o',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  offers: [
    {
      '@type': 'Offer',
      name: 'Free Plan',
      price: '0',
      priceCurrency: 'USD',
      description: '5 free PDF to Excel conversions',
    },
    {
      '@type': 'Offer',
      name: 'Pro Plan',
      price: '9',
      priceCurrency: 'USD',
      priceSpecification: {
        '@type': 'UnitPriceSpecification',
        billingDuration: 'P1M',
      },
      description: '300 PDF to Excel conversions per month',
    },
  ],
  featureList: [
    'Convert PDF to Excel',
    'Convert images to Excel',
    'Invoice data extraction',
    'Bank statement conversion',
    'GPT-4o powered accuracy',
    'Instant download',
  ],
  screenshot: 'https://docxl.ai/og-image.png',
  softwareVersion: '1.0',
  contactPoint: {
    '@type': 'ContactPoint',
    email: 'hello@docxlai.com',
    contactType: 'customer support',
  },
};

const orgSchema = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'DocXL AI',
  url: 'https://docxl.ai',
  logo: 'https://docxl.ai/logo.png',
  email: 'hello@docxlai.com',
  sameAs: [],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/site.webmanifest" />
        <meta name="theme-color" content="#2563eb" />
        <meta name="msapplication-TileColor" content="#2563eb" />
        <meta name="msapplication-config" content="/browserconfig.xml" />
      </head>
      <body className={inter.className}>
        <JsonLd data={webAppSchema} />
        <JsonLd data={orgSchema} />
        {children}
      </body>
    </html>
  );
}
