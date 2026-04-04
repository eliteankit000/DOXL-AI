import PrivacyClient from '@/components/PrivacyClient';

export const metadata = {
  title: 'Privacy Policy — DocXL AI',
  description: 'Privacy Policy for DocXL AI PDF to Excel converter.',
  alternates: { canonical: 'https://docxl.ai/privacy' },
  robots: { index: true, follow: false },
};

export default function PrivacyPage() {
  return <PrivacyClient />;
}
