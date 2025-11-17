#!/bin/bash

# Script to add DATABASE_URL from PostgreSQL to twilio-chatbot service

echo "🔗 Adding DATABASE_URL to twilio-chatbot service..."
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in. Please run 'railway login' first."
    exit 1
fi

echo "✅ Logged in as: $(railway whoami)"
echo ""

# Link to project
echo "Linking to project..."
cd "$(dirname "$0")"
railway link

echo ""

# Get DATABASE_URL from PostgreSQL service
echo "Fetching DATABASE_URL from PostgreSQL service..."

# Try different service names
DB_URL=""
for service_name in "postgres" "postgresql" "Postgres" "PostgreSQL"; do
    DB_URL=$(railway variables --service "$service_name" 2>/dev/null | grep "DATABASE_URL" | head -1 | awk -F'│' '{print $2}' | xargs)
    if [ ! -z "$DB_URL" ]; then
        echo "✅ Found DATABASE_URL from service: $service_name"
        break
    fi
done

if [ -z "$DB_URL" ]; then
    echo "❌ Could not find DATABASE_URL automatically."
    echo ""
    echo "Please add it manually:"
    echo "1. Copy DATABASE_URL from PostgreSQL service Variables tab"
    echo "2. Run: railway variables --service twilio-chatbot --set DATABASE_URL=\"<paste value>\""
    echo ""
    echo "Or add it via Railway Dashboard:"
    echo "- Go to twilio-chatbot service → Variables → New Variable"
    echo "- Name: DATABASE_URL"
    echo "- Value: (paste from PostgreSQL service)"
    exit 1
fi

# Add DATABASE_URL to twilio-chatbot service
echo ""
echo "Adding DATABASE_URL to twilio-chatbot service..."
railway variables --service twilio-chatbot --set "DATABASE_URL=$DB_URL"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ DATABASE_URL added successfully!"
    echo ""
    echo "Railway will automatically redeploy your service."
    echo "Check deployment logs for:"
    echo "  ✅ 'Connected to PostgreSQL database'"
    echo "  ✅ 'PostgreSQL initialized with X user(s)'"
    echo ""
    echo "Users will now persist across deployments! 🎉"
else
    echo ""
    echo "❌ Failed to add DATABASE_URL. Please add it manually via Railway Dashboard."
    exit 1
fi

