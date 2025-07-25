# force_fix_encoding.py
input_file = "hybrid_bot.py"
output_file = "hybrid_bot_fixed.py"

with open(input_file, "rb") as f:
    raw_data = f.read()

# Try to decode as UTF-8, fallback to latin-1 for corrupted sequences
decoded_text = raw_data.decode("utf-8", errors="replace")

# Re-encode properly as UTF-8
with open(output_file, "w", encoding="utf-8") as f:
    f.write(decoded_text)

print(f"✅ Fixed encoding saved as {output_file}")
