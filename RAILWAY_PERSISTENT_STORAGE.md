# Railway Persistent Storage Setup

## Problem
ChromaDB data is stored in `./chroma_db/` directory, which gets wiped on each Railway deployment.

## Solution: Add Persistent Volume

### Option 1: Via Railway Dashboard (Recommended)

1. Go to Railway Dashboard: https://railway.app/project/94afacbb-a2fb-440d-b567-f7af07b0b5b1
2. Click on your service
3. Go to "Settings" tab
4. Scroll to "Volumes" section
5. Click "Add Volume"
6. Configure:
   - **Mount Path**: `/app/chroma_db`
   - **Size**: 5 GB (or more if needed)
7. Click "Add"
8. Railway will redeploy automatically

### Option 2: Via Railway CLI

```bash
railway volume create --mount /app/chroma_db --size 5GB
```

## After Adding Volume

1. Railway will redeploy
2. Upload your files again through the web interface
3. Process them to populate the database
4. Data will now persist across deployments!

## Alternative: Re-upload Files

If you don't want to set up persistent storage right now:
1. Go to web interface: https://twilio-chatbot-production-154e.up.railway.app
2. Upload your files again
3. Process them
4. Note: Data will be lost on next deployment unless you add persistent storage

## Backup Strategy

For production, consider:
- Setting up automated backups of chroma_db
- Or using an external vector database (Pinecone, Weaviate, etc.)
