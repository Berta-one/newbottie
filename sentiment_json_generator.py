#!/usr/bin/env python3
"""
Sentiment JSON Generator for Render
Creates a single JSON environment variable containing all sentiment keywords
Solves Render's 100 variable limit by consolidating into one SENTIMENT_CONFIG variable
"""

import json
import os
import re

def parse_env_file_to_json(env_file):
    """Parse .env file and convert to JSON structure"""
    
    if not os.path.exists(env_file):
        print(f"❌ File {env_file} not found!")
        return None
    
    sentiment_config = {}
    
    with open(env_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                # Parse SENTIMENT_KW_ETH="keywords" format
                match = re.match(r'SENTIMENT_KW_([A-Z0-9]+)="([^"]+)"', line)
                if match:
                    asset = match.group(1)
                    keywords = match.group(2)
                    # Convert comma-separated keywords to list
                    keyword_list = [kw.strip() for kw in keywords.split(',')]
                    sentiment_config[asset.lower()] = keyword_list
    
    return sentiment_config

def create_sentiment_json_config():
    """Create JSON configuration for all sentiment keywords"""
    
    # Try production file first, then fall back to top 50
    source_files = ["sentiment_production_vars.env", "sentiment_top_50_vars.env"]
    
    config = None
    source_used = None
    
    for source_file in source_files:
        if os.path.exists(source_file):
            config = parse_env_file_to_json(source_file)
            if config:
                source_used = source_file
                break
    
    if not config:
        print("❌ No valid sentiment configuration files found!")
        return
    
    # Create the JSON configuration
    json_config = {
        "sentiment_keywords": config,
        "version": "1.0",
        "generated_from": source_used,
        "total_assets": len(config)
    }
    
    # Write JSON file
    json_file = "sentiment_config.json"
    with open(json_file, 'w') as f:
        json.dump(json_config, f, indent=2)
    
    # Create the environment variable format
    json_string = json.dumps(json_config, separators=(',', ':'))  # Compact format
    
    # Create .env file with single variable
    env_file = "sentiment_json_config.env"
    with open(env_file, 'w') as f:
        f.write("# Single JSON configuration for all sentiment keywords\n")
        f.write("# Copy this single variable to Render Environment Variables\n")
        f.write(f"# Contains {len(config)} assets from {source_used}\n\n")
        f.write(f'SENTIMENT_CONFIG=\'{json_string}\'\n')
    
    print(f"✅ Created {json_file} with {len(config)} assets")
    print(f"✅ Created {env_file} for Render deployment")
    
    # Create usage instructions
    create_json_usage_instructions(source_used, len(config))
    
    return json_config

def create_json_usage_instructions(source_file, asset_count):
    """Create instructions for using JSON configuration"""
    
    instructions = f"""# JSON Sentiment Configuration Usage

## Overview
All {asset_count} sentiment keywords from `{source_file}` have been consolidated into a single JSON configuration.

## Files Created
- `sentiment_config.json` - Human-readable JSON configuration
- `sentiment_json_config.env` - Single environment variable for Render

## Render Deployment
1. Open `sentiment_json_config.env`
2. Copy the SENTIMENT_CONFIG variable
3. Paste into Render Environment Variables
4. Save changes

## Code Usage
Update your sentiment analysis code to use the JSON configuration:

```python
import json
import os

# Load sentiment configuration
def load_sentiment_config():
    config_json = os.environ.get('SENTIMENT_CONFIG')
    if config_json:
        return json.loads(config_json)
    return {{}}

# Get keywords for an asset
def get_sentiment_keywords(asset):
    config = load_sentiment_config()
    return config.get('sentiment_keywords', {{}}).get(asset.lower(), [])

# Example usage
eth_keywords = get_sentiment_keywords('ETH')
btc_keywords = get_sentiment_keywords('BTC')
```

## Benefits
- ✅ Only 1 environment variable instead of {asset_count}
- ✅ Easier to manage and update
- ✅ Works within Render's limits
- ✅ Programmatically accessible
- ✅ Version controlled

## Migration Steps
1. Deploy the SENTIMENT_CONFIG variable to Render
2. Update your sentiment analysis code to use `load_sentiment_config()`
3. Remove old SENTIMENT_KW_* variables (optional cleanup)
4. Test sentiment analysis functionality

## Verification
Check that `os.environ.get('SENTIMENT_CONFIG')` returns a valid JSON string in your application.
"""
    
    with open("sentiment_json_usage.md", 'w') as f:
        f.write(instructions)
    
    print("✅ Created sentiment_json_usage.md with implementation guide")

if __name__ == "__main__":
    print("🚀 Creating JSON sentiment configuration...")
    config = create_sentiment_json_config()
    if config:
        print(f"🎉 JSON configuration created with {len(config['sentiment_keywords'])} assets!")
        print("📖 Check sentiment_json_usage.md for implementation details")
    else:
        print("❌ Failed to create JSON configuration")
