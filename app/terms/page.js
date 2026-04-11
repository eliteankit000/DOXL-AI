import Link from 'next/link';
import { FileSpreadsheet, ArrowLeft } from 'lucide-react';
import Footer from '@/components/Footer';

export const metadata = {
  title: 'Terms of Service — Love2Excel',
  description: 'Terms of Service for Love2Excel PDF to Excel converter.',
  alternates: { canonical: 'https://love2excel.ai/terms' },
  robots: { index: true, follow: false },
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
              <span className="text-xl font-bold text-foreground">Love2Excel</span>
            </Link>
            <Link href="/" className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2">
              <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
            </Link>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 lg:py-20">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-3">Terms of Service</h1>
          <p className="text-muted-foreground">Last updated: January 2025</p>
        </div>

        <div className="prose prose-blue max-w-none space-y-8 text-foreground">
          
          {/* 1. Agreement */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">1. Agreement to Terms</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              By accessing or using Love2Excel ("Service", "Platform", "we", "us"), you agree to be bound by these Terms of Service. If you disagree with any part of these terms, you may not access the Service.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              We reserve the right to update these terms at any time. Continued use of the Service after changes constitutes acceptance of the revised terms.
            </p>
          </section>

          {/* 2. Service Description */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">2. Service Description</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              Love2Excel is a SaaS platform that uses artificial intelligence to extract structured data from documents (PDFs, images, invoices, bank statements, receipts) and convert them into editable Excel spreadsheets.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              The Service is provided "as is" and "as available" without warranties of any kind, either express or implied. We do not guarantee that the Service will be uninterrupted, secure, or error-free.
            </p>
          </section>

          {/* 3. Eligibility */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">3. Eligibility</h2>
            <p className="text-muted-foreground leading-relaxed">
              You must be at least 18 years old to use this Service. By using Love2Excel, you represent and warrant that you meet this age requirement and have the legal capacity to enter into these Terms.
            </p>
          </section>

          {/* 4. User Accounts */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">4. User Accounts</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p>You are responsible for:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Maintaining the confidentiality of your account credentials</li>
                <li>All activities that occur under your account</li>
                <li>Notifying us immediately of any unauthorized access</li>
                <li>Ensuring the accuracy of information you provide during registration</li>
              </ul>
              <p className="mt-3">
                We reserve the right to suspend or terminate accounts that violate these Terms or engage in fraudulent, abusive, or illegal activity.
              </p>
            </div>
          </section>

          {/* 5. Acceptable Use */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">5. Acceptable Use Policy</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p>You agree NOT to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Upload documents containing illegal, harmful, or offensive content</li>
                <li>Attempt to reverse engineer, decompile, or hack the Service</li>
                <li>Use automated tools (bots, scrapers) to access the Service without permission</li>
                <li>Resell, redistribute, or commercially exploit the Service without authorization</li>
                <li>Upload malware, viruses, or any malicious code</li>
                <li>Violate any applicable laws or regulations</li>
                <li>Infringe on intellectual property rights of others</li>
              </ul>
              <p className="mt-3">
                Violation of this policy may result in immediate account termination and legal action.
              </p>
            </div>
          </section>

          {/* 6. Billing and Payments */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">6. Billing and Payments</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p><strong>Free Plan:</strong> Includes 5 credits. No credit card required.</p>
              <p><strong>Pro Plan:</strong> ₹699 INR (India) or $9 USD (Global) for 300 credits.</p>
              
              <p className="mt-4">Payment terms:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>All payments are processed securely through Razorpay (India) or Paddle (Global)</li>
                <li>Prices are subject to change with 30 days notice</li>
                <li>You authorize us to charge your payment method for all fees incurred</li>
                <li>Failed payments may result in service suspension</li>
              </ul>

              <p className="mt-4"><strong>No Refunds:</strong> All sales are final. We do not offer refunds or credits for partial month usage, upgrade/downgrade refunds, or unused credits. Please review your purchase carefully before completing payment.</p>
            </div>
          </section>

          {/* 7. Credits System */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">7. Credits and Usage</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p>Each document processing operation consumes 1 credit. Credits are:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Non-refundable and non-transferable</li>
                <li>Valid for the lifetime of your account (Free Plan) or reset monthly (Pro Plan)</li>
                <li>Deducted before processing begins</li>
                <li>Refunded only in case of processing timeouts or technical failures on our end</li>
              </ul>
              <p className="mt-3">
                Pro plan credits reset to 300 on the 1st of each month. Unused credits do not roll over.
              </p>
            </div>
          </section>

          {/* 8. Data Ownership and Privacy */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">8. Data Ownership and Privacy</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p><strong>You retain full ownership</strong> of all documents and data you upload to Love2Excel.</p>
              
              <p>We commit to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Automatically deleting uploaded files within 48 hours</li>
                <li>Encrypting all data in transit (TLS) and at rest (AES-256)</li>
                <li>Never selling, sharing, or using your data for training AI models</li>
                <li>Processing data solely for the purpose of providing the Service</li>
              </ul>

              <p className="mt-3">
                For full details, please review our <Link href="/privacy" className="text-primary hover:underline">Privacy Policy</Link>.
              </p>
            </div>
          </section>

          {/* 9. Intellectual Property */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">9. Intellectual Property Rights</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p>
                The Service, including all software, algorithms, design, text, graphics, and logos, is owned by Love2Excel and is protected by copyright, trademark, and other intellectual property laws.
              </p>
              <p>
                You are granted a limited, non-exclusive, non-transferable license to use the Service for your personal or business purposes. This license does not permit you to copy, modify, distribute, sell, or reverse engineer any part of the Service.
              </p>
            </div>
          </section>

          {/* 10. Limitation of Liability */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">10. Limitation of Liability</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p>
                <strong>To the maximum extent permitted by law:</strong>
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Love2Excel and its affiliates shall not be liable for any indirect, incidental, special, consequential, or punitive damages</li>
                <li>Our total liability shall not exceed the amount you paid us in the last 12 months</li>
                <li>We are not responsible for errors in AI-extracted data. Users must verify all extracted information</li>
                <li>We are not liable for data loss, security breaches caused by third parties, or service interruptions beyond our control</li>
              </ul>
              <p className="mt-3">
                Some jurisdictions do not allow the exclusion of certain warranties or limitations of liability, so some of the above may not apply to you.
              </p>
            </div>
          </section>

          {/* 11. Termination */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">11. Account Termination</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p>You may terminate your account at any time from your dashboard settings.</p>
              
              <p>We may suspend or terminate your account immediately if:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>You violate these Terms of Service</li>
                <li>Your payment method fails or your account becomes delinquent</li>
                <li>We are required to do so by law</li>
                <li>We cease operations or discontinue the Service</li>
              </ul>

              <p className="mt-3">
                Upon termination, your right to use the Service will immediately cease. We may delete your data within 30 days of termination. No refunds will be provided for terminated accounts.
              </p>
            </div>
          </section>

          {/* 12. Governing Law */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">12. Governing Law and Disputes</h2>
            <div className="space-y-3 text-muted-foreground leading-relaxed">
              <p>
                These Terms shall be governed by and construed in accordance with the laws of India, without regard to its conflict of law provisions.
              </p>
              <p>
                Any disputes arising out of or relating to these Terms or the Service shall be resolved through binding arbitration in accordance with the rules of the Indian Arbitration and Conciliation Act, 1996.
              </p>
              <p>
                You agree to resolve disputes individually and waive any right to participate in class-action lawsuits or class-wide arbitration.
              </p>
            </div>
          </section>

          {/* 13. Changes to Service */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">13. Changes to Service and Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              We reserve the right to modify, suspend, or discontinue any part of the Service at any time with or without notice. We will notify users of material changes to these Terms via email or through the Service. Your continued use after changes indicates acceptance of the revised Terms.
            </p>
          </section>

          {/* 14. Contact */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">14. Contact Information</h2>
            <div className="text-muted-foreground leading-relaxed space-y-2">
              <p>If you have questions about these Terms, please contact us:</p>
              <p>
                <strong>Email:</strong> <a href="mailto:hello@love2excel.com" className="text-primary hover:underline">hello@love2excel.com</a>
              </p>
              <p>
                <strong>Contact Form:</strong> <Link href="/contact" className="text-primary hover:underline">love2excel.ai/contact</Link>
              </p>
            </div>
          </section>

          {/* Acceptance */}
          <section className="border-t pt-8 mt-12">
            <p className="text-sm text-muted-foreground italic">
              By creating an account and using Love2Excel, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
            </p>
          </section>

        </div>
      </div>

      <Footer />
    </div>
  );
}
