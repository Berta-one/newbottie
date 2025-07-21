import os
import sys

def fix_unicode_and_syntax():
    """Fix both Unicode encoding and syntax issues"""
    
    file_path = "hybrid_bot.py"
    
    if not os.path.exists(file_path):
        print("❌ hybrid_bot.py not found")
        return False
    
    print("🔧 Fixing Unicode encoding and syntax...")
    
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"✅ Successfully read with {encoding} encoding")
            break
        except UnicodeDecodeError:
            print(f"❌ Failed with {encoding} encoding")
            continue
    else:
        print("❌ Could not read file with any encoding")
        return False
    
    # Fix the content
    lines = content.split('\n')
    
    # Look for problematic lines around 1860
    fixes_made = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Fix orphaned else statements
        if line.strip() == 'else:':
            # Check if there's a matching if above
            found_if = False
            for j in range(max(0, i-20), i):
                if 'if ' in lines[j] or 'elif ' in lines[j]:
                    if lines[j].strip().endswith(':'):
                        found_if = True
                        break
            
            if not found_if:
                print(f"🔧 Fixing orphaned else at line {line_num}")
                lines[i] = '    # Fixed: removed orphaned else statement'
                fixes_made += 1
    
    # Write back with UTF-8 encoding
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Fixed {fixes_made} syntax issues and saved with UTF-8 encoding")
        return True
        
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        return False

def validate_syntax():
    """Validate the fixed syntax"""
    try:
        with open("hybrid_bot.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, "hybrid_bot.py", 'exec')
        print("✅ Python syntax is now valid!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
        if e.text:
            print(f"   Problem line: {e.text.strip()}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

if __name__ == "__main__":
    print("🚨 UNICODE + SYNTAX FIX")
    print("=" * 30)
    
    if fix_unicode_and_syntax():
        if validate_syntax():
            print("🎉 SUCCESS! File is ready!")
        else:
            print("⚠️ Syntax issues may remain")
    else:
        print("❌ Fix failed")
