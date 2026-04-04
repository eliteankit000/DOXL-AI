import { App } from '@/components/AppShell';
import JsonLd from '@/components/JsonLd';

export const metadata = {
  title: 'Convert PDF to Excel Free Online — DocXL AI',
  description:
    'The fastest AI-powered PDF to Excel converter. Upload invoices, ' +
    'bank statements, or any PDF table and get a clean Excel file ' +
    'instantly. Free credits included. No credit card required.',
  alternates: { canonical: 'https://docxl.ai' },
  openGraph: {
    title: 'Convert PDF to Excel Free Online — DocXL AI',
    description: 'AI-powered PDF to Excel in seconds. Try free.',
    url: 'https://docxl.ai',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
};

const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'How do I convert a PDF to Excel?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Upload your PDF on DocXL AI, our AI extracts all tables and data automatically, and you can download the result as an Excel .xlsx file in seconds.',
      },
    },
    {
      '@type': 'Question',
      name: 'Is DocXL AI free?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Yes. DocXL AI includes 5 free credits on signup. Each credit converts one PDF or image to Excel. Upgrade to Pro for 300 credits per month.',
      },
    },
    {
      '@type': 'Question',
      name: 'What file types does DocXL AI support?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'DocXL AI supports PDF, JPG, JPEG, and PNG files. It can extract tables from any of these formats.',
      },
    },
    {
      '@type': 'Question',
      name: 'How accurate is the AI extraction?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: "DocXL AI uses GPT-4o, OpenAI's most capable model, for extraction. It achieves high accuracy on structured documents like invoices, bank statements, and data tables.",
      },
    },
    {
      '@type': 'Question',
      name: 'What is the page limit per PDF?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'DocXL AI processes up to 6 pages per PDF. For longer documents, split the PDF into parts and upload each separately.',
      },
    },
  ],
};

const howToSchema = {
  '@context': 'https://schema.org',
  '@type': 'HowTo',
  name: 'How to Convert PDF to Excel Using DocXL AI',
  description: 'Convert any PDF to Excel in 3 simple steps using AI',
  step: [
    {
      '@type': 'HowToStep',
      position: 1,
      name: 'Upload your PDF or image',
      text: 'Drag and drop or click to upload your PDF, JPG, or PNG file.',
    },
    {
      '@type': 'HowToStep',
      position: 2,
      name: 'AI extracts your data',
      text: 'GPT-4o analyzes your document and extracts all tables and data automatically.',
    },
    {
      '@type': 'HowToStep',
      position: 3,
      name: 'Download your Excel file',
      text: 'Review the extracted data, make any edits, then download as .xlsx.',
    },
  ],
  totalTime: 'PT30S',
  tool: { '@type': 'HowToTool', name: 'DocXL AI' },
};

export default function Page() {
  return (
    <>
      <JsonLd data={faqSchema} />
      <JsonLd data={howToSchema} />
      <App />
    </>
  );
}
