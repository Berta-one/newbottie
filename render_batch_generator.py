#!/usr/bin/env python3
"""
Render Batch Generator
Creates optimized environment variable batches for Render deployment
Solves the 100 environment variable limit by creating manageable chunks
"""

import os
from pathlib import Path

def create_render_batches():
    """Create 3 optimized batches for Render deployment"""
    
    # Read the top 50 file as our source
    source_file = "sentiment_top_50_vars.env"
    if not os.path.exists(source_file):
        print(f"❌ Source file {source_file} not found!")
        return
    
    with open(source_file, 'r') as f:
        lines = f.readlines()
    
    # Clean lines and remove empty ones
    lines = [line.strip() for line in lines if line.strip()]
    
    # Create 3 batches
    batch_size = len(lines) // 3
    batches = [
        lines[:batch_size],                    # Batch 1: 0-16
        lines[batch_size:batch_size*2],        # Batch 2: 17-33  
        lines[batch_size*2:]                   # Batch 3: 34-end
    ]
    
    # Write batch files
    for i, batch in enumerate(batches, 1):
        filename = f"render_batch_{i}.env"
        with open(filename, 'w') as f:
            f.write("# Render Environment Variables Batch {}\n".format(i))
            f.write("# Copy and paste these variables into Render Environment Variables section\n")
            f.write("# Total variables in this batch: {}\n\n".format(len(batch)))
            
            for line in batch:
                f.write(line + "\n")
        
        print(f"✅ Created {filename} with {len(batch)} variables")
    
    # Create deployment instructions
    create_batch_instructions(len(lines))

def create_batch_instructions(total_vars):
    """Create detailed deployment instructions for batches"""
    
    instructions = f"""# Render Batch Deployment Instructions

## Overview
Your {total_vars} sentiment variables have been split into 3 manageable batches to work with Render's environment variable limits.

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
.\\deploy_to_render.ps1
```

## Verification
After deployment, you should have approximately {total_vars} sentiment variables in your Render environment starting with `SENTIMENT_KW_`.

## Troubleshooting
- If variables don't appear, try refreshing the Render dashboard
- If deployment fails, reduce batch size by splitting further
- Check Render logs for any environment variable related errors
"""
    
    with open("render_batch_deployment.md", 'w') as f:
        f.write(instructions)
    
    print("✅ Created render_batch_deployment.md with detailed instructions")

if __name__ == "__main__":
    print("🚀 Creating Render environment variable batches...")
    create_render_batches()
    print("🎉 Batch creation complete! Check the deployment instructions.")
