import PricingContent from '@/components/PricingContent';
import Footer from '@/components/Footer';
import JsonLd from '@/components/JsonLd';

export const metadata = {
  title: 'Pricing — DocXL AI PDF to Excel Converter',
  description:
    'DocXL AI pricing plans. Start free with 5 credits. Upgrade to Pro ' +
    'for unlimited PDF to Excel conversions at $9/month. Cancel anytime.',
  alternates: { canonical: 'https://docxl.ai/pricing' },
  openGraph: {
    title: 'Pricing — DocXL AI PDF to Excel Converter',
    description: 'Start free. Upgrade to Pro for $9/month.',
    url: 'https://docxl.ai/pricing',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
};

const pricingSchema = {
  '@context': 'https://schema.org',
  '@type': 'Product',
  name: 'DocXL AI Pro',
  description: '300 AI-powered PDF to Excel conversions per month',
  brand: { '@type': 'Brand', name: 'DocXL AI' },
  offers: {
    '@type': 'Offer',
    price: '9.00',
    priceCurrency: 'USD',
    priceValidUntil: '2025-12-31',
    availability: 'https://schema.org/InStock',
    url: 'https://docxl.ai/pricing',
  },
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.8',
    reviewCount: '124',
  },
};

export default function PricingPage() {
  return (
    <>
      <JsonLd data={pricingSchema} />
      <div className="min-h-screen bg-background">
        <PricingContent />
        <Footer />
      </div>
    </>
  );
}
