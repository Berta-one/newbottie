#!/usr/bin/env python3
"""
Script to help trigger Render deployment manually
"""

import os
import time
from datetime import datetime

def create_deployment_trigger():
    """Create a deployment trigger file to force Render to redeploy"""
    
    print("🚀 TRIGGERING RENDER DEPLOYMENT")
    print("=" * 40)
    
    # Create a deployment timestamp file
    timestamp = datetime.now().isoformat()
    
    deploy_content = f"""# Deployment Trigger
# This file forces Render to detect changes and redeploy

DEPLOYMENT_TIMESTAMP={timestamp}
EXECUTION_LOOP_FIX=enabled
FORCE_FULL_MODE=true

# This deployment includes:
# - Execution loop startup fix
# - Background trading loops enabled
# - FULL mode instead of MINIMAL mode
# - Autonomous trade execution enabled

# Expected result:
# Bot will switch from MINIMAL to FULL mode and start executing trades
"""
    
    with open('DEPLOYMENT_TRIGGER.txt', 'w') as f:
        f.write(deploy_content)
    
    print(f"✅ Created deployment trigger file")
    print(f"📅 Timestamp: {timestamp}")
    
    return True

def commit_deployment_trigger():
    """Commit the deployment trigger to force GitHub/Render sync"""
    
    import subprocess
    
    try:
        # Add the trigger file
        result = subprocess.run(['git', 'add', 'DEPLOYMENT_TRIGGER.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Added deployment trigger to git")
        
        # Commit with deployment message
        commit_msg = f"Deploy: Force execution loop activation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Committed deployment trigger")
            print(f"📝 Commit message: {commit_msg}")
        else:
            print(f"⚠️ Commit result: {result.stderr}")
        
        # Push to main
        result = subprocess.run(['git', 'push', 'origin', 'main'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Pushed to main branch")
            print("🌐 Render should detect changes and auto-deploy")
        else:
            print(f"❌ Push failed: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Git operations failed: {e}")
        return False

def check_deployment_status():
    """Check if deployment is working"""
    
    print(f"\n⏳ MONITORING DEPLOYMENT...")
    print("=" * 40)
    
    print("🔍 What to watch for:")
    print("1. Check your Render dashboard for new deployment")
    print("2. Monitor deployment logs for:")
    print("   ✅ '🚀 Starting execution loops...'")
    print("   ✅ '✅ Execution loop started'")
    print("   ✅ '✅ Signals loop started'")
    print("   ✅ '🎯 Bot in FULL execution mode'")
    
    print(f"\n📊 Verification commands (run in 3-5 minutes):")
    print("curl https://bottie-1.onrender.com/trading/status")
    print("# Should show: \"mode\": \"FULL\"")
    print("")
    print("curl https://bottie-1.onrender.com/trades")
    print("# Should show executed trades within 10 minutes")
    
    print(f"\n🎯 Expected timeline:")
    print("• 0-2 min: Render detects changes")
    print("• 2-4 min: Build and deploy")
    print("• 4-6 min: Service restart with execution loops")
    print("• 6-10 min: First trades executed")
    print("• 10+ min: Autonomous trading active")

def main():
    """Main deployment trigger function"""
    
    print("🤖 RENDER DEPLOYMENT TRIGGER")
    print("=" * 50)
    print("This will force Render to redeploy with the execution loop fix")
    
    # Create trigger file
    if create_deployment_trigger():
        
        # Commit and push
        if commit_deployment_trigger():
            
            # Show monitoring instructions
            check_deployment_status()
            
            print(f"\n🎉 DEPLOYMENT TRIGGERED!")
            print("=" * 50)
            print("✅ Changes committed to main branch")
            print("✅ Render will auto-deploy within 2-3 minutes")
            print("✅ Bot will switch to FULL mode and start trading")
            
            print(f"\n🔗 Monitor your deployment:")
            print("• Render Dashboard: https://dashboard.render.com")
            print("• Bot Status: https://bottie-1.onrender.com/trading/status")
            print("• Bot Health: https://bottie-1.onrender.com/health")
            
        else:
            print("❌ Failed to commit deployment trigger")
    else:
        print("❌ Failed to create deployment trigger")

if __name__ == "__main__":
    main()