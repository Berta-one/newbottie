# 🔧 Bottie Debug & Fix Guide

## 🚨 **Zero Positions & Equity Issue**

You're seeing **0 positions** and **0 equity** because there are several potential issues:

### **1. Portfolio Initialization Issues**

The system has two separate tracking systems:
- **API Portfolio Loop** (in `api/app.py`) - tracks exchange balances  
- **Trade Executor** (in `engine/executor.py`) - executes paper/live trades

### **2. Potential Root Causes**

#### **A. Exchange Connection Issues**
```python
# In portfolio_loop(), if API keys fail:
bal = _exchange.fetch_balance(params={}) if (API_KEY and API_SECRET) else {"total": {}}
```

#### **B. Geo-Restrictions**
```python
# Common error in logs:
"Geo-restricted by venue for authenticated calls."
```

#### **C. Zero Exchange Balances**
- Your exchange account might actually have $0
- No assets = no equity calculation

#### **D. Execution Runtime Disabled**
```python
# Check if this is False:
EXECUTION_RUNTIME_ENABLED = False
```

### **3. Quick Diagnostics**

#### **Test 1: Check Render Logs**
Look for these error patterns:
- `"Exchange error"`
- `"Geo-restricted"`
- `"EXECUTION_RUNTIME_ENABLED"`
- `"snapshot | equity=0.00"`

#### **Test 2: API Health Check**
```bash
curl https://bottie-1.onrender.com/health
curl https://bottie-1.onrender.com/trading/status
```

#### **Test 3: Manual Capital Injection**
If running paper mode, the system should initialize with `EQUITY_START`.

### **4. Immediate Fixes**

#### **Fix A: Enable Execution Runtime**
```bash
curl -X POST https://bottie-1.onrender.com/execution/enable
```

#### **Fix B: Check Trading Status**
```bash
curl https://bottie-1.onrender.com/trading/status
```

#### **Fix C: Manual Paper Trading Setup**
If no real balances, force paper mode initialization.

### **5. Environment Variables to Check on Render**

Required for live trading:
```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_secret
EQUITY_START=10000
EXECUTION_RUNTIME_ENABLED=true
BOT_MODE=paper  # or "live"
```

### **6. Debug Commands**

Run these to diagnose:

```bash
# Check if execution is enabled
curl https://bottie-1.onrender.com/trading/status

# Enable execution if disabled
curl -X POST https://bottie-1.onrender.com/execution/enable

# Check portfolio data
curl https://bottie-1.onrender.com/portfolio/current

# Check recent logs
curl https://bottie-1.onrender.com/logs
```

### **7. Expected Behavior**

Once fixed, you should see:
- **Equity > 0** (either real balance or paper starting capital)
- **Positions** appearing as trades execute
- **Logs** showing `"snapshot | equity=X.XX positions=N"`

### **8. Next Steps**

1. **Check Render logs** for error messages
2. **Verify environment variables** are set correctly
3. **Test API endpoints** manually
4. **Enable execution runtime** if disabled
5. **Monitor logs** for trading activity

The system is complex with multiple components, but the core issue is likely either:
- **Execution disabled**
- **Exchange connection failure** 
- **Zero starting capital in paper mode**

Let me know what you find in the Render logs! 🔍
