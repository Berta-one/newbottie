# fix_emojis.py
with open("hybrid_bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace all corrupted emojis with clean text
replacements = {
    'ðŸ"': '[LOCK]',
    'ðŸ"„': '[REFRESH]', 
    'ðŸ"¦': '[PACKAGE]',
    'ðŸš€': '[ROCKET]',
    'ðŸ§ª': '[TEST]',
    'ðŸ"§': '[TOOL]',
    'ðŸ"'': '[KEY]',
    'ðŸŽ¯': '[TARGET]',
    'ðŸ'¡': '[IDEA]',
    'ðŸ"Š': '[CHART]',
    'ðŸŸ¢': 'GREEN',
    'ðŸ"´': 'RED', 
    'ðŸŸ¡': 'YELLOW',
    'ðŸ›'': '[STOP]',
    'â–¶ï¸': '[PLAY]',
    'ðŸ"ˆ': '[UP_CHART]',
    'ðŸ§ ': '[BRAIN]',
    'ðŸ¤–': '[ROBOT]',
    'âœ‹': '[HAND]',
    'âš›': '[ATOM]',
    'ðŸ› ': '[SETTINGS]',
    'ðŸ©º': '[HEALTH]',
    'ðŸ"œ': '[SCROLL]',
    'ðŸ"‰': '[DOWN_CHART]',
    'ðŸ'°': '[MONEY]',
    'ðŸ"‹': '[LIST]',
    'ðŸš¨': '[ALERT]',
    'ðŸŽ®': '[GAME]',
    'ðŸŒ': '[GLOBE]',
    'ðŸ""': '[BELL]',
    'ðŸ'¾': '[SAVE]',
    'ðŸ"¤': '[UPLOAD]',
    'ðŸ"—': '[LINK]',
    'ðŸ—'ï¸': '[TRASH]',
    'ðŸ"¥': '[DOWNLOAD]'
}

fixes_applied = 0
for corrupted, replacement in replacements.items():
    if corrupted in content:
        content = content.replace(corrupted, replacement)
        fixes_applied += 1
        print(f"Fixed: {corrupted} -> {replacement}")

with open("hybrid_bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Applied {fixes_applied} emoji fixes")
