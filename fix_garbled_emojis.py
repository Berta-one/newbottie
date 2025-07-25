import os
import re

# Define replacements for common garbled characters
replacements = {
    "❌": "❌",
    "✔️": "✔️",
    "✔": "✔",
    "£": "£",
    "€": "€",
    "•": "•",
    "—": "—",
    "–": "–",
    "“": "“",
    "”": "”",
    "‘": "‘",
    "’": "’",
    "…": "…",
    "🎯": "🎯",
    "💷": "💷",
    "💸": "💸",
    "💰": "💰",
    "💹": "💹",
    "📊": "📊",
    "📝": "📝",
    "📍": "📍",
    "📏": "📏",
    "📐": "📐",
    "📁": "📁",
    "📚": "📚",
    "📞": "📞"
}

def fix_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    original = content
    for bad, good in replacements.items():
        content = content.replace(bad, good)
    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed: {path}")

def scan_directory(root_folder, extensions):
    for root, _, files in os.walk(root_folder):
        for filename in files:
            if any(filename.endswith(ext) for ext in extensions):
                fix_file(os.path.join(root, filename))

# Run the fixer
scan_directory("C:/tools/Bottie-main", [".py", ".txt", ".md"])
