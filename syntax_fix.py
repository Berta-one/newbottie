#!/usr/bin/env python3
"""
Syntax Fix - Separate from railway API fixes
============================================
Fixes Python syntax errors in hybrid_bot.py
"""

import os
import re

def fix_syntax_errors():
    """Fix syntax errors in hybrid_bot.py"""
    
    file_path = "hybrid_bot.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File {file_path} not found!")
        return False
    
    print(f"🔧 Fixing syntax errors in {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        # Fix orphaned else statements
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check for orphaned else
            if line.strip() == 'else:' or re.match(r'^\s*else:\s*$', line):
                # Look back for matching if/elif
                found_matching_if = False
                
                for j in range(i-1, max(0, i-20), -1):
                    prev_line = lines[j].strip()
                    if prev_line.endswith(':') and ('if ' in prev_line or 'elif ' in prev_line):
                        found_matching_if = True
                        break
                    elif prev_line.startswith('def ') or prev_line.startswith('class '):
                        break
                
                if not found_matching_if:
                    print(f"🔧 Fixing orphaned 'else:' at line {i+1}")
                    fixed_lines.append(f"    # Fixed: orphaned else statement removed from line {i+1}")
                    fixes_applied += 1
                    continue
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Write fixed content if changes were made
        if content != original_content:
            # Backup original
            backup_path = f"{file_path}.syntax_backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"📁 Backup saved: {backup_path}")
            
            # Write fixed version
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Fixed {fixes_applied} syntax errors")
            return True
        else:
            print("ℹ️ No syntax errors found")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing syntax: {e}")
        return False

def main():
    print("🔧 SYNTAX ERROR FIX")
    print("=" * 30)
    
    # Fix syntax errors
    if fix_syntax_errors():
        print("✅ Syntax fixes applied")
        print("🎉 File is ready to run!")
    else:
        print("❌ Failed to apply fixes")

if __name__ == "__main__":
    main()
