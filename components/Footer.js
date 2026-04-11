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
            <Link href="/" className="flex items-center gap-2" aria-label="Love2Excel home">
              <img src="/logo.png" alt="Love2Excel" className="h-8 w-auto max-w-[160px]" />
            </Link>
            <p className="text-sm text-muted-foreground leading-relaxed">
              AI-powered PDF to Excel converter. Fast, secure, and accurate.
            </p>
            <p className="text-xs text-muted-foreground">Made with &#9829; in India</p>
          </div>

          {/* Column 2 - Product */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Product</h4>
            <ul className="space-y-3">
              <li><Link href="/" className="text-sm text-muted-foreground hover:text-primary transition-colors">PDF to Excel Converter</Link></li>
              <li><Link href="/pricing" className="text-sm text-muted-foreground hover:text-primary transition-colors">Pricing</Link></li>
              <li><Link href="/blog" className="text-sm text-muted-foreground hover:text-primary transition-colors">Blog</Link></li>
              <li><Link href="/#how-it-works" className="text-sm text-muted-foreground hover:text-primary transition-colors">How it works</Link></li>
            </ul>
          </div>

          {/* Column 3 - Legal & Support */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Legal & Support</h4>
            <ul className="space-y-3">
              <li><Link href="/terms" className="text-sm text-muted-foreground hover:text-primary transition-colors">Terms of Service</Link></li>
              <li><Link href="/privacy" className="text-sm text-muted-foreground hover:text-primary transition-colors">Privacy Policy</Link></li>
              <li><Link href="/contact" className="text-sm text-muted-foreground hover:text-primary transition-colors">Contact Support</Link></li>
            </ul>
          </div>

          {/* Column 4 - Connect */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Connect</h4>
            <ul className="space-y-3">
              <li>
                <address className="not-italic">
                  <a href="mailto:hello@love2excel.com" className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2">
                    <Mail className="w-4 h-4" /> hello@love2excel.com
                  </a>
                </address>
              </li>
              <li>
                <a href="https://twitter.com/love2excelai" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2">
                  <Twitter className="w-4 h-4" /> @love2excelai
                </a>
              </li>
              <li>
                <a href="https://linkedin.com/company/love2excelai" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-2">
                  <Linkedin className="w-4 h-4" /> Love2Excel
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Middle Section - Divider + Trust Badges */}
      <div className="border-t">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
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

      {/* Bottom Section - Copyright */}
      <div className="bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-3">
            <p className="text-xs text-gray-400 text-center md:text-left">
              &copy; 2025 Love2Excel. All rights reserved.
            </p>
            <div className="flex items-center gap-4 flex-shrink-0">
              <Link href="/privacy" className="text-xs text-gray-400 hover:text-white transition-colors">Privacy Policy</Link>
              <Link href="/terms" className="text-xs text-gray-400 hover:text-white transition-colors">Terms of Service</Link>
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
