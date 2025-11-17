# Railway Storage Solutions

## Problem
Railway deployments don't persist ChromaDB data by default.

## Solutions

### Option 1: Railway Volumes (If Available)
Railway volumes might not be visible in free tier. Check:
- Settings → Scroll down → Look for "Volumes" or "Storage"
- Or volumes might only be available in paid plans

### Option 2: Use Railway's /data Directory
Railway provides a `/data` directory that persists. Code updated to check:
1. `RAILWAY_VOLUME_MOUNT_PATH` environment variable
2. `DATA_DIR` environment variable  
3. Falls back to `./chroma_db`

To use:
1. Set environment variable: `DATA_DIR=/data`
2. Railway will use persistent `/data` directory

### Option 3: External Storage (Best for Production)
Use cloud storage:
- AWS S3
- Google Cloud Storage
- Or export/import ChromaDB data

### Option 4: Re-upload Files (Temporary)
After each deployment:
1. Upload files via web interface
2. Process them
3. Data will be available until next deployment

## Recommended: Set DATA_DIR Environment Variable

1. Go to Railway → Your Service → Variables
2. Add: `DATA_DIR` = `/data`
3. Railway will use persistent storage
4. Redeploy

This is the easiest solution that should work!
