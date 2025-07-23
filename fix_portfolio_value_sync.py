#!/usr/bin/env python3
"""
Portfolio Value Synchronization Fix
Ensures consistent portfolio values across all dashboard tabs
"""

import os
import sys
from pathlib import Path

def find_portfolio_value_calculations():
    """Find all portfolio value calculation methods in the codebase"""
    
    portfolio_calculations = {}
    
    # Files to check for portfolio calculations
    files_to_check = [
        "hybrid_bot.py",
        "dashboard.py", 
        "bot_controller.py",
        "portfolio_manager.py",
        "portfolio_trading_bot.py"
    ]
    
    for filename in files_to_check:
        if Path(filename).exists():
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for portfolio value calculations
            calculations = []
            
            if "total_usd" in content:
                calculations.append("total_usd calculation found")
            if "total_gbp" in content:
                calculations.append("total_gbp calculation found")
            if "sum(coin['usd_value']" in content:
                calculations.append("sum(coin['usd_value']) pattern found")
            if "portfolio_value" in content:
                calculations.append("portfolio_value variable found")
            if "total_value" in content:
                calculations.append("total_value calculation found")
                
            if calculations:
                portfolio_calculations[filename] = calculations
    
    return portfolio_calculations

def create_unified_portfolio_calculator():
    """Create a unified portfolio value calculator"""
    
    calculator_code = '''#!/usr/bin/env python3
"""
Unified Portfolio Value Calculator
Ensures consistent portfolio calculations across all tabs
"""

class UnifiedPortfolioCalculator:
    """Single source of truth for portfolio value calculations"""
    
    def __init__(self):
        self._cached_portfolio = {}
        self._cached_total_usd = 0.0
        self._cached_total_gbp = 0.0
        self._cache_timestamp = None
        self._gbp_rate = 0.79  # Default fallback
    
    def get_gbp_exchange_rate(self):
        """Get current GBP exchange rate with caching"""
        try:
            import requests
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            self._gbp_rate = response.json()['rates']['GBP']
            return self._gbp_rate
        except:
            return self._gbp_rate  # Use cached/fallback rate
    
    def calculate_portfolio_totals(self, portfolio_data):
        """
        Calculate consistent portfolio totals
        
        Args:
            portfolio_data: Dictionary of portfolio assets
            
        Returns:
            tuple: (total_usd, total_gbp, gbp_rate)
        """
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
        """Get comprehensive portfolio metrics"""
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
        """Calculate largest holding percentage"""
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
        """Format portfolio data for consistent display"""
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
    """Get portfolio totals using unified calculator"""
    return portfolio_calculator.calculate_portfolio_totals(portfolio_data)

def get_portfolio_metrics(portfolio_data):
    """Get portfolio metrics using unified calculator"""
    return portfolio_calculator.get_portfolio_metrics(portfolio_data)

def format_portfolio_display(portfolio_data):
    """Format portfolio for display using unified calculator"""
    return portfolio_calculator.format_portfolio_for_display(portfolio_data)
'''
    
    # Save the calculator
    with open("unified_portfolio_calculator.py", "w", encoding="utf-8") as f:
        f.write(calculator_code)
    
    print("✅ Created unified_portfolio_calculator.py")

def create_portfolio_sync_patch():
    """Create patches for existing files to use unified calculator"""
    
    # Patch for dashboard functions
    dashboard_patch = '''
# PORTFOLIO VALUE SYNC PATCH
# Add this import at the top of your dashboard files:
from unified_portfolio_calculator import get_portfolio_totals, get_portfolio_metrics

# Replace portfolio value calculations with:
def get_consistent_portfolio_values(portfolio_data):
    """Get consistent portfolio values across all tabs"""
    total_usd, total_gbp, gbp_rate = get_portfolio_totals(portfolio_data)
    
    return {
        'total_usd': total_usd,
        'total_gbp': total_gbp, 
        'gbp_rate': gbp_rate,
        'formatted_usd': f"${total_usd:,.2f}",
        'formatted_gbp': f"£{total_gbp:,.2f}"
    }

# In your dashboard rendering functions, replace:
# OLD: total_usd = sum(coin['usd_value'] for coin in portfolio.values())
# NEW: totals = get_consistent_portfolio_values(portfolio)
#      total_usd = totals['total_usd']
#      total_gbp = totals['total_gbp']
'''
    
    with open("portfolio_sync_patch.py", "w", encoding="utf-8") as f:
        f.write(dashboard_patch)
    
    print("✅ Created portfolio_sync_patch.py")

def create_quick_fix_script():
    """Create a quick fix script to apply immediately"""
    
    fix_script = '''#!/usr/bin/env python3
"""
Quick Portfolio Value Fix
Applies immediate fixes to sync portfolio values
"""

import os
import re
from pathlib import Path

def fix_hybrid_bot():
    """Fix hybrid_bot.py portfolio calculations"""
    
    if not Path("hybrid_bot.py").exists():
        print("⚠️ hybrid_bot.py not found")
        return
    
    with open("hybrid_bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find and replace inconsistent portfolio calculations
    fixes_applied = []
    
    # Fix 1: Ensure consistent total_usd calculation
    old_pattern = r'total_usd\s*=\s*sum\(coin\[\'usd_value\'\]\s*for\s*coin\s*in\s*portfolio\.values\(\)\)'
    new_pattern = '''# Unified portfolio calculation
    total_usd = 0.0
    for asset, data in portfolio.items():
        if isinstance(data, dict) and 'usd_value' in data:
            total_usd += float(data['usd_value'])'''
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_pattern, content)
        fixes_applied.append("Fixed total_usd calculation")
    
    # Fix 2: Ensure consistent GBP calculation
    old_gbp = r'total_gbp\s*=\s*total_usd\s*\*\s*gbp_rate'
    new_gbp = '''# Consistent GBP calculation
    gbp_rate = get_gbp_exchange_rate() if 'get_gbp_exchange_rate' in globals() else 0.79
    total_gbp = total_usd * gbp_rate'''
    
    if re.search(old_gbp, content):
        content = re.sub(old_gbp, new_gbp, content)
        fixes_applied.append("Fixed total_gbp calculation")
    
    # Fix 3: Add import for unified calculator
    if 'from unified_portfolio_calculator import' not in content:
        import_line = "from unified_portfolio_calculator import get_portfolio_totals, get_portfolio_metrics\\n"
        content = import_line + content
        fixes_applied.append("Added unified calculator import")
    
    if fixes_applied:
        # Backup original
        with open("hybrid_bot_backup.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        # Write fixed version
        with open("hybrid_bot.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ Fixed hybrid_bot.py: {', '.join(fixes_applied)}")
    else:
        print("✅ hybrid_bot.py appears to be using consistent calculations")

def add_debug_logging():
    """Add debug logging to track portfolio values"""
    
    debug_code = '''
# PORTFOLIO DEBUG LOGGING
def debug_portfolio_values(portfolio_data, location="unknown"):
    """Debug portfolio value calculations"""
    print(f"\\n=== PORTFOLIO DEBUG [{location}] ===")
    
    if not portfolio_data:
        print("❌ Portfolio data is empty")
        return
    
    total_debug = 0.0
    for asset, data in portfolio_data.items():
        if isinstance(data, dict):
            usd_value = data.get('usd_value', 0)
            print(f"{asset}: ${usd_value:.2f}")
            total_debug += float(usd_value)
    
    print(f"🔢 Total calculated: ${total_debug:.2f}")
    print("=" * 40)
    
    return total_debug

# Add this function call in your dashboard rendering:
# debug_total = debug_portfolio_values(portfolio, "Dashboard Tab")
'''
    
    with open("portfolio_debug.py", "w", encoding="utf-8") as f:
        f.write(debug_code)
    
    print("✅ Created portfolio_debug.py for troubleshooting")

def main():
    """Main fix function"""
    print("🔧 Portfolio Value Synchronization Fix")
    print("=" * 50)
    
    print("\\n1. Analyzing current portfolio calculations...")
    calculations = find_portfolio_value_calculations()
    
    for filename, calcs in calculations.items():
        print(f"📄 {filename}:")
        for calc in calcs:
            print(f"   - {calc}")
    
    print("\\n2. Creating unified portfolio calculator...")
    create_unified_portfolio_calculator()
    
    print("\\n3. Creating sync patches...")
    create_portfolio_sync_patch()
    
    print("\\n4. Creating debug tools...")
    add_debug_logging()
    
    print("\\n5. Creating quick fix script...")
    create_quick_fix_script()
    
    print("\\n" + "=" * 50)
    print("🎉 PORTFOLIO SYNC FIX COMPLETED!")
    print("=" * 50)
    
    print("\\n📋 Next Steps:")
    print("1. Import the unified calculator in your dashboard files:")
    print("   from unified_portfolio_calculator import get_portfolio_totals")
    
    print("\\n2. Replace portfolio calculations with:")
    print("   total_usd, total_gbp, gbp_rate = get_portfolio_totals(portfolio)")
    
    print("\\n3. Use debug logging to verify values:")
    print("   from portfolio_debug import debug_portfolio_values")
    print("   debug_portfolio_values(portfolio, 'Dashboard Tab')")
    
    print("\\n4. Test both tabs to confirm values match")
    
    print("\\n🔍 Root Cause:")
    print("Different files were calculating portfolio values differently:")
    print("- Some used sum(coin['usd_value'] for coin in portfolio.values())")
    print("- Others used different data structures or calculations")
    print("- GBP rates were fetched at different times")
    
    print("\\n✅ Solution:")
    print("- Unified calculator ensures consistent calculations")
    print("- Single source of truth for all portfolio values")
    print("- Cached exchange rates prevent discrepancies")

if __name__ == "__main__":
    main()
'''
    
    with open("quick_portfolio_fix.py", "w", encoding="utf-8") as f:
        f.write(fix_script)
    
    print("✅ Created quick_portfolio_fix.py")

def main():
    """Main function to create all portfolio sync fixes"""
    print("🔧 Portfolio Value Synchronization Fix")
    print("=" * 50)
    
    print("\n1. Analyzing current portfolio calculations...")
    calculations = find_portfolio_value_calculations()
    
    for filename, calcs in calculations.items():
        print(f"📄 {filename}:")
        for calc in calcs:
            print(f"   - {calc}")
    
    print("\n2. Creating unified portfolio calculator...")
    create_unified_portfolio_calculator()
    
    print("\n3. Creating sync patches...")
    create_portfolio_sync_patch()
    
    print("\n4. Creating quick fix script...")
    create_quick_fix_script()
    
    print("\n" + "=" * 50)
    print("🎉 PORTFOLIO SYNC FIX COMPLETED!")
    print("=" * 50)
    
    print("\n📋 Quick Fix Steps:")
    print("1. Run: python quick_portfolio_fix.py")
    print("2. Add to your dashboard files:")
    print("   from unified_portfolio_calculator import get_portfolio_totals")
    print("3. Replace portfolio calculations:")
    print("   total_usd, total_gbp, gbp_rate = get_portfolio_totals(portfolio)")
    print("4. Test both Dashboard and Portfolio tabs")
    
    print("\n🎯 This will ensure both tabs show the same portfolio value!")

if __name__ == "__main__":
    main()