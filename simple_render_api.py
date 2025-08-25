#!/usr/bin/env python3
"""
Simplified Render API - Minimal version to ensure deployment works
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import time

# Create FastAPI app
app = FastAPI(title="Bottie Simple API", version="1.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple HTML page
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bottie Trading Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="bg-white rounded-xl shadow-lg p-8 text-center">
            <h1 class="text-4xl font-bold text-gray-800 mb-4">🚀 Bottie Trading Dashboard</h1>
            <p class="text-xl text-gray-600 mb-6">Your site is now loading successfully!</p>
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
                <strong>✅ Deployment Successful!</strong><br>
                Render deployment is working properly.
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <div class="bg-blue-50 p-4 rounded-lg">
                    <h3 class="font-semibold text-blue-800">API Status</h3>
                    <p class="text-blue-600">✅ Online</p>
                </div>
                <div class="bg-green-50 p-4 rounded-lg">
                    <h3 class="font-semibold text-green-800">Server</h3>
                    <p class="text-green-600">✅ Render.com</p>
                </div>
                <div class="bg-purple-50 p-4 rounded-lg">
                    <h3 class="font-semibold text-purple-800">Status</h3>
                    <p class="text-purple-600">✅ Live</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the main dashboard"""
    return HTML_CONTENT

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "UP",
        "service": "bottie-simple-api",
        "timestamp": time.time(),
        "message": "Render deployment successful!"
    }

@app.get("/api/status")
def api_status():
    """API status endpoint"""
    return {
        "success": True,
        "message": "Bottie API is running on Render",
        "timestamp": time.time(),
        "environment": os.getenv("ENVIRONMENT", "production")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)