# Pinecone Setup Guide

## Quick Setup (5 minutes)

### Step 1: Sign up for Pinecone
1. Go to: https://app.pinecone.io
2. Sign up for free account
3. Create a new project (or use default)

### Step 2: Create Index
1. In Pinecone dashboard, click "Create Index"
2. Name: `customer-service-kb` (or any name you prefer)
3. Dimensions: `1536` (for OpenAI text-embedding-ada-002)
4. Metric: `cosine`
5. Click "Create Index"

### Step 3: Get API Key
1. Go to "API Keys" section
2. Copy your API key
3. Note your environment (e.g., `us-east1-gcp`)

### Step 4: Add to Railway
1. Go to Railway → Your Service → Variables
2. Add these variables:
   - `PINECONE_API_KEY` = [your API key]
   - `PINECONE_ENVIRONMENT` = [your environment, e.g., `us-east1-gcp`]

### Step 5: Deploy
- Railway will auto-deploy
- Or trigger manual redeploy

## Environment Variables Needed

```
PINECONE_API_KEY=your_api_key_here
PINECONE_ENVIRONMENT=us-east1-gcp
```

## Free Tier Limits

- ✅ 1 index
- ✅ 100K vectors
- ✅ 5GB storage
- ✅ Perfect for testing/development

## After Setup

1. Upload your files through web interface
2. Process them
3. Data will be stored in Pinecone
4. **Data persists across deployments!** ✅

## Troubleshooting

**Error: "PINECONE_API_KEY not set"**
- Make sure you added the variable in Railway
- Check spelling (case-sensitive)

**Error: "Index not found"**
- Create the index in Pinecone dashboard first
- Use the exact index name

**Error: "Environment not found"**
- Check your Pinecone dashboard for correct environment name
- Common: `us-east1-gcp`, `us-west1-gcp`, `eu-west1-gcp`

## Migration from ChromaDB

- Old ChromaDB data won't transfer automatically
- Re-upload files through web interface
- They'll be stored in Pinecone going forward

