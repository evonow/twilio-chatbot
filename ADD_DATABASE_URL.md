# Fix: Add DATABASE_URL to Railway

## Problem
Users are being wiped on each deployment because `DATABASE_URL` is not set, so the app falls back to JSON file storage (which is ephemeral).

## Solution: Add DATABASE_URL Variable

### Step 1: Get DATABASE_URL from PostgreSQL Service

1. Go to Railway Dashboard: https://railway.app
2. Open your project: **nurturing-adaptation**
3. Find the **PostgreSQL** service (it should be listed alongside twilio-chatbot)
4. Click on the **PostgreSQL** service
5. Go to **"Variables"** tab
6. Find **`DATABASE_URL`** - it will look like:
   ```
   postgresql://postgres:password@hostname:5432/railway
   ```
7. **Copy the entire DATABASE_URL value**

### Step 2: Add DATABASE_URL to twilio-chatbot Service

1. Click on **twilio-chatbot** service (not PostgreSQL)
2. Go to **"Variables"** tab
3. Click **"New Variable"** or **"Add Variable"**
4. Enter:
   - **Name**: `DATABASE_URL`
   - **Value**: Paste the DATABASE_URL you copied from PostgreSQL service
5. Click **"Add"** or **"Save"**

### Step 3: Verify

1. Railway will automatically redeploy your service
2. Check deployment logs for:
   - ✅ "Connected to PostgreSQL database"
   - ✅ "PostgreSQL initialized with X user(s)"
3. If you see ⚠️ "DATABASE_URL not set", the variable wasn't added correctly

### Step 4: Test

1. Create a test user in the admin panel
2. Check deployment logs to confirm PostgreSQL is being used
3. Redeploy (or wait for next deployment)
4. Verify the test user still exists

## Why This Happened

Railway usually automatically adds `DATABASE_URL` when you add PostgreSQL, but sometimes it doesn't link properly. Adding it manually ensures the connection works.

## After Fix

Once `DATABASE_URL` is set:
- ✅ Users will persist across deployments
- ✅ No more data loss on redeploy
- ✅ All user management operations use PostgreSQL

