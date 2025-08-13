# JSON Sentiment Configuration Usage

## Overview
All 50 sentiment keywords from `sentiment_top_50_vars.env` have been consolidated into a single JSON configuration.

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
    return {}

# Get keywords for an asset
def get_sentiment_keywords(asset):
    config = load_sentiment_config()
    return config.get('sentiment_keywords', {}).get(asset.lower(), [])

# Example usage
eth_keywords = get_sentiment_keywords('ETH')
btc_keywords = get_sentiment_keywords('BTC')
```

## Benefits
- ✅ Only 1 environment variable instead of 50
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
