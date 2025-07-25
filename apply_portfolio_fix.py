 -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Quick Portfolio Value Fix Patch
Apply this to fix portfolio value synchronization
"""

import os
import re
from pathlib import Path


def apply_portfolio_fix():
    """Apply portfolio value synchronization fix"""

    print("ðŸ”§ Applying Portfolio Value Fix...")

    # Files to patch
    files_to_patch = ["hybrid_bot.py", "portfolio_trading_bot.py", "bot_controller.py"]

    for filename in files_to_patch:
        if Path(filename).exists():
            print(f"ðŸ“„ Patching {filename}...")

            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()

                # Backup original
                backup_name = f"{filename}.backup"
                with open(backup_name, "w", encoding="utf-8") as f:
                    f.write(content)

                # Add import if not present
                if "from unified_portfolio_calculator import" not in content:
                    import_line = "from unified_portfolio_calculator import get_portfolio_totals, debug_portfolio_values\n"
                    content = import_line + content
                    print(f"  âœ… Added unified calculator import")

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
                    new_calc = (
                        "# total_gbp calculated above with get_portfolio_totals()"
                    )
                    content = re.sub(old_pattern2, new_calc, content)
                    patterns_fixed.append("GBP calculation")

                # Write patched file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)

                if patterns_fixed:
                    print(f"  âœ… Fixed: {', '.join(patterns_fixed)}")
                else:
                    print(f"  âœ… No patterns to fix found")

            except Exception as e:
                print(f"  âŒ Error patching {filename}: {e}")
        else:
            print(f"  âš ï¸ {filename} not found")

    print("\nðŸŽ‰ Portfolio fix applied!")
    print("\nðŸ“‹ Next steps:")
    print("1. Test your dashboard: streamlit run hybrid_bot.py")
    print("2. Check both Dashboard and Portfolio tabs show same value")
    print("3. If issues persist, check debug output in console")


if __name__ == "__main__":
    apply_portfolio_fix()

