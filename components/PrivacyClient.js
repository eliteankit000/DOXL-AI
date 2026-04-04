'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { FileSpreadsheet, ArrowUp, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';

export default function PrivacyClient() {
  const [showBackToTop, setShowBackToTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowBackToTop(window.scrollY > 400);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const sections = [
    { id: 'introduction', title: '1. Introduction' },
    { id: 'information-we-collect', title: '2. Information We Collect' },
    { id: 'how-we-use', title: '3. How We Use Your Information' },
    { id: 'document-handling', title: '4. Document and File Handling' },
    { id: 'data-sharing', title: '5. Data Sharing and Third Parties' },
    { id: 'cookies', title: '6. Cookies and Tracking' },
    { id: 'data-security', title: '7. Data Security' },
    { id: 'your-rights', title: '8. Your Rights' },
    { id: 'childrens-privacy', title: "9. Children's Privacy" },
    { id: 'data-retention', title: '10. Data Retention' },
    { id: 'international-transfers', title: '11. International Data Transfers' },
    { id: 'changes', title: '12. Changes to This Policy' },
    { id: 'contact-us', title: '13. Contact Us' },
  ];

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
            <Link href="/">
              <Button variant="outline" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 text-center">
          <h1 className="text-4xl font-bold text-foreground mb-3">Privacy Policy</h1>
          <p className="text-muted-foreground">Last updated: July 1, 2025</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
        {/* Table of Contents */}
        <div className="bg-white rounded-xl border p-6 mb-12">
          <h2 className="text-lg font-semibold mb-4">Table of Contents</h2>
          <nav className="space-y-2">
            {sections.map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className="block text-sm text-primary hover:text-primary/80 hover:underline transition-colors"
              >
                {section.title}
              </a>
            ))}
          </nav>
        </div>

        {/* Sections */}
        <div className="space-y-12 text-base leading-[1.8] text-foreground">
          {/* 1. Introduction */}
          <section id="introduction">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">1. Introduction</h2>
            <p className="mb-4">
              DocXL AI is a software-as-a-service platform operated from India that enables users to convert PDFs, images, invoices, bank statements, and other financial documents into structured, downloadable Excel data using artificial intelligence. This Privacy Policy describes how we collect, use, store, protect, and share your personal information when you access or use the DocXL AI platform, including our website, application, APIs, and any related services.
            </p>
            <p>
              This policy applies to all users of DocXL AI, including registered users, visitors, and anyone who interacts with our services. By accessing or using DocXL AI, you acknowledge that you have read and understood this Privacy Policy and consent to the collection and use of your information as described herein. If you do not agree with any part of this policy, please discontinue use of the service immediately.
            </p>
          </section>

          {/* 2. Information We Collect */}
          <section id="information-we-collect">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">2. Information We Collect</h2>
            <p className="mb-4">
              <strong>Account Information:</strong> When you create an account, we collect your name, email address, and password. Your password is cryptographically hashed using industry-standard algorithms and is never stored in plain text. We do not have access to your actual password.
            </p>
            <p className="mb-4">
              <strong>Uploaded Documents:</strong> When you use our service, you upload documents such as PDFs, images, bank statements, invoices, and receipts. These files are temporarily stored in encrypted cloud storage for the sole purpose of processing and data extraction.
            </p>
            <p className="mb-4">
              <strong>Extracted Data:</strong> The structured financial data derived from your uploaded documents, including transaction rows, amounts, dates, categories, and other fields identified by our AI, is stored in your account for you to review, edit, and download.
            </p>
            <p className="mb-4">
              <strong>Usage Data:</strong> We automatically collect certain technical information when you use our service, including pages visited, features used, timestamps of actions, your IP address, browser type and version, device type, operating system, and referring URLs. This data helps us improve the service and ensure security.
            </p>
            <p className="mb-4">
              <strong>Payment Information:</strong> If you subscribe to DocXL AI Pro, your payment is processed securely by Razorpay, our third-party payment processor. DocXL AI does not store, collect, or have access to your credit card numbers, CVV codes, bank account details, or any sensitive financial payment information. All payment data is handled exclusively by Razorpay in accordance with PCI-DSS compliance standards.
            </p>
            <p>
              <strong>Communications:</strong> If you contact our support team via email or through the contact form on our website, we collect your name, email address, the subject of your inquiry, and the content of your message to provide assistance and improve our service.
            </p>
          </section>

          {/* 3. How We Use Your Information */}
          <section id="how-we-use">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">3. How We Use Your Information</h2>
            <p className="mb-4">
              We use the information we collect to provide, maintain, and improve the DocXL AI document extraction service. Specifically, your data is used to authenticate your account and maintain session security, to process your uploaded documents and extract structured data using our AI models, and to deliver the extracted results to your dashboard for review and download.
            </p>
            <p className="mb-4">
              We process payment information through Razorpay to manage your subscription, process payments, and maintain billing records. Transactional emails, including receipt confirmations, processing notifications, and account-related communications, are sent to keep you informed about your account activity.
            </p>
            <p className="mb-4">
              To improve AI extraction accuracy, we may analyze anonymized and aggregated usage patterns. No individual documents are used for model training without your explicit, informed consent. We use technical data to detect and prevent fraud, abuse, unauthorized access, and other security threats to our platform and users.
            </p>
            <p>
              DocXL AI operates in compliance with applicable Indian laws, including the Information Technology Act 2000 and the Information Technology (Amendment) Act 2008, and we may use your information as necessary to fulfill our legal obligations under these and other applicable regulations.
            </p>
          </section>

          {/* 4. Document and File Handling */}
          <section id="document-handling">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">4. Document and File Handling</h2>
            <p className="mb-4">
              The security and privacy of your uploaded documents is of paramount importance to us. All uploaded files are stored in encrypted cloud storage powered by Supabase, which uses AWS S3-compatible infrastructure with encryption at rest. Files are transmitted over TLS-encrypted connections at all times.
            </p>
            <p className="mb-4">
              Uploaded files are automatically deleted from our servers within 48 hours of processing completion. This automated deletion ensures that your sensitive financial documents are not retained longer than necessary for service delivery.
            </p>
            <p className="mb-4">
              The extracted structured data (rows, tables, and summaries) derived from your documents is retained in your account indefinitely until you choose to delete it. You have full control over your extracted data and may delete any file and its associated extracted results at any time from your dashboard.
            </p>
            <p>
              DocXL AI employees do not manually read, review, or access your uploaded documents under any circumstances, except when explicitly required to resolve a technical support issue and only with your prior, express consent.
            </p>
          </section>

          {/* 5. Data Sharing and Third Parties */}
          <section id="data-sharing">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">5. Data Sharing and Third Parties</h2>
            <p className="mb-4">
              DocXL AI does not sell your personal data to third parties under any circumstances. We do not allow advertisers or marketing companies to target you based on the content of your uploaded documents or extracted data.
            </p>
            <p className="mb-4">
              We share data with the following service providers only to the extent strictly necessary to deliver our service:
            </p>
            <p className="mb-4">
              <strong>Supabase</strong> provides our database, authentication, and file storage infrastructure. Your account data, uploaded files, and extracted results are stored on Supabase's cloud infrastructure, which employs industry-standard security measures including encryption at rest and in transit.
            </p>
            <p className="mb-4">
              <strong>OpenAI</strong> powers our AI document processing capabilities. When you upload a document for extraction, the document image or text is sent to OpenAI's API for analysis. This interaction is governed by OpenAI's API data usage policy. Importantly, we use API access, which means your data is not used to train OpenAI's models.
            </p>
            <p className="mb-4">
              <strong>Razorpay</strong> processes all payment transactions for Pro subscriptions. Payment data shared with Razorpay is governed by Razorpay's own privacy policy and PCI-DSS compliance standards.
            </p>
            <p className="mb-4">
              <strong>Hosting Provider:</strong> Our application infrastructure is hosted on cloud platforms that maintain strict security and privacy standards.
            </p>
            <p className="mb-4">
              We may disclose your information if required to do so by Indian law, a court order, or a directive from a government authority with lawful jurisdiction. In the event that DocXL AI is acquired, merged with another entity, or undergoes a business transfer, your data may be transferred to the new entity under the same privacy commitments described in this policy.
            </p>
          </section>

          {/* 6. Cookies and Tracking */}
          <section id="cookies">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">6. Cookies and Tracking</h2>
            <p className="mb-4">
              DocXL AI uses essential cookies only. These are session authentication cookies that are strictly necessary for the login and authentication functionality of our platform to operate correctly. Without these cookies, you would not be able to maintain a logged-in session.
            </p>
            <p className="mb-4">
              We do not use advertising cookies, cross-site tracking pixels, third-party analytics services that create user profiles, or any other non-essential tracking technologies. Your browsing activity on DocXL AI is not shared with or visible to any advertising networks or data brokers.
            </p>
            <p>
              You may disable cookies in your browser settings, however please be aware that doing so will prevent you from logging into your DocXL AI account, as our authentication system relies on session cookies to function.
            </p>
          </section>

          {/* 7. Data Security */}
          <section id="data-security">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">7. Data Security</h2>
            <p className="mb-4">
              We take the security of your data seriously and implement multiple layers of protection. All data transmitted between your browser and our servers is encrypted using Transport Layer Security (TLS) 1.2 or higher, ensuring that your information cannot be intercepted during transit.
            </p>
            <p className="mb-4">
              Data stored at rest in our database and file storage systems is encrypted using AES-256 encryption, which is the industry standard for protecting sensitive information. Your account passwords are hashed using bcrypt, a deliberately slow hashing algorithm designed to resist brute-force attacks, and are never stored in plain text.
            </p>
            <p className="mb-4">
              Access to production databases and infrastructure is strictly restricted to authorized personnel only, who must authenticate using multi-factor authentication. We conduct periodic security reviews and promptly address any vulnerabilities identified.
            </p>
            <p>
              Despite these comprehensive measures, no system connected to the internet can be guaranteed to be 100% secure. We strongly encourage you to use a strong, unique password for your DocXL AI account and to avoid reusing passwords from other services.
            </p>
          </section>

          {/* 8. Your Rights */}
          <section id="your-rights">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">8. Your Rights</h2>
            <p className="mb-4">
              You have the right to access a complete copy of all personal data we hold about you. You may request this at any time by contacting us at the email address provided below.
            </p>
            <p className="mb-4">
              You have the right to request correction of any inaccurate or incomplete personal data we hold about you. If any information in your account is incorrect, we will update it promptly upon your request.
            </p>
            <p className="mb-4">
              You have the right to deletion of your account and all associated data, commonly known as the "right to be forgotten." Upon receiving a valid deletion request, we will permanently remove your account, uploaded files, extracted results, and personal information from our systems.
            </p>
            <p className="mb-4">
              You have the right to data portability. You may request your extracted data in JSON or CSV format, which you can download and transfer to another service.
            </p>
            <p className="mb-4">
              You have the right to withdraw your consent to our processing of your data at any time. You may exercise this right by discontinuing your use of the service and requesting account deletion.
            </p>
            <p>
              To exercise any of these rights, please email <a href="mailto:hello@docxlai.com" className="text-primary hover:underline">hello@docxlai.com</a> with the subject line &quot;Privacy Request &#8212; [Right Type]&quot; (e.g., &quot;Privacy Request &#8212; Deletion&quot;). We will respond to your request within 30 calendar days.
            </p>
          </section>

          {/* 9. Children's Privacy */}
          <section id="childrens-privacy">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">9. Children&apos;s Privacy</h2>
            <p className="mb-4">
              DocXL AI is not intended for use by children under the age of 13. We do not knowingly collect, solicit, or store personal information from children under 13 years of age.
            </p>
            <p>
              If you are a parent or guardian and believe that your child has provided personal information to DocXL AI without your consent, please contact us immediately at <a href="mailto:hello@docxlai.com" className="text-primary hover:underline">hello@docxlai.com</a>. We will take prompt steps to delete the information from our systems.
            </p>
          </section>

          {/* 10. Data Retention */}
          <section id="data-retention">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">10. Data Retention</h2>
            <p className="mb-4">
              <strong>Account data</strong> (name, email, preferences) is retained for the duration of your account plus 90 days following account deletion, after which it is permanently purged from all systems.
            </p>
            <p className="mb-4">
              <strong>Uploaded files</strong> (PDFs, images, documents) are automatically deleted within 48 hours of processing completion. Files associated with failed processing are also deleted within this timeframe.
            </p>
            <p className="mb-4">
              <strong>Extracted data</strong> (structured rows, tables, summaries) is retained in your account until you explicitly delete it or close your account.
            </p>
            <p className="mb-4">
              <strong>Payment records</strong> are retained for 7 years as required by Indian GST regulations and applicable accounting laws to maintain accurate financial records.
            </p>
            <p>
              <strong>Usage logs</strong> (access logs, action logs) are retained for 12 months for security monitoring, fraud prevention, and service improvement purposes, after which they are automatically purged.
            </p>
          </section>

          {/* 11. International Data Transfers */}
          <section id="international-transfers">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">11. International Data Transfers</h2>
            <p className="mb-4">
              DocXL AI is operated from India. However, some of our third-party service providers, including Supabase and OpenAI, may process your data on servers located outside of India, including in the United States and other jurisdictions.
            </p>
            <p>
              By using DocXL AI, you consent to the transfer of your information to these jurisdictions. We ensure that all third-party processors with whom we share data maintain adequate data protection standards consistent with or exceeding the requirements of applicable Indian data protection laws.
            </p>
          </section>

          {/* 12. Changes to This Policy */}
          <section id="changes">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">12. Changes to This Policy</h2>
            <p className="mb-4">
              We may update this Privacy Policy from time to time to reflect changes in our practices, technology, legal requirements, or other factors. When we make material changes to this policy, we will notify registered users via email and/or display a prominent banner within the application.
            </p>
            <p>
              Your continued use of DocXL AI after any changes to this policy constitutes your acceptance of the updated terms. The "Last updated" date at the top of this page will always reflect the date of the most recent revision. We encourage you to review this policy periodically.
            </p>
          </section>

          {/* 13. Contact Us */}
          <section id="contact-us">
            <h2 className="text-2xl font-bold mb-4 pl-4 border-l-4 border-primary">13. Contact Us</h2>
            <p className="mb-4">
              If you have any questions, concerns, or requests regarding this Privacy Policy or your personal data, please contact us:
            </p>
            <ul className="list-none space-y-2 mb-4">
              <li><strong>Privacy inquiries:</strong> <a href="mailto:hello@docxlai.com" className="text-primary hover:underline">hello@docxlai.com</a></li>
              <li><strong>General support:</strong> <a href="mailto:hello@docxlai.com" className="text-primary hover:underline">hello@docxlai.com</a></li>
              <li><strong>Mailing address:</strong> DocXL AI, India</li>
              <li><strong>Response time:</strong> Within 2 business days</li>
            </ul>
          </section>
        </div>
      </div>

      {/* Back to Top Button */}
      {showBackToTop && (
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="fixed bottom-6 right-6 z-50 w-10 h-10 bg-primary text-white rounded-full shadow-lg flex items-center justify-center hover:bg-primary/90 transition-all"
          aria-label="Back to top"
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      )}

      <Footer />
    </div>
  );
}
