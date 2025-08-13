#!/usr/bin/env python3
"""
Helper script to generate sentiment variables for Render deployment
Generates a clean list that's easy to copy-paste into Render environment variables
"""

import os
import subprocess
import sys

def generate_sentiment_vars():
    """Generate sentiment variables with different options"""
    
    print("🧠 Sentiment Variables Generator for Render")
    print("=" * 50)
    print()
    
    # Options
    options = [
        ("Top 20 assets (recommended for testing)", "20"),
        ("Top 50 assets (good balance)", "50"), 
        ("Top 100 assets (comprehensive)", "100"),
        ("All assets (200+ variables)", "0")
    ]
    
    print("Choose an option:")
    for i, (desc, value) in enumerate(options, 1):
        print(f"{i}. {desc}")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice not in ['1', '2', '3', '4']:
        print("Invalid choice. Using default (Top 50)")
        choice = '2'
    
    top_by_volume = options[int(choice) - 1][1]
    
    print(f"\n🔄 Generating sentiment variables...")
    
    # Set environment and run generator
    env = os.environ.copy()
    env['TOP_BY_VOLUME'] = top_by_volume
    env['ONLY_SPOT'] = '1'
    env['INCLUDE_STABLES'] = '0'
    
    try:
        result = subprocess.run([
            sys.executable, 'generate_all_sentiment_vars.py'
        ], env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            lines = output.split('\n')
            
            print(f"✅ Generated {len(lines)} sentiment variables")
            print()
            
            # Save to file
            filename = f"sentiment_top_{top_by_volume}_vars.env"
            with open(filename, 'w') as f:
                f.write(output)
            
            print(f"📁 Saved to: {filename}")
            print()
            
            # Show first few for preview
            print("📋 Preview (first 5 variables):")
            print("-" * 40)
            for line in lines[:5]:
                print(line)
            
            if len(lines) > 5:
                print(f"... and {len(lines) - 5} more")
            
            print()
            print("🚀 Ready for Render Deployment:")
            print(f"1. Copy contents of {filename}")
            print("2. Paste into Render environment variables")
            print("3. Deploy and test cross-pair trading with sentiment!")
            
        else:
            print(f"❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error running generator: {e}")

if __name__ == "__main__":
    generate_sentiment_vars()
