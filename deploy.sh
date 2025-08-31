#!/bin/bash

# Bottie Trading System Deployment Script
# Handles different deployment scenarios with proper port configuration

set -e

echo "🚀 Bottie Trading System Deployment"
echo "=================================="

# Check deployment type
DEPLOY_TYPE=${1:-"local"}

case $DEPLOY_TYPE in
  "docker")
    echo "🐳 Docker Deployment"
    echo "Building Docker image..."
    docker build -t bottie-trading .
    
    echo "Starting container on port 8000..."
    docker run -d \
      --name bottie-trading \
      -p 8000:8000 \
      --env-file .env \
      --restart unless-stopped \
      bottie-trading
    
    echo "✅ Docker container started"
    echo "🌐 Access at: http://localhost:8000"
    echo "📊 Health check: curl http://localhost:8000/health"
    ;;
    
  "pm2")
    echo "🔧 PM2 Deployment"
    
    # Check if PM2 is installed
    if ! command -v pm2 &> /dev/null; then
      echo "Installing PM2..."
      npm install -g pm2
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Start with PM2
    echo "Starting with PM2..."
    pm2 start ecosystem.config.js --env production
    pm2 save
    
    echo "✅ PM2 deployment completed"
    echo "🌐 Access at: http://localhost:8000"
    echo "📊 Status: pm2 status"
    echo "📋 Logs: pm2 logs bottie-api"
    ;;
    
  "render")
    echo "☁️ Render Deployment"
    echo "Using render.yaml configuration..."
    echo "Make sure your Render service is configured with:"
    echo "  - Build Command: pip install -r requirements.txt"
    echo "  - Start Command: uvicorn render_api:app --host 0.0.0.0 --port \$PORT"
    echo "  - Environment Variables: Set in Render dashboard"
    echo ""
    echo "✅ Render configuration ready"
    echo "🌐 Your app will be available at: https://your-app.onrender.com"
    ;;
    
  "local"|*)
    echo "💻 Local Development"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
      echo "Creating virtual environment..."
      python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Start the application
    echo "Starting local server..."
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔌 API: http://localhost:8000"
    echo "📡 WebSocket: ws://localhost:8000/ws"
    echo ""
    
    python start_complete_system.py
    ;;
esac

echo ""
echo "📋 DEPLOYMENT CHECKLIST:"
echo "========================"
echo "1. ✅ Port configuration standardized (8000)"
echo "2. ⚠️  Set environment variables (copy .env.template to .env)"
echo "3. ⚠️  Configure Binance API credentials"
echo "4. ✅ WebSocket endpoints available (/ws, /ws/live)"
echo "5. ✅ Health check endpoint available (/health)"
echo ""
echo "🔧 TROUBLESHOOTING 502 ERRORS:"
echo "- Verify the service is running on the expected port"
echo "- Check reverse proxy/tunnel configuration"
echo "- Test health endpoint: curl http://localhost:8000/health"
echo "- Check logs for startup errors"