#!/bin/bash

# Railway PostgreSQL Setup Script
# Run this script to add PostgreSQL to your Railway project

echo "🚂 Railway PostgreSQL Setup"
echo "=========================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    brew install railway
fi

echo "✅ Railway CLI installed"
echo ""

# Step 1: Login (requires browser)
echo "Step 1: Logging into Railway..."
echo "This will open your browser for authentication."
railway login

if [ $? -ne 0 ]; then
    echo "❌ Login failed. Please run 'railway login' manually."
    exit 1
fi

echo "✅ Logged in successfully"
echo ""

# Step 2: Link to project
echo "Step 2: Linking to project..."
cd "$(dirname "$0")"
railway link

if [ $? -ne 0 ]; then
    echo "❌ Failed to link project. Please select your project manually."
    exit 1
fi

echo "✅ Project linked"
echo ""

# Step 3: Add PostgreSQL
echo "Step 3: Adding PostgreSQL database..."
railway add --database postgres

if [ $? -ne 0 ]; then
    echo "❌ Failed to add PostgreSQL. Please check Railway dashboard."
    exit 1
fi

echo ""
echo "✅ PostgreSQL added successfully!"
echo ""
echo "Next steps:"
echo "1. Railway should automatically add DATABASE_URL to your web service"
echo "2. Check your web service Variables tab to confirm DATABASE_URL is set"
echo "3. Your app will automatically use PostgreSQL on next deployment"
echo ""
echo "Done! 🎉"

