import Link from 'next/link';
import { FileSpreadsheet, ArrowRight } from 'lucide-react';
import Footer from '@/components/Footer';

export const metadata = {
  title: 'Blog — PDF to Excel Tips & Tutorials | Love2Excel',
  description:
    'Learn how to convert PDFs, invoices, and bank statements to Excel. ' +
    'Tips, tutorials, and guides from the Love2Excel team.',
  alternates: { canonical: 'https://love2excel.ai/blog' },
};

const posts = [
  {
    slug: '/blog/convert-pdf-to-excel',
    title: 'How to Convert PDF to Excel (Free, Online, in Seconds)',
    excerpt: 'Step-by-step guide to converting any PDF to Excel online for free. Works with invoices, bank statements, and scanned documents.',
    date: '2025-07-01',
  },
  {
    slug: '/blog/invoice-to-excel',
    title: 'How to Convert Invoices to Excel Automatically',
    excerpt: 'Stop manually entering invoice data into Excel. Use AI to extract vendor, date, line items, and totals from any invoice PDF.',
    date: '2025-07-01',
  },
  {
    slug: '/blog/bank-statement-to-excel',
    title: 'Convert Bank Statement PDF to Excel — Free Online Tool',
    excerpt: 'Convert any bank statement PDF to Excel in seconds. Extract transaction date, description, debit, credit, and balance columns.',
    date: '2025-07-01',
  },
];

export default function BlogPage() {
  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center gap-2" aria-label="Love2Excel home">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-foreground">Love2Excel</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground hidden sm:inline">Pricing</Link>
              <Link href="/contact" className="text-sm text-muted-foreground hover:text-foreground hidden sm:inline">Contact</Link>
              <Link href="/" className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium shadow hover:bg-primary/90">Get Started</Link>
            </div>
          </div>
        </div>
      </nav>

      <main role="main" className="max-w-4xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold mb-4">Blog</h1>
        <p className="text-muted-foreground mb-12">Tips, tutorials, and guides for converting documents to Excel using AI.</p>
        <div className="grid gap-8">
          {posts.map(post => (
            <Link key={post.slug} href={post.slug} className="group block border rounded-xl p-6 hover:shadow-lg transition-shadow">
              <p className="text-xs text-muted-foreground mb-2">{new Date(post.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
              <h2 className="text-xl font-semibold group-hover:text-primary transition-colors mb-2">{post.title}</h2>
              <p className="text-muted-foreground text-sm mb-3">{post.excerpt}</p>
              <span className="text-primary text-sm font-medium flex items-center gap-1">Read more <ArrowRight className="w-4 h-4" /></span>
            </Link>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  );
}
