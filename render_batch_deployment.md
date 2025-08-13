# Render Batch Deployment Instructions

## Overview
Your 50 sentiment variables have been split into 3 manageable batches to work with Render's environment variable limits.

## Files Created
- `render_batch_1.env` - First batch of variables
- `render_batch_2.env` - Second batch of variables  
- `render_batch_3.env` - Third batch of variables

## Deployment Steps

### Step 1: Access Render Dashboard
1. Go to https://dashboard.render.com
2. Select your Bottie service
3. Go to "Environment" tab

### Step 2: Deploy Batch 1
1. Open `render_batch_1.env` in a text editor
2. Copy all variables (skip the # comment lines)
3. Paste into Render Environment Variables section
4. Click "Save Changes"

### Step 3: Deploy Batch 2
1. Open `render_batch_2.env` in a text editor
2. Copy all variables (skip the # comment lines)  
3. Add to existing Environment Variables in Render
4. Click "Save Changes"

### Step 4: Deploy Batch 3
1. Open `render_batch_3.env` in a text editor
2. Copy all variables (skip the # comment lines)
3. Add to existing Environment Variables in Render
4. Click "Save Changes"

### Step 5: Verify Deployment
1. Check that all variables are visible in Render Environment tab
2. Restart your service if needed
3. Test the sentiment analysis endpoints

## Alternative: PowerShell Helper
Use the PowerShell script for automated copying:
```powershell
.\deploy_to_render.ps1
```

## Verification
After deployment, you should have approximately 50 sentiment variables in your Render environment starting with `SENTIMENT_KW_`.

## Troubleshooting
- If variables don't appear, try refreshing the Render dashboard
- If deployment fails, reduce batch size by splitting further
- Check Render logs for any environment variable related errors
