# Bottie Trading System - Deployment Guide

## 🚀 Quick Start

The Bottie trading system supports multiple deployment methods. Choose the one that fits your needs:

## 📋 Prerequisites

1. **Python 3.11+** installed
2. **Binance API credentials** (for live trading)
3. **Environment variables** configured (copy `.env.template` to `.env`)

## 🐳 Docker Deployment (Recommended for VPS)

```bash
# 1. Build the image
docker build -t bottie-trading .

# 2. Run with environment file
docker run -d \
  --name bottie-trading \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  bottie-trading

# 3. Verify deployment
curl http://localhost:8000/health
```

**Nginx Configuration:**
```nginx
location / {
  proxy_pass http://127.0.0.1:8000;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";  # WebSocket support
  proxy_read_timeout 300s;
}
```

## ☁️ Render Deployment

1. **Create Render Web Service** from GitHub repository
2. **Configuration:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn render_api:app --host 0.0.0.0 --port $PORT`
   - Environment Variables: Set in Render dashboard (use `.env.template`)

3. **Verify:** `curl https://your-app.onrender.com/health`

## 🔧 PM2 Deployment (VPS)

```bash
# 1. Install PM2
npm install -g pm2

# 2. Deploy with script
./deploy.sh pm2

# 3. Manage the service
pm2 status
pm2 logs bottie-api
pm2 restart bottie-api
```

## 💻 Local Development

```bash
# 1. Quick start
./deploy.sh local

# OR manual setup:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python start_complete_system.py
```

## 🌐 Access URLs

- **Frontend Dashboard:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **WebSocket Interactive:** ws://localhost:8000/ws
- **WebSocket Live Feed:** ws://localhost:8000/ws/live

## 🔧 Troubleshooting 502 Errors

### Common Causes & Solutions

1. **Port Mismatch**
   ```bash
   # Check what port the app is running on
   ss -ltnp | grep -E '8000|10000'
   
   # Test locally
   curl -i http://127.0.0.1:8000/health
   ```

2. **Reverse Proxy Configuration**
   - Ensure proxy points to correct port (8000)
   - Add WebSocket upgrade headers for `/ws` endpoints
   - Check proxy timeout settings

3. **Environment Variables**
   ```bash
   # Verify required variables are set
   echo $PORT
   echo $BINANCE_API_KEY
   ```

4. **Service Health**
   ```bash
   # Check if service is running
   ps aux | grep uvicorn
   
   # Check logs
   tail -f logs/error.log  # PM2
   docker logs bottie-trading  # Docker
   ```

## 🔒 Security Configuration

### Environment Variables (Required)

```bash
# Copy template and configure
cp .env.template .env

# Set secure passwords
DASHBOARD_PASSWORD=your_secure_password
ADMIN_PASSWORD=your_admin_password
JWT_SECRET_KEY=your_jwt_secret_key

# Configure Binance API (for live trading)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_secret_key
```

### API Key Security

⚠️ **IMPORTANT:** Never commit `.env` files to version control

1. **Rotate exposed keys** if they were previously committed
2. **Use platform secret managers** for production (Render Environment Variables, Docker secrets, etc.)
3. **Restrict API key permissions** to trading only (no withdrawals)

## 📊 WebSocket Features

### Interactive WebSocket (`/ws`)
- Request-response pattern
- Get specific data on demand
- Available requests: `get_market_data`, `get_signals`, `get_trades`, `get_sentiment`, `get_ml`, `get_quantum`

### Live Feed WebSocket (`/ws/live`)
- Continuous updates every 5 seconds
- Real-time market data and signals
- Perfect for dashboard monitoring

### Example Usage
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data.type);
};

// Request specific data
ws.send(JSON.stringify({ type: 'get_signals' }));
```

## 🏗️ Architecture

- **Backend:** FastAPI + Uvicorn (Python)
- **Frontend:** Static HTML + JavaScript
- **Real-time:** WebSocket connections
- **Data:** SQLite + In-memory caching
- **Exchange:** Binance API (ccxt)

## 📈 Available Endpoints

### Core Trading
- `GET /status` - Account status and balance
- `GET /signals` - Trading signals
- `GET /grid/matrix` - Trading grid matrix
- `GET /trades/history` - Complete trade history since Aug 1st

### Detailed Tables (WebSocket-optimized)
- `GET /trades/table` - Enhanced trade visualization
- `GET /sentiment/table` - Sentiment analysis data
- `GET /ml/table` - ML predictions (1h/4h/24h)
- `GET /quantum/table` - Quantum analysis data

### WebSocket
- `WS /ws` - Interactive real-time data
- `WS /ws/live` - Continuous live feed

## 🎯 Performance Features

- **WebSocket real-time updates** instead of HTTP polling
- **Intelligent fallback** to HTTP if WebSocket fails
- **Auto-reconnection** with exponential backoff
- **Comprehensive caching** for optimal performance
- **Graceful degradation** when exchange is unavailable

---

For specific deployment issues, check the logs and verify port configurations match your infrastructure setup.