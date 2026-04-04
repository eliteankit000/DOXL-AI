import Link from 'next/link';
import { FileSpreadsheet } from 'lucide-react';
import JsonLd from '@/components/JsonLd';
import Footer from '@/components/Footer';

export const metadata = {
  title: 'How to Convert Invoices to Excel Automatically — DocXL AI',
  description:
    'Stop manually entering invoice data into Excel. Use AI to extract ' +
    'vendor, date, line items, tax, and totals from any invoice PDF into Excel in seconds.',
  alternates: { canonical: 'https://docxl.ai/blog/invoice-to-excel' },
};

const articleSchema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'How to Convert Invoice PDFs to Excel Automatically Using AI',
  datePublished: '2025-07-01',
  dateModified: '2025-07-01',
  author: { '@type': 'Organization', name: 'DocXL AI', url: 'https://docxl.ai' },
  publisher: { '@type': 'Organization', name: 'DocXL AI', logo: { '@type': 'ImageObject', url: 'https://docxl.ai/logo.png' } },
};

export default function InvoiceToExcelArticle() {
  return (
    <>
      <JsonLd data={articleSchema} />
      <div className="min-h-screen bg-background">
        <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <Link href="/" className="flex items-center gap-2"><div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center"><FileSpreadsheet className="w-5 h-5 text-white" /></div><span className="text-xl font-bold">DocXL AI</span></Link>
              <div className="flex items-center gap-4">
                <Link href="/blog" className="text-sm text-muted-foreground hover:text-foreground">Blog</Link>
                <Link href="/" className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium shadow hover:bg-primary/90">Try Free</Link>
              </div>
            </div>
          </div>
        </nav>

        <main role="main" className="max-w-3xl mx-auto px-4 py-16">
          <p className="text-sm text-muted-foreground mb-4"><Link href="/blog" className="text-primary hover:underline">Blog</Link> / Invoice to Excel</p>
          <article className="prose prose-slate max-w-none">
            <h1 className="text-3xl sm:text-4xl font-bold mb-6">How to Convert Invoice PDFs to Excel Automatically Using AI</h1>
            <p className="text-lg text-muted-foreground mb-8">Manually typing invoice data into Excel is tedious, error-prone, and wastes hours every week. Whether you are an accountant processing vendor invoices or a small business owner tracking expenses, there is a faster way. DocXL AI uses GPT-4o to extract every field from your invoice PDFs into structured Excel rows in seconds.</p>

            <h2 className="text-2xl font-semibold mt-10 mb-4">What Data DocXL AI Extracts from Invoices</h2>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground mb-6">
              <li>Invoice number and date</li>
              <li>Vendor / supplier name and address</li>
              <li>Line items with descriptions</li>
              <li>Quantities and unit prices</li>
              <li>Subtotal, tax / GST amounts, and total</li>
              <li>Payment terms and due dates</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-10 mb-4">How to Convert an Invoice to Excel Step by Step</h2>
            <ol className="list-decimal pl-6 space-y-2 text-muted-foreground mb-6">
              <li><strong>Upload your invoice PDF or image</strong> to <Link href="/" className="text-primary underline">docxl.ai</Link>. Drag and drop or click to browse. JPG and PNG receipt photos work too.</li>
              <li><strong>AI processes your invoice.</strong> GPT-4o reads every field, identifies line items, calculates totals, and structures everything into rows and columns.</li>
              <li><strong>Download as Excel.</strong> Review the extracted data in an editable table, make any corrections, then download as .xlsx.</li>
            </ol>

            <h2 className="text-2xl font-semibold mt-10 mb-4">Why AI Invoice Extraction Beats Manual Entry</h2>
            <p className="text-muted-foreground mb-4"><strong>Speed:</strong> Convert a 5-page invoice in under 30 seconds instead of 15 minutes of manual typing. <strong>Accuracy:</strong> GPT-4o understands invoice layouts, so it correctly maps line items even when formatting varies between vendors. <strong>No typos:</strong> Eliminate human data entry errors. <strong>Any format:</strong> Works with invoices from any vendor, any layout, any country.</p>

            <h2 className="text-2xl font-semibold mt-10 mb-4">Supported Invoice Formats</h2>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground mb-6">
              <li>PDF invoices (text-based and scanned)</li>
              <li>Scanned invoice images (JPG, PNG)</li>
              <li>Multi-page invoice PDFs (up to 6 pages per conversion)</li>
            </ul>

            <div className="bg-primary/5 border border-primary/20 rounded-xl p-6 text-center mt-10">
              <p className="font-semibold text-lg mb-2">Try free invoice to Excel conversion</p>
              <p className="text-muted-foreground mb-4">5 free conversions, no credit card required.</p>
              <Link href="/" className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-6 py-3 text-sm font-medium hover:bg-primary/90">Try free invoice to Excel conversion \u2192</Link>
            </div>
          </article>
        </main>

        <Footer />
      </div>
    </>
  );
}
