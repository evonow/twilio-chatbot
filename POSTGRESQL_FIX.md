# PostgreSQL Setup Fix Guide

## Issue
The warning "psycopg2 not installed - using JSON file fallback (ephemeral)" means PostgreSQL is not properly configured, causing users to be lost on each deployment.

## Solution Steps

### 1. Verify psycopg2-binary is installed
✅ **DONE**: Added `psycopg2-binary>=2.9.9` to `requirements.txt`
- Railway will automatically install it on the next deployment

### 2. Verify PostgreSQL Database exists on Railway
1. Go to your Railway dashboard: https://railway.app
2. Select your project
3. Check if you see a PostgreSQL service (separate from your web service)
4. If not, add it:
   - Click "+ New" → "Database" → "Add PostgreSQL"
   - Or use Railway CLI: `railway add postgresql`

### 3. Add DATABASE_URL to your web service
The PostgreSQL service creates a `DATABASE_URL` environment variable, but it needs to be linked to your web service.

**Option A: Using Railway Dashboard (Easiest)**
1. Go to your **web service** (not the PostgreSQL service)
2. Click on "Variables" tab
3. Click "+ New Variable"
4. Name: `DATABASE_URL`
5. Value: Copy the `DATABASE_URL` from your PostgreSQL service:
   - Go to PostgreSQL service → Variables tab
   - Copy the `DATABASE_URL` value
   - Paste it into your web service variables
6. Click "Add"

**Option B: Using Variable Reference (Recommended)**
1. Go to your **web service** → Variables tab
2. Click "+ New Variable"
3. Name: `DATABASE_URL`
4. Click "Reference" button (or select "Reference" from dropdown)
5. Select your PostgreSQL service
6. Select `DATABASE_URL` variable
7. Click "Add"

This automatically links the variables, so if PostgreSQL URL changes, your web service will automatically get the update.

### 4. Verify Setup
After the next deployment:
1. Log in to your app
2. Go to "User Management" section
3. Check the Database Status alert:
   - ✅ **Green**: "PostgreSQL connected | X user(s) stored | Users will persist across deployments"
   - ⚠️ **Yellow/Red**: Still needs configuration (check steps above)

### 5. Test Persistence
1. Create a test user
2. Wait for Railway to redeploy (or trigger a redeploy)
3. Log back in and verify the test user still exists

## Troubleshooting

### If psycopg2 still not found:
- Wait for Railway to finish deploying (check deployment logs)
- Verify `psycopg2-binary` is in `requirements.txt` ✅ (already done)

### If DATABASE_URL not set:
- Follow Step 3 above to add it manually
- Make sure you're adding it to the **web service**, not PostgreSQL service

### If connection fails:
- Check Railway logs for connection errors
- Verify PostgreSQL service is running (green status)
- Try copying DATABASE_URL directly from PostgreSQL service variables

## Quick Check Script
After deployment, the `/api/db-status` endpoint will show:
- `psycopg2_available`: Should be `true`
- `database_url_set`: Should be `true`
- `connection_test`: Should be `"success"`
- `using_postgres`: Should be `true`

If any of these are false, follow the steps above.

