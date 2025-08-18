#!/usr/bin/env python3
"""Fix fetch calls in reports.js to use the fallback method"""

import re

def fix_reports_js():
    # Read the file
    with open('/workspace/netlify-deploy/reports.js', 'r') as f:
        content = f.read()
    
    # Replace fetch calls with fetchWithFallback
    patterns = [
        (r'await fetch\(`\$\{this\.apiUrl\}(/[^`]+)`\)', r'await this.fetchWithFallback("\1")'),
        (r'if \(!response\.ok\) throw new Error\([^)]+\);\s*', ''),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Write the fixed content
    with open('/workspace/netlify-deploy/reports.js', 'w') as f:
        f.write(content)
    
    print("✅ Fixed fetch calls in reports.js")

if __name__ == '__main__':
    fix_reports_js()