# Frontend Access Guide

## Issue Resolution

After running the mobile test, the index page was not found because the API server (port 8000) only serves JSON endpoints, not HTML files.

## Solution

The frontend files need to be served separately from the API. Here are the options:

### Option 1: Quick Frontend Access (Recommended)
```bash
# Start frontend server on port 3000
cd /workspace
python3 -m http.server 3000 --directory web
```
Then open: http://localhost:3000

### Option 2: Complete System Startup
```bash
# Start both frontend and API servers
cd /workspace
python3 start_complete_system.py
```

### Option 3: Frontend with Local API
To connect the frontend to your local API instead of the remote one:
```
http://localhost:3000?api=http://localhost:8000
```

## Server Architecture

- **Frontend Server**: Port 3000 (serves HTML/CSS/JS files)
- **API Server**: Port 8000 (serves JSON endpoints)

## Files Structure
```
/workspace/
├── web/
│   ├── index.html      # Main dashboard
│   ├── app.js          # Frontend logic
│   └── style.css       # Styling
├── api/
│   └── app.py          # API server
└── start_complete_system.py  # Combined startup script
```

## Why This Happened

The mobile test didn't break anything - it just highlighted that:
1. The API server only serves JSON data
2. HTML files need a separate web server
3. The frontend was previously accessed differently

## Quick Test
```bash
# Test frontend
curl -I http://localhost:3000/

# Test API
curl -I http://localhost:8000/health
```

Both should return HTTP 200 OK responses.