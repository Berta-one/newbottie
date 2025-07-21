import re

with open("hybrid_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

print("Original file size:", len(content))

# Remove all corrupted Unicode patterns starting with ð
content = re.sub(r'ð[^\w\s]', '[EMOJI]', content)

# Remove other problematic Unicode patterns
content = re.sub(r'â[^\w\s]', '[SYMBOL]', content)

print("After cleanup size:", len(content))

# Write the cleaned content
with open("hybrid_bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Cleaned all problematic Unicode characters")
