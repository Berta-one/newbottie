import re

# Input / Output files
input_file = "hybrid_bot.py"
output_file = "hybrid_bot_fixed.py"

# 1. Read raw bytes and decode with fallback
with open(input_file, "rb") as f:
    raw_data = f.read()

decoded_text = raw_data.decode("utf-8", errors="replace")

# 2. Fix common garbled sequences
patterns = {
    r"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢": "•",
    r"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦": "…",
    r"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â": "”",
    r"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Âœ": "“",
    r"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¨": "¨",
    r"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢": "•",
    r"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦": "…",
    r"ÃƒÂ¢Ã¢â€šÂ¬": "—",  # em-dash
    r"ÃƒÂ¢Ã¢â€šÂ¬": "—",
    r"ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢€Å¡Ã‚Â¬": "€",  # Euro symbol
    r"ÃƒÆ’Ã‚Â°": "°",
    r"Ãƒâ€šÃ‚Â£": "£",  # Pound symbol
    # Add more as needed for your file...
}

for pattern, replacement in patterns.items():
    decoded_text = re.sub(pattern, replacement, decoded_text)

# 3. Normalize emojis if they were broken
emoji_fixes = {
    "ðŸ“Š": "📊",
    "ðŸŸ¢": "🔴",
    "ðŸ”´": "🔴",
    "âœ…": "✅",
    "â¹": "⏹",
    "ðŸ›‘": "🛑",
    "ðŸ“œ": "📜",
    "ðŸ“": "📝",
    "ðŸ“ˆ": "📈",
    "ðŸ“‹": "📋",
}

for bad, good in emoji_fixes.items():
    decoded_text = decoded_text.replace(bad, good)

# 4. Save the cleaned file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(decoded_text)

print(f"✅ Fixed encoding issues in {input_file}, saved to {output_file}")
