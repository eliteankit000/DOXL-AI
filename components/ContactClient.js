'use client';
import { useState } from 'react';
import Link from 'next/link';
import { FileSpreadsheet, ArrowLeft, MessageCircle, CreditCard, Shield, Check, Loader2, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import Footer from '@/components/Footer';

const contactCards = [
  {
    icon: MessageCircle,
    title: 'General Support',
    desc: 'Questions about your account, uploads, or extractions',
    email: 'hello@love2excel.com',
    badge: 'Avg response: 2 hours',
    color: 'bg-blue-50 text-blue-600',
  },
  {
    icon: CreditCard,
    title: 'Billing & Payments',
    desc: 'Subscription issues, payment failures, refund requests',
    email: 'hello@love2excel.com',
    badge: 'Avg response: 4 hours',
    color: 'bg-green-50 text-green-600',
  },
  {
    icon: Shield,
    title: 'Privacy & Data',
    desc: 'Data deletion requests, privacy concerns, compliance',
    email: 'hello@love2excel.com',
    badge: 'Avg response: 1 business day',
    color: 'bg-purple-50 text-purple-600',
  },
];

const faqItems = [
  {
    q: 'How do I delete my account and all my data?',
    a: 'You can delete your account from your dashboard settings. All your data including uploaded files, extracted results, and personal information will be permanently deleted within 24 hours. For immediate deletion, email hello@love2excel.com with subject "Account Deletion Request".',
  },
  {
    q: 'Why did my extraction fail?',
    a: 'Common reasons: the document is blurry or low resolution (try scanning at 300 DPI+), the PDF is password-protected (remove the password first), the file contains scanned text at an angle (straighten it), or the document is in an unsupported language. Contact hello@love2excel.com with your upload ID if the issue persists.',
  },
  {
    q: 'Is my financial data safe?',
    a: 'Yes. Files are encrypted in transit (TLS) and at rest (AES-256). Uploaded documents are automatically deleted within 48 hours. We never sell or share your data. Read our full Privacy Policy for details.',
  },
  {
    q: 'What is your refund policy?',
    a: 'All sales are final. We do not offer refunds for Pro plan purchases, partial month usage, or unused credits. Please review your purchase carefully before completing payment. For exceptional circumstances, contact hello@love2excel.com.',
  },
  {
    q: 'Do you support languages other than English?',
    a: 'Our AI can extract data from documents in most languages including Hindi, Tamil, Telugu, Bengali, Marathi, and other major Indian languages, as well as Spanish, French, German, and more. Results may vary by language complexity.',
  },
  {
    q: 'How many pages can one PDF have?',
    a: 'Free plan: up to 10 pages per PDF. Pro plan: up to 50 pages per PDF. For larger documents, split them into multiple files before uploading.',
  },
];

const subjectOptions = [
  'General Question',
  'Bug Report',
  'Feature Request',
  'Billing Issue',
  'Data/Privacy Request',
  'Partnership',
  'Other',
];

export default function ContactClient() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });
  const [agreed, setAgreed] = useState(false);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const validateForm = () => {
    const newErrors = {};
    if (!form.name.trim()) newErrors.name = 'Name is required';
    if (!form.email.trim()) newErrors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) newErrors.email = 'Invalid email address';
    if (!form.subject) newErrors.subject = 'Please select a subject';
    if (!form.message.trim()) newErrors.message = 'Message is required';
    else if (form.message.trim().length < 20) newErrors.message = 'Message must be at least 20 characters';
    if (!agreed) newErrors.agreed = 'You must agree to the Privacy Policy';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setSubmitting(true);
    
    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name,
          email: form.email,
          message: `[${form.subject}] ${form.message}`,
        }),
      });
      
      if (!response.ok) throw new Error('Form submission failed');
      
      setSubmitted(true);
    } catch (error) {
      console.error('Form submission error:', error);
      setErrors({ submit: 'Failed to send your message. Please email us directly at hello@love2excel.com' });
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setForm({ name: '', email: '', subject: '', message: '' });
    setAgreed(false);
    setErrors({});
    setSubmitted(false);
  };

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: undefined }));
  };

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
            <Link href="/">
              <Button variant="outline" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <div className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 text-center">
          <h1 className="text-4xl font-bold text-foreground mb-3">Get in Touch</h1>
          <p className="text-muted-foreground text-lg">
            We typically respond within 2 business hours during IST business hours (Mon&#8211;Fri, 9am&#8211;6pm)
          </p>
          <p className="text-sm text-muted-foreground mt-3">
            <Link href="/pricing" className="text-primary hover:underline">See our pricing plans</Link>
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
        {/* Contact Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {contactCards.map((card, i) => (
            <Card key={i} className="border shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="pt-6 space-y-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${card.color}`}>
                  <card.icon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-1">{card.title}</h3>
                  <p className="text-sm text-muted-foreground mb-3">{card.desc}</p>
                </div>
                <a
                  href={`mailto:${card.email}`}
                  className="inline-block text-sm text-primary hover:underline font-medium"
                >
                  {card.email}
                </a>
                <div>
                  <Badge variant="secondary" className="text-xs">{card.badge}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Contact Form */}
        <div className="max-w-2xl mx-auto mb-16">
          <h2 className="text-2xl font-bold text-center mb-8">Send Us a Message</h2>
          <Card className="border shadow-sm">
            <CardContent className="pt-6">
              {submitted ? (
                <div className="py-12 text-center space-y-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                    <Check className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground">Your message has been sent!</h3>
                  <p className="text-muted-foreground">
                    We&apos;ll reply within 24 hours to <span className="font-medium text-foreground">{form.email}</span>.
                  </p>
                  <Button variant="outline" onClick={resetForm}>Send another message</Button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Name <span className="text-destructive">*</span></Label>
                      <Input
                        id="name"
                        placeholder="Your name"
                        value={form.name}
                        onChange={e => handleChange('name', e.target.value)}
                      />
                      {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email <span className="text-destructive">*</span></Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="you@example.com"
                        value={form.email}
                        onChange={e => handleChange('email', e.target.value)}
                      />
                      {errors.email && <p className="text-xs text-destructive">{errors.email}</p>}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="subject">Subject <span className="text-destructive">*</span></Label>
                    <select
                      id="subject"
                      className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      value={form.subject}
                      onChange={e => handleChange('subject', e.target.value)}
                    >
                      <option value="">Select a subject...</option>
                      {subjectOptions.map(opt => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                    {errors.subject && <p className="text-xs text-destructive">{errors.subject}</p>}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="message">Message <span className="text-destructive">*</span></Label>
                    <textarea
                      id="message"
                      className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
                      placeholder="Describe your question, issue, or feedback in detail..."
                      rows={5}
                      value={form.message}
                      onChange={e => handleChange('message', e.target.value)}
                      maxLength={2000}
                    />
                    <div className="flex justify-between">
                      {errors.message ? (
                        <p className="text-xs text-destructive">{errors.message}</p>
                      ) : <span />}
                      <p className="text-xs text-muted-foreground">{form.message.length}/2000</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      id="agree"
                      checked={agreed}
                      onChange={e => { setAgreed(e.target.checked); if (errors.agreed) setErrors(prev => ({ ...prev, agreed: undefined })); }}
                      className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <Label htmlFor="agree" className="text-sm font-normal text-muted-foreground">
                      I agree to the <Link href="/privacy" className="text-primary hover:underline">Privacy Policy</Link>
                    </Label>
                  </div>
                  {errors.agreed && <p className="text-xs text-destructive">{errors.agreed}</p>}
                  <Button type="submit" className="w-full" disabled={submitting}>
                    {submitting ? (
                      <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Sending...</>
                    ) : (
                      <><Send className="w-4 h-4 mr-2" /> Send Message</>
                    )}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </div>

        {/* FAQ Accordion */}
        <div className="max-w-2xl mx-auto mb-16">
          <h2 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h2>
          <Accordion type="single" collapsible className="w-full">
            {faqItems.map((item, i) => (
              <AccordionItem key={i} value={`faq-${i}`}>
                <AccordionTrigger className="text-left font-medium">{item.q}</AccordionTrigger>
                <AccordionContent className="text-muted-foreground leading-relaxed">{item.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>

      <Footer />
    </div>
  );
}
