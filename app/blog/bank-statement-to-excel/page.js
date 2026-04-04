import Link from 'next/link';
import { FileSpreadsheet } from 'lucide-react';
import JsonLd from '@/components/JsonLd';
import Footer from '@/components/Footer';

export const metadata = {
  title: 'Convert Bank Statement PDF to Excel — Free Online Tool',
  description:
    'Convert any bank statement PDF to Excel in seconds. Extract ' +
    'transaction date, description, debit, credit, and balance columns automatically. Free with DocXL AI.',
  alternates: { canonical: 'https://docxl.ai/blog/bank-statement-to-excel' },
};

const articleSchema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'How to Convert a Bank Statement PDF to Excel Free',
  datePublished: '2025-07-01',
  dateModified: '2025-07-01',
  author: { '@type': 'Organization', name: 'DocXL AI', url: 'https://docxl.ai' },
  publisher: { '@type': 'Organization', name: 'DocXL AI', logo: { '@type': 'ImageObject', url: 'https://docxl.ai/logo.png' } },
};

export default function BankStatementToExcelArticle() {
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
          <p className="text-sm text-muted-foreground mb-4"><Link href="/blog" className="text-primary hover:underline">Blog</Link> / Bank Statement to Excel</p>
          <article className="prose prose-slate max-w-none">
            <h1 className="text-3xl sm:text-4xl font-bold mb-6">How to Convert a Bank Statement PDF to Excel Free</h1>
            <p className="text-lg text-muted-foreground mb-8">Whether you need bank data in Excel for budgeting, accounting, tax preparation, or expense tracking, manually typing transactions from a PDF bank statement is one of the most tedious data tasks. DocXL AI automates the entire process using GPT-4o AI.</p>

            <h2 className="text-2xl font-semibold mt-10 mb-4">Columns DocXL AI Extracts from Bank Statements</h2>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground mb-6">
              <li>Transaction Date</li>
              <li>Transaction Description / Narration</li>
              <li>Reference Number</li>
              <li>Debit Amount</li>
              <li>Credit Amount</li>
              <li>Running Balance</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-10 mb-4">Step-by-Step: Bank Statement PDF to Excel</h2>
            <ol className="list-decimal pl-6 space-y-2 text-muted-foreground mb-6">
              <li><strong>Upload your bank statement PDF</strong> to <Link href="/" className="text-primary underline">docxl.ai</Link>. You can also upload a screenshot or photo of a printed statement.</li>
              <li><strong>AI reads every transaction.</strong> GPT-4o identifies the table structure, parses dates, amounts, and descriptions, and outputs structured rows.</li>
              <li><strong>Download as Excel.</strong> Review the data, edit any cell if needed, then click "Download Excel" to get your .xlsx file.</li>
            </ol>

            <h2 className="text-2xl font-semibold mt-10 mb-4">Works With All Major Banks</h2>
            <p className="text-muted-foreground mb-4">DocXL AI reads any PDF format regardless of bank. Whether your statement is from HDFC, SBI, ICICI, Chase, Bank of America, Barclays, or any other bank — the AI adapts to the layout and extracts the data correctly. It even handles scanned statements where text is embedded as images.</p>

            <h2 className="text-2xl font-semibold mt-10 mb-4">What to Do After Converting</h2>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground mb-6">
              <li>Use Excel SUMIF formulas to calculate category totals</li>
              <li>Filter transactions by date range or amount</li>
              <li>Import the data into accounting software like Tally, QuickBooks, or Zoho Books</li>
              <li>Create pivot tables for monthly spending analysis</li>
            </ul>

            <div className="bg-primary/5 border border-primary/20 rounded-xl p-6 text-center mt-10">
              <p className="font-semibold text-lg mb-2">Convert your bank statement free</p>
              <p className="text-muted-foreground mb-4">5 free conversions, no credit card required.</p>
              <Link href="/" className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-6 py-3 text-sm font-medium hover:bg-primary/90">Convert your bank statement free \u2192</Link>
            </div>
          </article>
        </main>

        <Footer />
      </div>
    </>
  );
}
