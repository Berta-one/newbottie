import ast
import sys

def find_all_syntax_errors(filename):
   print(f"Checking {filename} for ALL syntax errors...")
   
   try:
       with open(filename, 'r', encoding='utf-8') as f:
           content = f.read()
       
       # Try to parse the entire file
       ast.parse(content, filename)
       print("✅ No syntax errors found!")
       return []
       
   except SyntaxError as e:
       print(f"❌ SYNTAX ERROR at line {e.lineno}:")
       print(f"   Message: {e.msg}")
       print(f"   Text: {repr(e.text.strip() if e.text else 'N/A')}")
       if e.offset:
           print(f"   Position: {e.offset}")
       
       # Show context around the error
       lines = content.split('\n')
       start = max(0, e.lineno - 5)
       end = min(len(lines), e.lineno + 5)
       
       print(f"\n   Context around line {e.lineno}:")
       for i in range(start, end):
           marker = ">>> " if i == e.lineno - 1 else "    "
           print(f"   {marker}Line {i+1}: {repr(lines[i])}")
       
       return [e]
   
   except Exception as e:
       print(f"❌ OTHER ERROR: {e}")
       return [e]

if __name__ == "__main__":
   find_all_syntax_errors("hybrid_bot.py")
