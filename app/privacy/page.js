import PrivacyClient from '@/components/PrivacyClient';

export const metadata = {
  title: 'Privacy Policy — Love2Excel',
  description: 'Privacy Policy for Love2Excel PDF to Excel converter.',
  alternates: { canonical: 'https://love2excel.ai/privacy' },
  robots: { index: true, follow: false },
};

export default function PrivacyPage() {
  return <PrivacyClient />;
}
