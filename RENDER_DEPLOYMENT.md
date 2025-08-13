# Render Deployment Guide

## Environment Variables for Multiple Services

### Problem
Render requires unique environment variable names across all services in your account. If you have multiple Bottie services, you can't use the same `ENABLE_GRID_WS` variable name.

### Solution Options

## Option 1: Service-Specific Prefixes (Recommended)

### API Service
```bash
# Environment Variables in Render Dashboard
API_ENABLE_GRID_WS=1                    # WebSocket grid control
API_KEY=your_binance_api_key            # Trading credentials
API_SECRET=your_binance_secret          # Trading credentials
API_CLAUDE_KEY=your_claude_key          # AI analysis
```

### Main Bot Service
```bash
# Environment Variables in Render Dashboard  
BOTTIE_ENABLE_GRID_WS=1                 # WebSocket grid control
BOTTIE_API_KEY=your_binance_api_key     # Trading credentials
BOTTIE_API_SECRET=your_binance_secret   # Trading credentials
BOTTIE_CLAUDE_KEY=your_claude_key       # AI analysis
```

### Monitoring Service
```bash
# Environment Variables in Render Dashboard
MONITOR_ENABLE_GRID_WS=0                # Usually disabled for monitoring
MONITOR_API_KEY=your_binance_api_key    # Read-only credentials
MONITOR_API_SECRET=your_binance_secret  # Read-only credentials
```

## Option 2: Environment-Based Naming

### Production API Service
```bash
PROD_API_ENABLE_GRID_WS=1
PROD_API_KEY=your_prod_api_key
PROD_API_SECRET=your_prod_secret
```

### Staging API Service  
```bash
STAGING_API_ENABLE_GRID_WS=1
STAGING_API_KEY=your_test_api_key
STAGING_API_SECRET=your_test_secret
```

### Development API Service
```bash
DEV_API_ENABLE_GRID_WS=0
DEV_API_KEY=your_dev_api_key
DEV_API_SECRET=your_dev_secret
```

## Option 3: UUID-Based Unique Names

```bash
# API Service (generate unique suffix)
ENABLE_GRID_WS_A7B2=1
API_KEY_A7B2=your_api_key

# Bot Service (different unique suffix)  
ENABLE_GRID_WS_X9M4=1
API_KEY_X9M4=your_api_key
```

## Code Compatibility

The updated `api/app.py` automatically detects these variable patterns:

```python
# Checks in priority order:
1. API_ENABLE_GRID_WS      # Service-specific
2. BOTTIE_ENABLE_GRID_WS   # App-specific
3. ENABLE_GRID_WS          # Generic fallback
```

## Render Service Configuration

### 1. Create Services

#### API Service
- **Name:** `bottie-api`
- **Environment:** `Production`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn api.app:app --host 0.0.0.0 --port $PORT`

#### WebSocket Service (Optional)
- **Name:** `bottie-websocket`  
- **Environment:** `Production`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python engine/autonomous_engine_ws.py`

### 2. Set Environment Variables

#### For bottie-api service:
```bash
API_ENABLE_GRID_WS=1
API_KEY=your_binance_api_key
API_SECRET=your_binance_secret
API_CLAUDE_KEY=your_claude_key
ENVIRONMENT=production
```

#### For bottie-websocket service:
```bash
WS_ENABLE_GRID_WS=1
WS_API_KEY=your_binance_api_key  
WS_API_SECRET=your_binance_secret
ENVIRONMENT=production
```

### 3. Emergency Rollback Procedure

#### Via Render Dashboard:
1. Go to your service in Render
2. Navigate to **Environment** tab
3. Change `API_ENABLE_GRID_WS=1` to `API_ENABLE_GRID_WS=0`
4. Click **Save Changes**
5. Service auto-restarts with WebSocket disabled

#### Via Render CLI:
```bash
# Install Render CLI
npm install -g @render-cli/render

# Login to your account
render login

# Update environment variable
render env set API_ENABLE_GRID_WS 0 --service bottie-api

# Check deployment
render deployments list --service bottie-api
```

## Testing Your Setup

### 1. Verify Variable Detection
```bash
# Test locally with your naming scheme
export API_ENABLE_GRID_WS=1
python -c "import os; print('API_ENABLE_GRID_WS:', os.getenv('API_ENABLE_GRID_WS'))"
```

### 2. Test Rollback
```bash
# Disable and test
export API_ENABLE_GRID_WS=0
curl https://your-render-app.com/grid/matrix
# Should return: {"rows": [], "cols": [], "matrix": {}, "ts": ...}
```

### 3. Verify Logs
Check Render logs for startup messages:
- ✅ `Cross-pair WebSocket grid engine started`
- ℹ️ `Cross-pair WebSocket engine disabled (API_ENABLE_GRID_WS=0)`

## Best Practices

### 1. Naming Convention
- Use service prefix: `API_`, `BOT_`, `MONITOR_`
- Be consistent across related variables
- Document your naming scheme

### 2. Environment Management
- Production: Enable WebSocket (`=1`)
- Staging: Enable for testing (`=1`) 
- Development: Usually disable (`=0`)

### 3. Security
- Never commit credentials to git
- Use Render's encrypted environment variables
- Rotate API keys regularly

### 4. Monitoring
- Set up alerts for deployment failures
- Monitor startup logs for WebSocket status
- Test rollback procedure regularly

## Troubleshooting

### Variable Not Found
```bash
# Check all environment variables
render env list --service your-service-name

# Verify variable name matches code expectations
grep -n "ENABLE_GRID_WS" api/app.py
```

### Service Won't Start
1. Check build logs for dependency issues
2. Verify start command is correct
3. Test locally with same environment variables

### WebSocket Issues
1. Set `API_ENABLE_GRID_WS=0` to disable
2. Check API still works without WebSocket
3. Review ccxt.pro connection logs

## Support

For Render-specific issues:
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)

For Bottie WebSocket issues:
- Check `GRID_ROLLBACK_SWITCH.md`
- Review startup logs in Render dashboard
- Test with `API_ENABLE_GRID_WS=0` first
