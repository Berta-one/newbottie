#!/bin/bash

# Trading Reports Dashboard - Netlify Deployment Script
# This script prepares and deploys the reports dashboard to Netlify

set -e

echo "🚀 Deploying Trading Reports Dashboard to Netlify"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "netlify.toml" ]; then
    print_error "netlify.toml not found. Please run this script from the project root directory."
    exit 1
fi

print_status "Checking deployment directory..."

# Create netlify-deploy directory if it doesn't exist
if [ ! -d "netlify-deploy" ]; then
    print_warning "netlify-deploy directory not found. Creating it..."
    mkdir -p netlify-deploy
fi

# Check if required files exist
required_files=("netlify-deploy/reports.html" "netlify-deploy/reports.js" "netlify-deploy/report_generator.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    print_error "Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    print_error "Please ensure all required files are present before deploying."
    exit 1
fi

print_success "All required files found!"

# Create reports directory
print_status "Creating reports directory..."
mkdir -p netlify-deploy/reports

# Copy additional assets if they exist
print_status "Copying additional assets..."

if [ -d "web/assets" ]; then
    print_status "Copying assets from web/assets..."
    cp -r web/assets netlify-deploy/ 2>/dev/null || true
fi

if [ -f "web/style.css" ]; then
    print_status "Copying style.css..."
    cp web/style.css netlify-deploy/ 2>/dev/null || true
fi

# Create a simple index.html that redirects to reports
print_status "Creating index.html redirect..."
cat > netlify-deploy/index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Dashboard</title>
    <meta http-equiv="refresh" content="0; url=/reports.html">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }
        .container {
            max-width: 400px;
            padding: 2rem;
        }
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        a {
            color: white;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <h1>Trading Dashboard</h1>
        <p>Redirecting to reports dashboard...</p>
        <p><a href="/reports.html">Click here if not redirected automatically</a></p>
    </div>
</body>
</html>
EOF

# Create _redirects file for Netlify
print_status "Creating _redirects file..."
cat > netlify-deploy/_redirects << EOF
# Redirect root to reports
/  /reports.html  200

# API proxying to your backend
/api/*  https://bottie-1.onrender.com/api/:splat  200

# SPA fallback
/*  /reports.html  200
EOF

# Validate the deployment
print_status "Validating deployment files..."

total_size=$(du -sh netlify-deploy | cut -f1)
print_status "Deployment directory size: $total_size"

file_count=$(find netlify-deploy -type f | wc -l)
print_status "Total files: $file_count"

# List important files
print_status "Deployment contents:"
echo "├── reports.html ($(stat -f%z netlify-deploy/reports.html 2>/dev/null || stat -c%s netlify-deploy/reports.html) bytes)"
echo "├── reports.js ($(stat -f%z netlify-deploy/reports.js 2>/dev/null || stat -c%s netlify-deploy/reports.js) bytes)"
echo "├── report_generator.py ($(stat -f%z netlify-deploy/report_generator.py 2>/dev/null || stat -c%s netlify-deploy/report_generator.py) bytes)"
echo "├── index.html"
echo "├── _redirects"
echo "└── reports/ (directory)"

# Check if Netlify CLI is available
if command -v netlify &> /dev/null; then
    print_status "Netlify CLI detected!"
    echo ""
    echo "To deploy now, run:"
    echo "  netlify deploy --dir=netlify-deploy --prod"
    echo ""
    echo "Or for a preview deployment:"
    echo "  netlify deploy --dir=netlify-deploy"
else
    print_warning "Netlify CLI not found."
    echo ""
    echo "To install Netlify CLI:"
    echo "  npm install -g netlify-cli"
    echo ""
    echo "Then authenticate and deploy:"
    echo "  netlify login"
    echo "  netlify deploy --dir=netlify-deploy --prod"
fi

print_success "Deployment preparation complete!"
echo ""
echo "📁 Deployment directory: netlify-deploy/"
echo "🌐 After deployment, access your dashboard at:"
echo "   https://your-site.netlify.app/reports"
echo ""
echo "🔧 Configuration:"
echo "   - API endpoint: https://bottie-1.onrender.com/api"
echo "   - Auto-refresh: Every 5 minutes"
echo "   - Sample data: Enabled as fallback"
echo ""
echo "📖 Documentation: See netlify-deploy/README.md for detailed usage instructions"

# Optional: Test the Python report generator
if command -v python3 &> /dev/null; then
    print_status "Testing Python report generator..."
    cd netlify-deploy
    if python3 -c "import sys; sys.path.append('.'); from report_generator import ReportGenerator; print('✅ Report generator import successful')" 2>/dev/null; then
        print_success "Python report generator is ready!"
        echo "  Test it with: cd netlify-deploy && python3 report_generator.py --type trading --range 24h"
    else
        print_warning "Python report generator needs dependencies. Install with:"
        echo "  pip install pandas numpy requests"
    fi
    cd ..
else
    print_warning "Python3 not found. The report generator requires Python 3.7+."
fi

echo ""
echo "🎉 Ready for deployment!"