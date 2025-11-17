# PostgreSQL Setup for Persistent User Storage

## Problem
Users are getting wiped on each Railway deployment because filesystem is ephemeral.

## Solution: Railway PostgreSQL Plugin

Railway provides a PostgreSQL database plugin that persists data across deployments.

## Step-by-Step Setup

### Step 1: Add PostgreSQL Plugin

**Option A: From Project Dashboard**
1. Go to Railway Dashboard: https://railway.app
2. Select your project
3. Look for **"+ New"** button (usually top right or in the project view)
4. Click **"+ New"** → Select **"Database"** → **"Add PostgreSQL"**
5. Railway will create a PostgreSQL database

**Option B: From Service Menu (Alternative)**
1. In your project, look for the **"New"** button or **"+"** icon
2. Click it and select **"Database"** → **"PostgreSQL"**
3. Railway will create a PostgreSQL database

**Option C: If you don't see Database option**
1. Go to your project dashboard
2. Click **"+ New"** or **"New Service"**
3. Look for **"Template"** or **"Plugin"** section
4. Search for "PostgreSQL" or look under **"Databases"**
5. Click **"Add PostgreSQL"** or **"Provision PostgreSQL"**

### Step 2: Link Database to Your Service

1. After PostgreSQL is created, click on your **web service** (the one running your app)
2. Go to **"Variables"** tab (or click **"View Variables"** from the service menu)
3. Railway should automatically add `DATABASE_URL` to your service
4. If `DATABASE_URL` is not automatically added:
   - Click **"Add Variable"** or **"New Variable"**
   - **Name**: `DATABASE_URL`
   - **Value**: Go to the PostgreSQL service → **"Variables"** tab → Copy the `DATABASE_URL` value
   - Paste it into your web service's `DATABASE_URL` variable

### Step 3: Verify and Deploy

1. Check that `DATABASE_URL` is set in your web service variables
2. Railway will automatically redeploy when variables change
3. The app will detect `DATABASE_URL` and use PostgreSQL
4. Users will persist permanently! ✅

## How It Works

- When `DATABASE_URL` is set, the app uses PostgreSQL
- When `DATABASE_URL` is not set, it falls back to JSON file
- PostgreSQL table is created automatically on first run
- Default admin (PIN 0000) is created automatically

## Verification

After deployment, check logs for:
- "Created default admin user in PostgreSQL" (first time)
- "Using existing PostgreSQL users table" (subsequent deployments)
- "Loaded X users from PostgreSQL"

## Benefits

✅ **Persistent**: Data survives deployments
✅ **Reliable**: Database is managed by Railway
✅ **Automatic**: No volume setup needed
✅ **Free Tier**: PostgreSQL plugin is available on free tier

## Migration from JSON

If you have users in JSON file:
1. Add PostgreSQL plugin
2. Users will be migrated automatically on next save
3. Or manually recreate them through Admin panel

