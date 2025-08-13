# Grid WebSocket Rollback Switch

## Overview
The Cross-Pair WebSocket engine includes a built-in rollback switch for safe operation. If `ccxt.pro` experiences issues or the WebSocket engine needs to be disabled, you can safely turn it off without breaking the API.

## Environment Variable Control

### Enable WebSocket Engine (Default)
```bash
export ENABLE_GRID_WS=1
# or
export ENABLE_GRID_WS=true
# or  
export ENABLE_GRID_WS=yes
```

### Disable WebSocket Engine (Safe Mode)
```bash
export ENABLE_GRID_WS=0
# or
export ENABLE_GRID_WS=false
# or
export ENABLE_GRID_WS=no
```

## Behavior

### When Enabled (ENABLE_GRID_WS=1)
- ✅ WebSocket engine starts normally
- ✅ Real-time market data streaming
- ✅ Live grid matrix updates
- ✅ Portfolio and scan asset detection

### When Disabled (ENABLE_GRID_WS=0)
- ⚠️ WebSocket engine is bypassed
- ✅ API endpoints still work (return empty/safe defaults)
- ✅ No crashes or errors
- ✅ Graceful degradation

## API Response Differences

### Grid Matrix Endpoint `/grid/matrix`

**Enabled:**
```json
{
  "rows": ["USDT", "BTC", "ETH"],
  "cols": ["USDT", "BTC", "ETH", "BNB", "ADA"],
  "matrix": {
    "BTC": {
      "ETH": {
        "signal": "BUY",
        "conf": 0.75,
        "last": 0.065,
        "final_prob": 0.72
      }
    }
  },
  "ts": 1692345678
}
```

**Disabled:**
```json
{
  "rows": [],
  "cols": [], 
  "matrix": {},
  "ts": 1692345678
}
```

### Portfolio Assets `/portfolio/assets`

**Enabled:** `{"assets": ["USDT", "BTC", "ETH"]}`  
**Disabled:** `{"assets": []}`

### Scan Assets `/scan/assets`

**Enabled:** `{"assets": ["USDT", "BTC", "ETH", "BNB", "ADA"]}`  
**Disabled:** `{"assets": []}`

## Deployment Scenarios

### Render Environment Variables (Multiple Options)

Render requires unique variable names across services. Use any of these approaches:

#### Option 1: Service-Specific Names
```bash
# For API service (recommended)
API_ENABLE_GRID_WS=1         # Enable production
API_ENABLE_GRID_WS=0         # Emergency rollback

# For main bot service  
BOTTIE_ENABLE_GRID_WS=1      # Enable production
BOTTIE_ENABLE_GRID_WS=0      # Emergency rollback
```

#### Option 2: Environment-Specific Names
```bash
# Production environment
PROD_ENABLE_GRID_WS=1

# Staging environment  
STAGING_ENABLE_GRID_WS=1

# Development environment
DEV_ENABLE_GRID_WS=0
```

#### Option 3: Generic (if no conflicts)
```bash
# Enable (production)
ENABLE_GRID_WS=1

# Disable (emergency rollback)  
ENABLE_GRID_WS=0
```

**Note:** The code automatically checks for variables in this priority order:
1. `API_ENABLE_GRID_WS` (service-specific)
2. `BOTTIE_ENABLE_GRID_WS` (app-specific) 
3. `ENABLE_GRID_WS` (generic fallback)

### Local Development
```bash
# In your .env file
ENABLE_GRID_WS=1

# Quick disable for testing
export ENABLE_GRID_WS=0 && python -m uvicorn api.app:app --reload
```

## Monitoring & Logs

### Startup Logs

**When Enabled:**
```
✅ Cross-pair WebSocket grid engine started
```

**When Disabled:**
```
ℹ️ Cross-pair WebSocket engine disabled (ENABLE_GRID_WS=0)
```

**When Failed:**
```
❌ Cross-pair WS engine start error: [specific error message]
```

## Troubleshooting

### Common Issues Requiring Rollback

1. **ccxt.pro Connection Issues**
   - Set `ENABLE_GRID_WS=0`
   - API continues working without WebSocket features

2. **Exchange API Rate Limits**
   - Temporarily disable with `ENABLE_GRID_WS=0`
   - Re-enable after rate limit reset

3. **Memory/Performance Issues**
   - Disable WebSocket to reduce resource usage
   - Monitor system performance

### Emergency Rollback Procedure

1. **Immediate Disable:**
   ```bash
   # Set environment variable
   export ENABLE_GRID_WS=0
   
   # Restart the API service
   # (method depends on deployment platform)
   ```

2. **Verify Rollback:**
   ```bash
   curl https://your-api.com/grid/matrix
   # Should return: {"rows": [], "cols": [], "matrix": {}, "ts": ...}
   ```

3. **Re-enable When Ready:**
   ```bash
   export ENABLE_GRID_WS=1
   # Restart service
   ```

## Frontend Handling

The dashboard automatically handles the disabled state:

- Empty grid displays gracefully
- No JavaScript errors
- "No data available" messages shown
- All other features continue working

## Production Recommendations

1. **Monitor WebSocket Health:** Check startup logs for engine status
2. **Have Rollback Ready:** Keep `ENABLE_GRID_WS=0` available for quick deployment
3. **Test Both States:** Verify your deployment works with WS both enabled and disabled
4. **Use Gradual Rollout:** Enable on staging first, then production

## Security Notes

- Disabling WebSocket doesn't affect authentication
- All API security remains intact
- No data exposure when disabled
- Safe to toggle in production environments
