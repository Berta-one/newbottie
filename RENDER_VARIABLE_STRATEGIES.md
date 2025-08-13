# Render Environment Variable Strategies

## Current Implementation (OR Logic)
The current code checks variables in this order and enables if ANY are true:
1. `API_ENABLE_GRID_WS=1` OR  
2. `BOTTIE_ENABLE_GRID_WS=1` OR
3. `ENABLE_GRID_WS=1` (default)

**Pros:** Flexible, backward compatible
**Cons:** Hard to disable if multiple variables are set

## Alternative: Service-Specific Only

If you want each service to ONLY check its own variable:

### Option A: API Service Only Checks API Variable

```python
# In api/app.py - only check API-specific variable
enable_grid_ws = os.getenv("API_ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")

if enable_grid_ws:
    # Start WebSocket
    add_log("✅ Cross-pair WebSocket grid engine started")
else:
    add_log("ℹ️ Cross-pair WebSocket engine disabled (API_ENABLE_GRID_WS=0)")
```

### Option B: Bot Service Only Checks Bot Variable

```python  
# In headless_bot.py - only check bot-specific variable
enable_grid_ws = os.getenv("BOTTIE_ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")

if enable_grid_ws:
    # Start WebSocket
    print("✅ Bot WebSocket grid engine started")
else:
    print("ℹ️ Bot WebSocket engine disabled (BOTTIE_ENABLE_GRID_WS=0)")
```

## Recommended Render Setup

### For Clean Separation (Recommended)

#### API Service Environment Variables:
```bash
API_ENABLE_GRID_WS=1
API_KEY=your_binance_api_key
API_SECRET=your_binance_secret
API_CLAUDE_KEY=your_claude_key
```

#### Bot Service Environment Variables:
```bash
BOT_ENABLE_GRID_WS=1  
BOT_API_KEY=your_binance_api_key
BOT_API_SECRET=your_binance_secret
BOT_CLAUDE_KEY=your_claude_key
```

#### Monitor Service Environment Variables:
```bash
MONITOR_ENABLE_GRID_WS=0  # Usually disabled
MONITOR_API_KEY=your_readonly_key
MONITOR_API_SECRET=your_readonly_secret
```

### Emergency Rollback Procedure

1. **API Service Issue:** Set `API_ENABLE_GRID_WS=0`
2. **Bot Service Issue:** Set `BOT_ENABLE_GRID_WS=0`  
3. **Global Issue:** Set all to `0`

### Testing Your Variable Setup

```bash
# Test API service locally
export API_ENABLE_GRID_WS=1
python -m uvicorn api.app:app --reload

# Test bot service locally  
export BOT_ENABLE_GRID_WS=1
python headless_bot.py

# Test rollback
export API_ENABLE_GRID_WS=0
export BOT_ENABLE_GRID_WS=0
```

## Which Approach Should You Use?

### Use Current OR Logic If:
- You want maximum flexibility
- You have simple deployment (1-2 services)
- You want backward compatibility

### Use Service-Specific Only If:  
- You have multiple services on Render
- You want clean separation of concerns
- You want precise control over each service
- You want to avoid variable name conflicts

## Implementation Choice

Would you like me to:

1. **Keep current OR logic** (flexible but can conflict)
2. **Switch to service-specific only** (clean separation)
3. **Provide both options** (you choose per service)

Let me know which approach works best for your Render deployment!
