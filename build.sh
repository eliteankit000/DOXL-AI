#!/bin/bash

echo "🚀 Starting DocXL AI build process..."

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
yarn install

# Install Python dependencies using --break-system-packages flag
# This is safe on Render as each service has isolated Python environment
echo "🐍 Installing Python dependencies..."
python3 -m pip install --break-system-packages --quiet openai pdfplumber python-dateutil Pillow

# Verify Python packages installed
echo "✅ Verifying Python packages..."
python3 -c "import openai; print('OpenAI:', openai.__version__)"
python3 -c "import pdfplumber; print('pdfplumber installed')"
python3 -c "import PIL; print('Pillow installed')"

# Build Next.js app
echo "🏗️  Building Next.js app..."
yarn build

echo "✅ Build completed successfully!"
