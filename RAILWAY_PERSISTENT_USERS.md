# Railway Persistent Storage for Users

## Problem
The `users.json` file resets after each deployment because Railway's filesystem is ephemeral.

## Solution
Use Railway's persistent volume feature to store user data.

## Steps to Set Up Persistent Storage

1. **Add Volume in Railway Dashboard:**
   - Go to your Railway project
   - Click on your service
   - Go to the "Volumes" tab
   - Click "Add Volume"
   - Name: `data`
   - Mount Path: `/data`
   - Click "Add"

2. **Set Environment Variable:**
   - Go to "Variables" tab
   - Add: `DATA_DIR=/data`
   - This tells the app to store users.json and uploads in the persistent volume

3. **Redeploy:**
   - Railway will automatically redeploy
   - Users will now persist across deployments!

## What Gets Stored in `/data`:
- `users.json` - User accounts and PINs
- `uploads/` - Uploaded files

## Alternative: Manual Migration
If you already have users, you can manually recreate them through the Admin panel after setting up the volume.

