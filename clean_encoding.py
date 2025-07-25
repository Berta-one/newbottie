import re

def clean_encoding_issues(text):
    # Common garbled patterns to clean Unicode
    replacements = {
        r'ÃƒÆ\'Ã‚Â¢ÃƒÂ¢Ã¢€Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å"': '-',
        r'ÃƒÆ\'Ã‚Â¢ÃƒÂ¢Ã¢€Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â': ' ',
        r'ÃƒÆ\'Ã‚Â¢ÃƒÂ¢Ã¢€Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…"': '"',
        r'ÃƒÆ\'Ã‚Â¢ÃƒÂ¢Ã¢€Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾': '~',
        r'ÃƒÆ\'Ã‚Â°Ãƒ…Ã‚Â¸Ãƒâ€šÃ‚Â§Ãƒâ€šÃ‚Â ': '🏠',
        r'ÃƒÆ\'Ã‚Â°Ãƒ…Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢Ãƒâ€šÃ‚Â¼': '💼',
        r'ÃƒÆ\'Ã‚Â°Ãƒ…Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã…"Ãƒâ€¹Ã¢€Â ': '📊',
        r'ÃƒÆ\'Ã‚Â°Ãƒ…Ã‚Â¸Ãƒâ€šÃ‚Â¤ÃƒÂ¢Ã¢â€šÂ¬Ã¢€Å"': '🤖',
        r'ÃƒÆ\'Ã‚Â¢Ãƒ…Ã¢€Å"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¹': '✅',
        r'ÃƒÆ\'Ã‚Â¢Ãƒâ€šÃ‚ÂÃƒ…Ã¢€â„¢': '❌',
        r'ÃƒÆ\'Ã‚Â¢Ãƒ…Ã‚Â¡Ãƒâ€šÃ‚Â ÃƒÆ\'Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â': '⚠️',
        r'ÃƒÆ\'Ã‚Â¢Ãƒ…Ã‚Â¡ÃƒÂ¢Ã¢â€šÂ¬Ã‚Âº': '⭐',
        r'ÃƒÆ\'Ã‚Â°Ãƒ…Ã‚Â¸Ãƒ…Ã‚Â¸Ãƒâ€šÃ‚Â¢': '✅',
        r'ÃƒÆ\'Ã‚Â°Ãƒ…Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€šÃ‚Â´': '❌',
        r'ÃƒÆ\'Ã‚Â°Ãƒ…Ã‚Â¸Ãƒ…Ã‚Â¸Ãƒâ€šÃ‚Â¡': '⚠️',
        r'Ã°Å¸"Å"': '📝',
        r'ÃƒÆ\'Ã‚Â¢ÃƒÂ¢Ã¢€Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢': '•',
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    return text

# Read, clean, and write the file
with open('hybrid_bot.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

cleaned_content = clean_encoding_issues(content)

with open('hybrid_bot_cleaned.py', 'w', encoding='utf-8') as f:
    f.write(cleaned_content)

print("✅ File cleaned and saved as hybrid_bot_cleaned.py")
