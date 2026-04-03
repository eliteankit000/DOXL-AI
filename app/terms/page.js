import Link from 'next/link';
import { FileSpreadsheet, ArrowLeft } from 'lucide-react';
import Footer from '@/components/Footer';

export const metadata = {
  title: 'Terms of Service - DocXL AI',
  description: 'Terms of Service for DocXL AI document extraction platform',
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-foreground">DocXL AI</span>
            </Link>
            <Link href="/" className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2">
              <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
            </Link>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-20">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-3">Terms of Service</h1>
          <span className="inline-block bg-orange-100 text-orange-700 text-sm font-medium px-3 py-1 rounded-full">Coming Soon</span>
        </div>

        <div className="bg-white rounded-xl border shadow-sm p-8 text-center space-y-6">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto">
            <FileSpreadsheet className="w-8 h-8 text-primary" />
          </div>
          <p className="text-muted-foreground leading-relaxed max-w-lg mx-auto">
            We are currently drafting our full Terms of Service. In the meantime, by using DocXL AI you agree to use the service lawfully and in accordance with our Privacy Policy.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/privacy" className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2">
              Read Privacy Policy
            </Link>
            <Link href="/contact" className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2">
              Contact Us
            </Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
