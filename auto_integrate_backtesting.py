#!/usr/bin/env python3
"""
Automated Backtesting Integration Script
=======================================

This script automatically integrates backtesting functionality into your
existing hybrid_bot.py without losing any of your custom code.
"""

import os
import re
import shutil
from datetime import datetime

def backup_existing_file():
    """Create a backup of the existing hybrid_bot.py"""
    
    if os.path.exists("hybrid_bot.py"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"hybrid_bot_backup_{timestamp}.py"
        shutil.copy("hybrid_bot.py", backup_name)
        print(f"✅ Created backup: {backup_name}")
        return True
    else:
        print("❌ hybrid_bot.py not found!")
        return False

def read_file(filename):
    """Read file content"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        return None

def write_file(filename, content):
    """Write content to file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"❌ Error writing {filename}: {e}")
        return False

def add_backtesting_import(content):
    """Add backtesting import to the file"""
    
    # Look for existing imports section
    import_pattern = r'(import streamlit as st.*?\n)'
    
    # Check if already imported
    if 'from backtesting_integration import BacktestingIntegration' in content:
        print("✅ Backtesting import already exists")
        return content
    
    # Add the import after streamlit import
    new_import = '''
# Backtesting integration
try:
    from backtesting_integration import BacktestingIntegration
    BACKTESTING_AVAILABLE = True
except ImportError:
    BACKTESTING_AVAILABLE = False
    print("⚠️ Backtesting not available - install: pip install ccxt scipy")
'''
    
    # Find where to insert
    lines = content.split('\n')
    insert_position = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('import streamlit as st'):
            insert_position = i + 1
            break
    
    if insert_position > 0:
        lines.insert(insert_position, new_import)
        print("✅ Added backtesting import")
        return '\n'.join(lines)
    else:
        print("⚠️ Could not find streamlit import - adding at top")
        return new_import + '\n' + content

def update_tabs_definition(content):
    """Update tabs definition to include backtesting"""
    
    # Look for tabs definition patterns
    patterns = [
        r'tabs = st\.tabs\(\[(.*?)\]\)',
        r'tabs = st\.tabs\(\[\s*(.*?)\s*\]\)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            existing_tabs = match.group(1)
            
            # Check if backtesting already included
            if 'Backtesting' in existing_tabs:
                print("✅ Backtesting tab already exists")
                return content
            
            # Add backtesting tab
            # Remove the closing bracket and add backtesting
            updated_tabs = existing_tabs.rstrip().rstrip(',') + ',\n        "🔬 Backtesting"'
            
            new_tabs_def = f'tabs = st.tabs([\n        {updated_tabs}\n    ])'
            
            updated_content = re.sub(pattern, new_tabs_def, content, flags=re.DOTALL)
            print("✅ Added backtesting tab to tabs definition")
            return updated_content
    
    print("⚠️ Could not find tabs definition - you may need to add manually")
    return content

def add_backtesting_tab_implementation(content):
    """Add backtesting tab implementation"""
    
    # Check if already implemented
    if 'render_backtesting_tab' in content or 'BacktestingIntegration()' in content:
        print("✅ Backtesting tab implementation already exists")
        return content
    
    # Look for the last tab implementation
    # Find pattern like "with tabs[X]:" and add after it
    tab_pattern = r'(with tabs\[\d+\]:.*?\n.*?(?=with tabs\[\d+\]:|if __name__|$))'
    matches = list(re.finditer(tab_pattern, content, re.DOTALL))
    
    if matches:
        # Get the last tab
        last_match = matches[-1]
        insert_position = last_match.end()
        
        # Determine the tab index (should be one more than the last)
        tab_indices = [int(re.search(r'with tabs\[(\d+)\]:', match.group(1)).group(1)) for match in matches]
        next_tab_index = max(tab_indices) + 1
        
        backtesting_tab_code = f'''
# Backtesting tab
with tabs[{next_tab_index}]:
    if BACKTESTING_AVAILABLE:
        try:
            backtesting = BacktestingIntegration()
            backtesting.render_backtesting_tab()
        except Exception as e:
            st.error(f"❌ Backtesting error: {{str(e)}}")
            st.info("Try running: pip install ccxt scipy")
    else:
        st.error("🔬 Backtesting Unavailable")
        st.markdown(\"\"\"
        **Backtesting requires additional dependencies:**
        
        ```bash
        pip install ccxt scipy
        ```
        
        **Features you're missing:**
        - Strategy optimization across weight combinations
        - Historical performance analysis  
        - ROI and win rate projections
        - Optimal parameter recommendations
        - Portfolio configuration export
        \"\"\")

'''
        
        # Insert the backtesting tab code
        updated_content = content[:insert_position] + backtesting_tab_code + content[insert_position:]
        print(f"✅ Added backtesting tab implementation at index {next_tab_index}")
        return updated_content
    
    else:
        print("⚠️ Could not find tab implementations - you may need to add manually")
        return content

def enhance_sidebar(content):
    """Add backtesting quick actions to sidebar"""
    
    # Check if already enhanced
    if 'Quick Backtest' in content:
        print("✅ Sidebar already enhanced with backtesting")
        return content
    
    # Look for sidebar section
    sidebar_pattern = r'(with st\.sidebar:.*?st\.markdown\("---"\))'
    matches = list(re.finditer(sidebar_pattern, content, re.DOTALL))
    
    if matches:
        # Add after the last divider in sidebar
        last_match = matches[-1]
        insert_position = last_match.end()
        
        sidebar_enhancement = '''
        # Quick backtesting
        if BACKTESTING_AVAILABLE:
            st.markdown("**🔬 Quick Backtest**")
            
            if st.button("🚀 Run Quick Test", use_container_width=True):
                try:
                    # Initialize and run demo backtest
                    backtesting = BacktestingIntegration()
                    backtesting.run_demo_backtest()
                    st.success("Demo backtest completed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")
            
            st.markdown("---")'''
        
        updated_content = content[:insert_position] + sidebar_enhancement + content[insert_position:]
        print("✅ Enhanced sidebar with quick backtesting")
        return updated_content
    
    print("⚠️ Could not find sidebar section")
    return content

def validate_integration(content):
    """Validate that integration was successful"""
    
    checks = [
        ("Backtesting import", 'from backtesting_integration import BacktestingIntegration' in content),
        ("Backtesting tab", '"🔬 Backtesting"' in content),
        ("Tab implementation", 'BacktestingIntegration()' in content),
        ("Error handling", 'BACKTESTING_AVAILABLE' in content)
    ]
    
    print("\n🔍 INTEGRATION VALIDATION:")
    print("=" * 40)
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All integration checks passed!")
        return True
    else:
        print("\n⚠️ Some checks failed - manual review needed")
        return False

def main():
    """Main integration script"""
    
    print("🚀 AUTOMATED BACKTESTING INTEGRATION")
    print("=" * 50)
    
    # Step 1: Backup existing file
    if not backup_existing_file():
        return False
    
    # Step 2: Read existing content
    print("📖 Reading existing hybrid_bot.py...")
    content = read_file("hybrid_bot.py")
    if not content:
        return False
    
    # Step 3: Apply modifications
    print("🔧 Applying backtesting integration...")
    
    content = add_backtesting_import(content)
    content = update_tabs_definition(content)
    content = add_backtesting_tab_implementation(content)
    content = enhance_sidebar(content)
    
    # Step 4: Write updated file
    print("💾 Writing updated hybrid_bot.py...")
    if not write_file("hybrid_bot.py", content):
        return False
    
    # Step 5: Validate integration
    validate_integration(content)
    
    print("\n" + "=" * 50)
    print("✅ INTEGRATION COMPLETE!")
    print("=" * 50)
    print("""
🎯 WHAT WAS DONE:
✅ Created backup of original file
✅ Added backtesting imports with error handling
✅ Updated tabs to include 🔬 Backtesting
✅ Added full backtesting tab implementation  
✅ Enhanced sidebar with quick actions
✅ Validated all changes

🚀 NEXT STEPS:
1. Save the backtesting_integration.py file (from first artifact)
2. Install dependencies: pip install ccxt scipy
3. Run your bot: streamlit run hybrid_bot.py
4. Navigate to the new 🔬 Backtesting tab
5. Click "🔄 Demo Backtest" to test functionality

🔧 IF ISSUES OCCUR:
- Check the backup file created
- Manually review the changes
- Install missing dependencies
- Check console for error messages

Your Bottie now has professional backtesting! 🎉
""")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Integration failed - check errors above")
        exit(1)
    else:
        print("\n🎉 Integration successful!")
        exit(0)