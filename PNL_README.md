# 📊 Sntax P&L Reporting System

Real-time WebSocket-based P&L tracking and reporting system for all trades since August 1st.

## 🚀 Quick Start

### 1. Start the P&L WebSocket Server
```bash
cd /workspace
python3 start_pnl_server.py
```

### 2. Access the P&L Dashboard
Open your browser and go to:
```
http://localhost:9000/pnl_dashboard.html
```

### 3. (Optional) Start API Integration
In a separate terminal:
```bash
cd /workspace
python3 pnl_integration.py
```

## 📈 Features

### ✅ Real-time P&L Tracking
- **WebSocket-based** updates (no REST API polling)
- **Live P&L calculations** for all trades
- **Real-time dashboard** with auto-refresh
- **Instant notifications** for new trades

### ✅ Comprehensive Trade Storage
- **SQLite database** for persistent storage
- **All trades since August 1st** automatically stored
- **Historical P&L analysis** with trend tracking
- **Export functionality** for reports

### ✅ Advanced Analytics
- **Per-symbol breakdown** with detailed metrics
- **Win/loss ratios** and success rates
- **Average P&L per trade** calculations
- **Largest wins/losses** tracking
- **Total volume** and trade count metrics

### ✅ Professional Dashboard
- **Real-time connection status** indicator
- **Interactive controls** for data refresh
- **Trade simulation** for testing
- **JSON export** for external analysis
- **Responsive design** with dark theme

## 🎯 Dashboard Features

### Summary Cards
- **Total P&L**: Overall profit/loss since August 1st
- **Total Trades**: Complete trade count with win/loss breakdown
- **Win Rate**: Success percentage with color coding
- **Average P&L**: Per-trade average performance

### Recent Trades Table
- **Real-time updates** via WebSocket
- **Complete trade details**: Time, symbol, side, amount, price, P&L
- **Color-coded P&L**: Green for profits, red for losses
- **Status tracking**: Open/closed trade monitoring

### Symbol Breakdown
- **Per-symbol analytics** with individual metrics
- **Win rates** and trade counts per symbol
- **Volume tracking** and P&L summaries
- **Best/worst trades** for each symbol

## 🔧 Technical Architecture

### WebSocket Server (`websocket_pnl_server.py`)
- **Port**: 8765 (WebSocket)
- **Database**: `trades_pnl.db` (SQLite)
- **Real-time updates** every 10 seconds
- **Trade simulation** for testing

### Dashboard (`pnl_dashboard.html`)
- **WebSocket client** with auto-reconnection
- **Real-time data visualization**
- **Export functionality** (JSON format)
- **Responsive design** for all devices

### API Integration (`pnl_integration.py`)
- **Syncs trades** from main API to P&L system
- **Automatic P&L calculation** using current prices
- **Real-time monitoring** for new trades
- **Error handling** and retry logic

## 📊 Database Schema

### Trades Table
```sql
- id: Auto-increment primary key
- trade_id: Unique trade identifier
- symbol: Trading pair (e.g., BTCUSDT)
- side: BUY or SELL
- amount: Trade quantity
- price: Execution price
- cost: Total trade cost
- fee: Trading fees
- timestamp: Unix timestamp (milliseconds)
- datetime: ISO datetime string
- status: Trade status (open/closed)
- pnl: Profit/Loss amount
- pnl_percentage: P&L percentage
```

### P&L Summary Table
```sql
- date: Trading date
- symbol: Trading pair
- total_trades: Number of trades
- winning_trades: Profitable trades count
- losing_trades: Loss-making trades count
- total_pnl: Total P&L for symbol/date
- win_rate: Success percentage
- avg_win/avg_loss: Average profit/loss
- largest_win/largest_loss: Best/worst trades
```

## 🎮 Usage Examples

### View P&L Report
1. Open dashboard at `http://localhost:9000/pnl_dashboard.html`
2. Dashboard automatically loads with current data
3. Real-time updates every 10 seconds

### Simulate Trades (Testing)
1. Click "🧪 Simulate Trade" button
2. Random trade will be generated and added
3. Dashboard updates automatically with new data

### Export Report
1. Click "📄 Export Report" button
2. JSON file downloads with complete P&L data
3. Use for external analysis or record keeping

### Manual Refresh
1. Click "🔄 Refresh Report" for instant update
2. Or click "Refresh" on individual sections
3. WebSocket reconnects automatically if disconnected

## 🔍 Monitoring & Debugging

### Connection Status
- **🟢 Green**: Connected to WebSocket server
- **🔴 Red**: Disconnected or connection failed
- **Auto-reconnect**: Up to 5 attempts with 3-second delay

### Console Logging
Open browser console (F12) to see:
- WebSocket connection status
- Message handling logs
- Error diagnostics
- Trade processing confirmations

### Server Logs
The P&L server outputs detailed logs:
- Trade storage confirmations
- Client connection/disconnection
- P&L calculation results
- Error messages and warnings

## 🛠️ Troubleshooting

### WebSocket Connection Failed
1. **Check server**: Ensure P&L server is running on port 8765
2. **Port conflicts**: Kill any processes using port 8765
3. **Firewall**: Allow connections on localhost:8765
4. **Browser**: Try refreshing or different browser

### No Trades Showing
1. **Database**: Check if `trades_pnl.db` exists
2. **Sample data**: Run server with `--simulate` flag
3. **API integration**: Ensure API is running and accessible
4. **Date range**: Verify trades are from August 1st onwards

### Performance Issues
1. **Database size**: Large trade history may slow queries
2. **WebSocket**: Check for connection stability
3. **Browser**: Clear cache and reload dashboard
4. **Memory**: Restart server if running for extended periods

## 📋 Requirements

- **Python 3.7+**
- **websockets** package
- **ccxt** package (for exchange integration)
- **sqlite3** (built-in with Python)
- **Modern web browser** with WebSocket support

## 🔄 Auto-Installation

The `start_pnl_server.py` script automatically:
1. **Checks dependencies** and installs missing packages
2. **Creates database** with proper schema
3. **Adds sample data** for demonstration
4. **Starts WebSocket server** on port 8765

## 🎯 Next Steps

1. **Start the server**: `python3 start_pnl_server.py`
2. **Open dashboard**: `http://localhost:9000/pnl_dashboard.html`
3. **Test functionality**: Use simulate trade feature
4. **Connect to API**: Run `pnl_integration.py` for live data
5. **Export reports**: Use dashboard export feature

**Your real-time P&L tracking system is ready! 🚀**