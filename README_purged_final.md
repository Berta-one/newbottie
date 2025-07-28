# 🤖 Ultimate AI Trading Bot (Purged & Production-Ready)

This repository contains the **complete AI-powered cryptocurrency trading bot**, purged of all placeholders and built for real-time, multi-pair live trading using Binance.

---

## ✅ Features

- 🧠 **AI Decision Engine** — combines LSTM + XGBoost + sentiment scores
- 📊 **Multi-pair WebSocket Engine** — trades all Binance USDT pairs
- ⚡ **Real-time Execution** — via CCXT on Binance (paper/live mode)
- 📈 **Streamlit Dashboard** — view signals, trades, logs in real time
- ☁️ **Docker + GitHub Actions** — automatic VPS deployment
- 🧪 **Auto-downloading models** — for easy setup, smaller repo size

---

## 📁 Directory Structure

```
.
├── engine/                 # Execution + live market engine
├── ml/                    # Model loading, signal logic
├── sentiment/             # News sentiment API logic
├── models/                # Auto-populated with LSTM/XGBoost models
├── dashboard/             # Streamlit UI
├── deployment/            # VPS + Cloudflare setup scripts
├── .github/workflows/     # Auto-deployment pipeline
├── .env.example           # Config template
├── docker-compose.yml     # Multi-container app definition
├── Dockerfile             # Base build for the bot
```

---

## ⚙️ Setup (No Terminal Required)

### 1. 📥 Clone Repo

You can upload or sync this to GitHub manually or via the web interface.

### 2. 🔐 Set up `.env`

Copy `.env.example` → `.env` and fill:

```env
API_KEY=your_binance_key
API_SECRET=your_binance_secret
MODE=live
```

---

## 🚀 Run It (On VPS)

```bash
git pull origin main
docker-compose up -d --build
```

📌 On first run:
- Models auto-download into `models/`
- Bot connects to Binance and dashboard runs on `http://your-vps-ip:8501`

---

## 🔁 Automatic Deployment (Optional)

### GitHub Actions

1. Add SSH key to your VPS (`~/.ssh/authorized_keys`)
2. Add these **GitHub secrets**:
   - `VPS_HOST`
   - `VPS_USER`
   - `VPS_SSH_KEY`

3. Workflow: `.github/workflows/deploy.yml`

---

## 🔍 Model Download Script

Located in `ml/model_loader.py`, it:
- Downloads latest `lstm_model.h5` and `xgboost_model.json`
- Places them into `models/`
- Used by `ml/decision_engine.py` during signal generation

---

## 🧠 Strategy Logic

1. Get real-time prices via WebSocket
2. Fetch news sentiment (via News API)
3. Feed historical data to:
   - LSTM (trend prediction)
   - XGBoost (volatility/confidence scoring)
4. Aggregate into final `buy`, `sell`, or `hold` signal
5. Risk-managed execution based on portfolio config

---

## 📬 Notifications (Optional)

Can be extended to:
- Email daily reports
- Send alerts via Discord/Telegram (not included)

---

## 🧠 Advanced (Optional Enhancements)

- Add Prometheus + Grafana for system monitoring
- Swap models with transformer-based or RL agents
- Extend Streamlit to show trade history and live stats

---

## 🧪 Testing Mode

Set `MODE=paper` in `.env` to run simulation only.

---

Made with 🧠 and 💹 by Codex.