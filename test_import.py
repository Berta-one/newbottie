# test_imports.py
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from auth import require_authentication
    print("✅ Auth import successful!")
except ImportError as e:
    print(f"❌ Auth import failed: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Files in directory: {os.listdir(current_dir)}")