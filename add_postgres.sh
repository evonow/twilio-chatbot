#!/bin/bash

# Quick script to add PostgreSQL after Railway login
# Run this AFTER running 'railway login'

echo "🚂 Adding PostgreSQL to Railway..."
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in. Please run 'railway login' first."
    exit 1
fi

echo "✅ Logged in as: $(railway whoami)"
echo ""

# Link to project (if not already linked)
echo "Linking to project..."
cd "$(dirname "$0")"
railway link

if [ $? -ne 0 ]; then
    echo "⚠️  Project may already be linked, or you need to select it manually"
fi

echo ""

# Add PostgreSQL
echo "Adding PostgreSQL database..."
railway add --database postgres

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ PostgreSQL added successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Railway should automatically add DATABASE_URL to your web service"
    echo "2. Check your web service Variables tab in Railway dashboard"
    echo "3. Your app will automatically use PostgreSQL on next deployment"
    echo ""
    echo "Done! 🎉"
else
    echo ""
    echo "❌ Failed to add PostgreSQL. Please check Railway dashboard manually."
    exit 1
fi

