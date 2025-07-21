import re

with open("hybrid_bot.py", "r", encoding="utf-8") as f:
    content = f.read()

print("Applying nuclear fix for all corrupted try/except blocks...")

# Pattern 1: Fix corrupted closing lines with symbols
content = re.sub(
    r"# Fixed: removed orphaned closing parenthesis\\\\n\s+print\(\"\[SYMBOL\]\[SYMBOL\][^\"]*\"\)",
    ")\n            print(\"[INFO] Component initialized\")",
    content
)

# Pattern 2: Remove orphaned except blocks and create proper structure  
lines = content.split("\n")
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i].strip()
    
    # Look for orphaned except statements
    if line.startswith("except Exception as e:") and i > 0:
        # Check if previous lines suggest this should be part of a proper try/except
        found_try = False
        
        # Look backwards for signs of a try block
        for j in range(max(0, i-20), i):
            if ("modules.get(" in lines[j] or 
                "components[" in lines[j] or
                "api_secret=" in lines[j]):
                found_try = True
                break
        
        if found_try:
            # This should be part of a proper try/except - fix it
            indent = len(lines[i]) - len(lines[i].lstrip())
            fixed_lines.append(" " * (indent - 4) + "except Exception as e:")
        else:
            fixed_lines.append(lines[i])
    else:
        fixed_lines.append(lines[i])
    
    i += 1

content = "\n".join(fixed_lines)

# Pattern 3: Fix any remaining [SYMBOL] patterns
content = content.replace("[SYMBOL][SYMBOL]", "[INFO]")
content = content.replace("[SYMBOL]", "[INFO]")

# Write the fixed content
with open("hybrid_bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Applied nuclear fix to all corrupted try/except blocks")
