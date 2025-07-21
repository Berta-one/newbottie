with open("hybrid_bot.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix the specific problematic lines
lines[751] = "                max_positions=5\n"          # Line 752
lines[752] = "            )\n"                            # Line 753 - close function call  
lines[753] = "            print(\"[INFO] Risk Manager initialized\")\n"  # Line 754
lines[754] = "\n"                                        # Line 755 - empty
lines[755] = ""                                          # Line 756 - remove duplicate try
lines[756] = ""                                          # Line 757 - remove comment
lines[757] = ""                                          # Line 758 - remove pass
lines[758] = "        except Exception as e:\n"          # Line 759 - proper except
lines[759] = "\n"                                        # Line 760 - empty
lines[760] = "            print(f\"[ERROR] Risk Manager failed: {e}\")\n"  # Line 761

with open("hybrid_bot.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("✅ Fixed try/except structure")
