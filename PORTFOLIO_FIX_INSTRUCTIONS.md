
# MANUAL PORTFOLIO VALUE FIX INSTRUCTIONS

## Problem:
Dashboard tab shows portfolio value as zero, while Portfolio tab shows correct value.

## Root Cause:
Different files calculate portfolio values using different methods and data structures.

## Solution:

### Step 1: Add Unified Calculator Import
Add this line to the TOP of hybrid_bot.py:

```python
from unified_portfolio_calculator import get_portfolio_totals, debug_portfolio_values
```

### Step 2: Replace Portfolio Calculations
Find lines that look like this:
```python
# OLD - Replace this
total_usd = sum(coin['usd_value'] for coin in portfolio.values())
total_gbp = bot.get_portfolio_value_gbp(total_usd)
```

Replace with:
```python
# NEW - Use this instead
total_usd, total_gbp, gbp_rate = get_portfolio_totals(portfolio)
```

### Step 3: Add Debug Logging (Temporary)
Add this line after portfolio calculations to debug:
```python
debug_total = debug_portfolio_values(portfolio, "Dashboard Tab")
```

### Step 4: Test
1. Run: streamlit run hybrid_bot.py
2. Check Dashboard tab - should now show correct portfolio value
3. Compare with Portfolio tab - values should match
4. Remove debug logging once confirmed working

## Quick Test Commands:
```bash
# 1. Apply the fix
python apply_portfolio_fix.py

# 2. Test dashboard
streamlit run hybrid_bot.py

# 3. Check both tabs show same value
```

## If Still Zero:
1. Check console for debug output
2. Verify portfolio data structure
3. Ensure Binance API is working
4. Check if USE_TESTNET vs LIVE mode issue
