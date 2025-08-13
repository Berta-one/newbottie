# 🚀 BOTTIE MAXI GRID DEPLOYMENT CHECKLIST

## 📋 **RENDER (BACKEND) DEPLOYMENT**

### ✅ **Step 1: Verify Requirements**
```bash
# Check requirements.txt already has ccxt-pro
grep "ccxt-pro" requirements.txt
```
**Status:** ✅ Already present

### ✅ **Step 2: Deploy Backend Files to Render**
**Upload/Deploy these files to your Render GitHub repo:**

1. **`api/cross_pairs.py`** ✅ Ready
2. **`api/routes_grid.py`** ✅ Ready  
3. **Updated `api/app.py`** ✅ Ready

**DO NOT deploy to Render:**
- ❌ `web/index.html` (goes to Netlify)
- ❌ `web/style.css` (goes to Netlify)
- ❌ `web/app.js` (goes to Netlify)

### ✅ **Step 3: Environment Variables (Optional)**
Add to Render Environment Variables if you want to customize:
```
ENABLE_GRID_WS=1                  # Set to 0 to disable WebSocket (rollback/safe mode)
GRID_MAX_COLS=60
GRID_STABLES=USDT,USDC,BUSD,DAI
PRIMARY_QUOTE=USDT
TRADE_MIN_CONF=0.55
```

### ✅ **Step 4: Deploy & Monitor Logs**
After Render deployment, check logs for these success messages:
```
✅ Expected Success Messages (when ENABLE_GRID_WS=1):
[WS] Loaded 2000+ markets
[WS] rows(held)=X cols(scan)=Y  
[WS] resolved Z symbols for maxi-grid
✅ Cross-pair WebSocket grid engine started

ℹ️ Safe Mode Message (when ENABLE_GRID_WS=0):
ℹ️ Cross-pair WebSocket engine disabled (ENABLE_GRID_WS=0)

❌ Watch for Error Messages:
❌ Cross-pair WS engine start error: [details]
[WS] fetch_balance failed: [API key issues]
```

### ✅ **Step 5: Test Backend APIs**
```bash
# Test new endpoints work
curl https://bottie-1.onrender.com/grid/matrix
curl https://bottie-1.onrender.com/portfolio/assets
curl https://bottie-1.onrender.com/scan/assets
```

---

## 🌐 **NETLIFY (FRONTEND) DEPLOYMENT**

### ✅ **Step 1: Frontend Files Ready**
**These files have been updated for Netlify deployment:**

1. **`web/index.html`** ✅ Updated with Maxi Grid
2. **`web/style.css`** ✅ Added grid styling  
3. **`web/app.js`** ✅ Added grid JavaScript

**DO NOT deploy to Netlify:**
- ❌ `api/` folder (stays on Render)
- ❌ Backend Python files
- ❌ `requirements.txt`

### ✅ **Step 2: Deploy to Netlify**
1. Upload the `web/` folder contents to Netlify
2. Or sync from your Netlify-connected repository
3. Deploy the updated frontend

### ✅ **Step 3: Test Frontend Integration**
Access your dashboard with API parameter:
```
https://your-netlify-site.netlify.app?api=https://bottie-1.onrender.com
```

**Expected Frontend Behavior:**
- ✅ Maxi Grid appears in dashboard
- ✅ Grid loads within ~2 seconds
- ✅ Shows portfolio assets as rows
- ✅ Shows market assets as columns  
- ✅ Cells display BUY/HOLD/SELL/NA with colors
- ✅ Hover shows detailed tooltips
- ✅ Updates every 15 seconds
- ✅ Timestamp shows "Updated: [time]"

---

## 🧪 **VALIDATION STEPS**

### **Backend Validation (Render)**
```bash
# Check health endpoint
curl https://bottie-1.onrender.com/health

# Check new grid endpoints
curl https://bottie-1.onrender.com/grid/matrix
# Should return: {"rows": [...], "cols": [...], "matrix": {...}, "ts": ...}

curl https://bottie-1.onrender.com/portfolio/assets  
# Should return: {"assets": ["BTC", "ETH", "USDT", ...]}

curl https://bottie-1.onrender.com/scan/assets
# Should return: {"assets": ["USDT", "BTC", "ETH", ...]}
```

### **Frontend Validation (Netlify)**
1. **Load Dashboard:** https://your-site.netlify.app?api=https://bottie-1.onrender.com
2. **Check Grid Loads:** Look for "Cross-Pair Maxi Grid" section
3. **Verify Data:** Grid should populate with BUY/HOLD/SELL cells
4. **Test Tooltips:** Hover over cells to see signal details
5. **Monitor Updates:** Watch timestamp update every 15 seconds
6. **Check Console:** No JavaScript errors in browser console

---

## 🔧 **DEPLOYMENT ARCHITECTURE**

```
┌─────────────────┐    API Calls    ┌─────────────────┐
│   NETLIFY       │ ──────────────> │     RENDER      │
│                 │                 │                 │
│ - index.html    │ <────────────── │ - api/app.py    │
│ - style.css     │   JSON Data     │ - cross_pairs.py│
│ - app.js        │                 │ - routes_grid.py│
│                 │                 │                 │
│ Frontend Only   │                 │  Backend Only   │
└─────────────────┘                 └─────────────────┘
```

**Key Points:**
- 🌐 **Netlify** hosts static files (`web/` folder)
- ⚡ **Render** hosts API and WebSocket engine (`api/` folder)
- 🔗 **Communication** via HTTPS API calls
- 🔄 **Updates** happen independently

---

## 📁 **FILE DEPLOYMENT MATRIX**

| File | Deploy to Render | Deploy to Netlify |
|------|:----------------:|:------------------:|
| `api/cross_pairs.py` | ✅ YES | ❌ NO |
| `api/routes_grid.py` | ✅ YES | ❌ NO |
| `api/app.py` | ✅ YES (updated) | ❌ NO |
| `requirements.txt` | ✅ YES | ❌ NO |
| `web/index.html` | ❌ NO | ✅ YES (updated) |
| `web/style.css` | ❌ NO | ✅ YES (updated) |
| `web/app.js` | ❌ NO | ✅ YES (updated) |

---

## ✅ **SUCCESS CHECKLIST**

### **Render Backend ✅**
- [ ] New files deployed to GitHub/Render
- [ ] Logs show WebSocket connection success
- [ ] Grid APIs return valid JSON data
- [ ] Portfolio detection working
- [ ] No deployment errors

### **Netlify Frontend ✅**  
- [ ] Web files deployed to Netlify
- [ ] Dashboard loads completely
- [ ] Maxi Grid section visible
- [ ] Grid populates with live data
- [ ] Tooltips work on hover
- [ ] Auto-refresh every 15 seconds
- [ ] No console errors

### **Integration ✅**
- [ ] Cross-origin requests work
- [ ] API base parameter works
- [ ] Real-time updates functioning
- [ ] Performance acceptable
- [ ] Mobile responsive

🎉 **Both platforms deployed independently and working together!**
