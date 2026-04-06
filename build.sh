#!/bin/bash

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
yarn install

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Build Next.js app
echo "Building Next.js app..."
yarn build

echo "Build completed successfully!"
