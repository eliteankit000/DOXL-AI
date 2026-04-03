'use client';
import Link from 'next/link';
import { FileSpreadsheet, Mail, Twitter, Linkedin, Github } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-white border-t">
      {/* Top Section - 4 Column Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Column 1 - Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-foreground">DocXL AI</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Transform documents into structured data with AI. Fast, secure, and accurate.
            </p>
            <p className="text-xs text-muted-foreground">Made with &#9829; in India</p>
          </div>

          {/* Column 2 - Product */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Product</h4>
            <ul className="space-y-3">
              <li><Link href="/" className="text-sm text-muted-foreground hover:text-primary transition-colors">Dashboard</Link></li>
              <li><Link href="/" className="text-sm text-muted-foreground hover:text-primary transition-colors">Upload Document</Link></li>
              <li><Link href="/" className="text-sm text-muted-foreground hover:text-primary transition-colors">Pricing</Link></li>
              <li><Link href="/#how-it-works" className="text-sm text-muted-foreground hover:text-primary transition-colors">How it works</Link></li>
            </ul>
          </div>

          {/* Column 3 - Legal & Support */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Legal & Support</h4>
            <ul className="space-y-3">
              <li><Link href="/privacy" className="text-sm text-muted-foreground hover:text-primary transition-colors">Privacy Policy</Link></li>
              <li><Link href="/contact" className="text-sm text-muted-foreground hover:text-primary transition-colors">Contact Us</Link></li>
              <li>
                <span className="text-sm text-muted-foreground flex items-center gap-2">
                  Terms of Service
                  <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded-full font-medium">Coming Soon</span>
                </span>
              </li>
              <li><span className="text-sm text-muted-foreground">7-day money back guarantee</span></li>
            </ul>
          </div>

          {/* Column 4 - Connect */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Connect</h4>
            <ul className="space-y-3">
              <li>
                <a href="mailto:support@docxl.ai" className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2">
                  <Mail className="w-4 h-4" /> support@docxl.ai
                </a>
              </li>
              <li>
                <a href="https://twitter.com/docxlai" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2">
                  <Twitter className="w-4 h-4" /> @docxlai
                </a>
              </li>
              <li>
                <a href="https://linkedin.com/company/docxlai" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2">
                  <Linkedin className="w-4 h-4" /> DocXL AI
                </a>
              </li>
              <li>
                <a href="https://github.com/docxlai" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2">
                  <Github className="w-4 h-4" /> GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Middle Section - Divider + Trust Badges */}
      <div className="border-t">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-3">
            <p className="text-xs text-muted-foreground text-center md:text-left">
              Secured by Supabase &middot; Powered by GPT-4o &middot; Payments by Razorpay
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <span className="inline-flex items-center text-[11px] bg-green-50 text-green-700 border border-green-200 px-2.5 py-1 rounded-full font-medium">
                &#128274; 256-bit Encryption
              </span>
              <span className="inline-flex items-center text-[11px] bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-full font-medium">
                &#10003; GDPR Ready
              </span>
              <span className="inline-flex items-center text-[11px] bg-orange-50 text-orange-700 border border-orange-200 px-2.5 py-1 rounded-full font-medium">
                &#127470;&#127475; Data processed in compliance with IT Act 2000
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section - Copyright */}
      <div className="bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-3">
            <p className="text-xs text-gray-400 text-center md:text-left max-w-3xl">
              &copy; 2025 DocXL AI. All rights reserved. Unauthorized reproduction, distribution, or use of any content, code, design, or data extraction methodology from this platform is strictly prohibited and may result in legal action under applicable Indian and international intellectual property laws.
            </p>
            <div className="flex items-center gap-4 flex-shrink-0">
              <Link href="/privacy" className="text-xs text-gray-400 hover:text-white transition-colors">Privacy Policy</Link>
              <Link href="/contact" className="text-xs text-gray-400 hover:text-white transition-colors">Contact</Link>
              <span className="text-[10px] bg-gray-800 text-gray-500 px-2 py-0.5 rounded font-mono">v1.0.0</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
