import ContactClient from '@/components/ContactClient';

export const metadata = {
  title: 'Contact Support — Love2Excel',
  description:
    'Get help with Love2Excel. Contact our support team for questions ' +
    'about PDF to Excel conversions, billing, or your account. ' +
    'We reply within 24 hours.',
  alternates: { canonical: 'https://love2excel.ai/contact' },
  openGraph: {
    title: 'Contact Support — Love2Excel',
    description: 'Reach our support team. We reply within 24 hours.',
    url: 'https://love2excel.ai/contact',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
};

export default function ContactPage() {
  return <ContactClient />;
}
