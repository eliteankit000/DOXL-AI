'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { FileSpreadsheet, Check, X } from 'lucide-react';

export default function PricingContent() {
  const [isIndian, setIsIndian] = useState(false);

  useEffect(() => {
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
      const lang = navigator.language || '';
      if (tz.startsWith('Asia/Kolkata') || tz.startsWith('Asia/Calcutta') || lang.startsWith('hi') || lang === 'en-IN') {
        setIsIndian(true);
      }
    } catch (e) {}
  }, []);

  const proPrice = isIndian ? '₹699' : '$9';
  const proPriceSuffix = '/month';

  const features = [
    { feature: 'Monthly conversions', free: '5', pro: '300' },
    { feature: 'File types', free: 'PDF, JPG, PNG', pro: 'PDF, JPG, PNG' },
    { feature: 'Max pages per PDF', free: '6', pro: '6' },
    { feature: 'Excel download', free: true, pro: true },
    { feature: 'Edit before download', free: true, pro: true },
    { feature: 'Priority processing', free: false, pro: true },
    { feature: 'Email support', free: false, pro: true },
    { feature: 'Price', free: '$0', pro: `${proPrice}/month` },
  ];

  const faqItems = [
    { q: 'Can I cancel my Pro subscription anytime?', a: 'Yes. Cancel anytime from your account settings. You keep Pro access until the end of your billing period.' },
    { q: 'What happens when I run out of credits?', a: "Free users can upgrade to Pro. Pro users' credits reset on the 1st of each month." },
    { q: 'Do unused credits roll over?', a: 'No. Credits reset monthly and do not roll over.' },
    { q: 'Is there a free trial for Pro?', a: 'All new users get 5 free conversions to try the tool. No credit card required.' },
    { q: 'What payment methods are accepted?', a: 'Indian users can pay via Razorpay (UPI, cards, net banking). International users can pay via Paddle (all major cards).' },
  ];

  return (
    <>
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
              <Link href="/blog" className="text-sm text-muted-foreground hover:text-foreground hidden sm:inline">Blog</Link>
              <Link href="/contact" className="text-sm text-muted-foreground hover:text-foreground hidden sm:inline">Contact</Link>
              <Link href="/" className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium shadow hover:bg-primary/90">Get Started</Link>
            </div>
          </div>
        </div>
      </nav>

      <main role="main">
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-4xl font-bold text-center mb-4">Love2Excel Pricing — PDF to Excel Converter Plans</h1>
            <p className="text-muted-foreground text-center mb-12 max-w-xl mx-auto">Start free. Upgrade when you need more conversions.</p>
            <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
              {/* Free */}
              <div className="border-2 rounded-xl p-8">
                <h3 className="text-xl font-semibold">Free Forever</h3>
                <div className="text-4xl font-bold mt-4">$0<span className="text-lg font-normal text-muted-foreground">/month</span></div>
                <ul className="mt-6 space-y-3">
                  {['5 PDF to Excel conversions', 'PDF, JPG, PNG support', 'Up to 6 pages per PDF', 'Excel .xlsx download', 'Standard processing speed'].map((f, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" />{f}</li>
                  ))}
                </ul>
                <Link href="/" className="mt-6 block w-full text-center rounded-md border border-primary text-primary px-4 py-2.5 text-sm font-medium hover:bg-primary/5">Start Free — No Card Needed</Link>
              </div>
              {/* Pro */}
              <div className="border-2 border-primary rounded-xl p-8 relative">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2"><span className="bg-primary text-primary-foreground px-3 py-1 rounded-full text-xs font-medium">Most Popular</span></div>
                <h3 className="text-xl font-semibold">Pro</h3>
                <div className="text-4xl font-bold mt-4">{proPrice}<span className="text-lg font-normal text-muted-foreground">{proPriceSuffix}</span></div>
                {!isIndian && <p className="text-sm text-muted-foreground">or ₹699/month for India</p>}
                {isIndian && <p className="text-sm text-muted-foreground">or $9/month (international)</p>}
                <ul className="mt-6 space-y-3">
                  {['300 conversions per month', 'Everything in Free', 'Up to 6 pages per PDF', 'Priority processing', 'Email support at hello@love2excel.com', 'Cancel anytime'].map((f, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" />{f}</li>
                  ))}
                </ul>
                <Link href="/" className="mt-6 block w-full text-center rounded-md bg-primary text-primary-foreground px-4 py-2.5 text-sm font-medium hover:bg-primary/90">Upgrade to Pro</Link>
              </div>
            </div>
          </div>
        </section>

        {/* Comparison Table */}
        <section className="py-16 bg-white">
          <div className="max-w-4xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-8">Free vs Pro Plan Comparison</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border rounded-xl overflow-hidden">
                <thead><tr className="bg-muted"><th className="text-left py-3 px-4 font-medium">Feature</th><th className="text-center py-3 px-4 font-medium">Free</th><th className="text-center py-3 px-4 font-medium">Pro</th></tr></thead>
                <tbody>
                  {features.map((f, i) => (
                    <tr key={i} className="border-t">
                      <td className="py-3 px-4">{f.feature}</td>
                      <td className="py-3 px-4 text-center">{typeof f.free === 'boolean' ? (f.free ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : <X className="w-4 h-4 text-muted-foreground mx-auto" />) : f.free}</td>
                      <td className="py-3 px-4 text-center">{typeof f.pro === 'boolean' ? (f.pro ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : <X className="w-4 h-4 text-muted-foreground mx-auto" />) : f.pro}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Pricing FAQ */}
        <section className="py-16">
          <div className="max-w-3xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-8">Pricing FAQ</h2>
            <div className="space-y-4">
              {faqItems.map((item, i) => (
                <div key={i} className="border rounded-lg p-5">
                  <h3 className="font-semibold mb-2">{item.q}</h3>
                  <p className="text-sm text-muted-foreground">{item.a}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-primary text-white">
          <div className="max-w-3xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold mb-4">Start converting PDFs to Excel free</h2>
            <Link href="/" className="inline-flex items-center justify-center rounded-md bg-white text-primary px-6 py-3 text-sm font-medium hover:bg-white/90">
              Start converting PDFs to Excel free →
            </Link>
          </div>
        </section>
      </main>
    </>
  );
}
