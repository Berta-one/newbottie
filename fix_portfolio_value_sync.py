#!/usr/bin/env python3
"""
Portfolio Value Synchronization Fix - CORRECTED VERSION
Ensures consistent portfolio values across all dashboard tabs
"""

import os
import sys
from pathlib import Path
from datetime import datetime


def create_unified_portfolio_calculator():
    """Create a unified portfolio value calculator"""

    calculator_code = """#!/usr/bin/env python3
'''
Unified Portfolio Value Calculator
Ensures consistent portfolio calculations across all tabs
'''

from datetime import datetime

class UnifiedPortfolioCalculator:
    '''Single source of truth for portfolio value calculations'''
    
    def __init__(self):
        self._cached_portfolio = {}
        self._cached_total_usd = 0.0
        self._cached_total_gbp = 0.0
        self._cache_timestamp = None
        self._gbp_rate = 0.79  # Default fallback
    
    def get_gbp_exchange_rate(self):
        '''Get current GBP exchange rate with caching'''
        try:
            import requests
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            self._gbp_rate = response.json()['rates']['GBP']
            return self._gbp_rate
        except:
            return self._gbp_rate  # Use cached/fallback rate
    
    def calculate_portfolio_totals(self, portfolio_data):
        '''
        Calculate consistent portfolio totals
        
        Args:
            portfolio_data: Dictionary of portfolio assets
            
        Returns:
            tuple: (total_usd, total_gbp, gbp_rate)
        '''
        if not portfolio_data:
            return 0.0, 0.0, self._gbp_rate
        
        # Calculate total USD value
        total_usd = 0.0
        
        for asset, data in portfolio_data.items():
            if isinstance(data, dict):
                # Handle different data structures
                if 'usd_value' in data:
                    total_usd += float(data['usd_value'])
                elif 'value' in data and 'price' in data and 'balance' in data:
                    total_usd += float(data['balance']) * float(data['price'])
                elif 'market_value' in data:
                    total_usd += float(data['market_value'])
                elif 'Value (USD)' in data:
                    # Handle DataFrame-like structure
                    usd_str = str(data['Value (USD)']).replace('$', '').replace(',', '')
                    try:
                        total_usd += float(usd_str)
                    except:
                        continue
        
        # Get current GBP rate and calculate GBP total
        gbp_rate = self.get_gbp_exchange_rate()
        total_gbp = total_usd * gbp_rate
        
        # Cache results
        self._cached_total_usd = total_usd
        self._cached_total_gbp = total_gbp
        self._cache_timestamp = datetime.now()
        
        return total_usd, total_gbp, gbp_rate
    
    def get_portfolio_metrics(self, portfolio_data):
        '''Get comprehensive portfolio metrics'''
        total_usd, total_gbp, gbp_rate = self.calculate_portfolio_totals(portfolio_data)
        
        return {
            'total_usd': total_usd,
            'total_gbp': total_gbp,
            'gbp_rate': gbp_rate,
            'asset_count': len(portfolio_data) if portfolio_data else 0,
            'largest_holding_pct': self._get_largest_holding_percentage(portfolio_data, total_usd),
            'formatted_usd': f"${total_usd:,.2f}",
            'formatted_gbp': f"£{total_gbp:,.2f}"
        }
    
    def _get_largest_holding_percentage(self, portfolio_data, total_usd):
        '''Calculate largest holding percentage'''
        if not portfolio_data or total_usd == 0:
            return 0.0
            
        max_value = 0.0
        for asset, data in portfolio_data.items():
            if isinstance(data, dict):
                if 'usd_value' in data:
                    asset_value = float(data['usd_value'])
                elif 'market_value' in data:
                    asset_value = float(data['market_value'])
                else:
                    continue
                    
                if asset_value > max_value:
                    max_value = asset_value
        
        return (max_value / total_usd * 100) if total_usd > 0 else 0.0
    
    def format_portfolio_for_display(self, portfolio_data):
        '''Format portfolio data for consistent display'''
        if not portfolio_data:
            return []
        
        total_usd, total_gbp, gbp_rate = self.calculate_portfolio_totals(portfolio_data)
        formatted_data = []
        
        for asset, data in portfolio_data.items():
            if isinstance(data, dict):
                # Extract values safely
                balance = float(data.get('balance', 0))
                price_usd = float(data.get('price_usd', data.get('price', 0)))
                usd_value = float(data.get('usd_value', balance * price_usd))
                change_24h = float(data.get('change_24h', 0))
                
                formatted_data.append({
                    'Asset': asset,
                    'Balance': f"{balance:.8f}".rstrip('0').rstrip('.'),
                    'Price (USD)': f"${price_usd:.4f}",
                    'Value (USD)': f"${usd_value:.2f}",
                    'Value (GBP)': f"£{usd_value * gbp_rate:.2f}",
                    '24h Change': f"{change_24h:.2f}%",
                    'Percentage': f"{(usd_value / total_usd * 100):.1f}%" if total_usd > 0 else "0.0%"
                })
        
        return formatted_data

# Global calculator instance
portfolio_calculator = UnifiedPortfolioCalculator()

# Convenience functions for easy import
def get_portfolio_totals(portfolio_data):
    '''Get portfolio totals using unified calculator'''
    return portfolio_calculator.calculate_portfolio_totals(portfolio_data)

def get_portfolio_metrics(portfolio_data):
    '''Get portfolio metrics using unified calculator'''
    return portfolio_calculator.get_portfolio_metrics(portfolio_data)

def format_portfolio_display(portfolio_data):
    '''Format portfolio for display using unified calculator'''
    return portfolio_calculator.format_portfolio_for_display(portfolio_data)

def debug_portfolio_values(portfolio_data, location="unknown"):
    '''Debug portfolio value calculations'''
    print(f"\\n=== PORTFOLIO DEBUG [{location}] ===")
    
    if not portfolio_data:
        print("❌ Portfolio data is empty")
        return 0.0
    
    total_debug = 0.0
    for asset, data in portfolio_data.items():
        if isinstance(data, dict):
            usd_value = data.get('usd_value', 0)
            print(f"{asset}: ${usd_value:.2f}")
            total_debug += float(usd_value)
    
    print(f"🔢 Total calculated: ${total_debug:.2f}")
    print("=" * 40)
    
    return total_debug
"""

    # Save the calculator
    with open("unified_portfolio_calculator.py", "w", encoding="utf-8") as f:
        f.write(calculator_code)

    print("✅ Created unified_portfolio_calculator.py")


def create_quick_fix_patch():
    """Create a simple patch file to apply to hybrid_bot.py"""

    patch_code = """#!/usr/bin/env python3
'''
Quick Portfolio Value Fix Patch
Apply this to fix portfolio value synchronization
'''

import os
import re
from pathlib import Path

def apply_portfolio_fix():
    '''Apply portfolio value synchronization fix'''
    
    print("🔧 Applying Portfolio Value Fix...")
    
    # Files to patch
    files_to_patch = ["hybrid_bot.py", "portfolio_trading_bot.py", "bot_controller.py"]
    
    for filename in files_to_patch:
        if Path(filename).exists():
            print(f"📄 Patching {filename}...")
            
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Backup original
                backup_name = f"{filename}.backup"
                with open(backup_name, "w", encoding="utf-8") as f:
                    f.write(content)
                
                # Add import if not present
                if "from unified_portfolio_calculator import" not in content:
                    import_line = "from unified_portfolio_calculator import get_portfolio_totals, debug_portfolio_values\\n"
                    content = import_line + content
                    print(f"  ✅ Added unified calculator import")
                
                # Look for portfolio calculation patterns
                patterns_fixed = []
                
                # Pattern 1: sum(coin['usd_value'] for coin in portfolio.values())
                old_pattern1 = r"total_usd\s*=\s*sum\(coin\['usd_value'\]\s*for\s*coin\s*in\s*portfolio\.values\(\)\)"
                if re.search(old_pattern1, content):
                    new_calc = "total_usd, total_gbp, gbp_rate = get_portfolio_totals(portfolio)"
                    content = re.sub(old_pattern1, new_calc, content)
                    patterns_fixed.append("sum() calculation")
                
                # Pattern 2: Individual total_gbp calculations
                old_pattern2 = r"total_gbp\s*=\s*total_usd\s*\*\s*gbp_rate"
                if re.search(old_pattern2, content):
                    new_calc = "# total_gbp calculated above with get_portfolio_totals()"
                    content = re.sub(old_pattern2, new_calc, content)
                    patterns_fixed.append("GBP calculation")
                
                # Write patched file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                
                if patterns_fixed:
                    print(f"  ✅ Fixed: {', '.join(patterns_fixed)}")
                else:
                    print(f"  ✅ No patterns to fix found")
                    
            except Exception as e:
                print(f"  ❌ Error patching {filename}: {e}")
        else:
            print(f"  ⚠️ {filename} not found")
    
    print("\\n🎉 Portfolio fix applied!")
    print("\\n📋 Next steps:")
    print("1. Test your dashboard: streamlit run hybrid_bot.py")
    print("2. Check both Dashboard and Portfolio tabs show same value")
    print("3. If issues persist, check debug output in console")

if __name__ == "__main__":
    apply_portfolio_fix()
"""

    with open("apply_portfolio_fix.py", "w", encoding="utf-8") as f:
        f.write(patch_code)

    print("✅ Created apply_portfolio_fix.py")


def create_manual_fix_instructions():
    """Create manual fix instructions"""

    instructions = """
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
"""

    with open("PORTFOLIO_FIX_INSTRUCTIONS.md", "w", encoding="utf-8") as f:
        f.write(instructions)

    print("✅ Created PORTFOLIO_FIX_INSTRUCTIONS.md")


def main():
    """Main function to create all portfolio sync fixes"""
    print("🔧 Portfolio Value Synchronization Fix - CORRECTED")
    print("=" * 60)

    print("\\n1. Creating unified portfolio calculator...")
    create_unified_portfolio_calculator()

    print("\\n2. Creating quick fix patch...")
    create_quick_fix_patch()

    print("\\n3. Creating manual instructions...")
    create_manual_fix_instructions()

    print("\\n" + "=" * 60)
    print("🎉 PORTFOLIO SYNC FIX COMPLETED!")
    print("=" * 60)

    print("\\n🚀 Quick Fix Steps:")
    print("1. Run: python apply_portfolio_fix.py")
    print("2. Test: streamlit run hybrid_bot.py")
    print("3. Check both Dashboard and Portfolio tabs")

    print("\\n📋 Files Created:")
    print("✅ unified_portfolio_calculator.py - Single source of truth")
    print("✅ apply_portfolio_fix.py - Automated patcher")
    print("✅ PORTFOLIO_FIX_INSTRUCTIONS.md - Manual instructions")

    print("\\n🎯 This will sync portfolio values across all tabs!")


if __name__ == "__main__":
    main()
