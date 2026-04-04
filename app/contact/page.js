import ContactClient from '@/components/ContactClient';

export const metadata = {
  title: 'Contact Support — DocXL AI',
  description:
    'Get help with DocXL AI. Contact our support team for questions ' +
    'about PDF to Excel conversions, billing, or your account. ' +
    'We reply within 24 hours.',
  alternates: { canonical: 'https://docxl.ai/contact' },
  openGraph: {
    title: 'Contact Support — DocXL AI',
    description: 'Reach our support team. We reply within 24 hours.',
    url: 'https://docxl.ai/contact',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
};

export default function ContactPage() {
  return <ContactClient />;
}
