# Bottie - Autonomous Crypto Trading Bot

**Bottie** is a fully containerized, machine learning-driven trading bot designed to interact with the Binance API. It supports real-time data ingestion, model inference, backtesting, and both paper and live trading.

## 🚀 Features

- Real-time trading on multiple pairs using WebSocket feeds
- Machine Learning-based signal generation (XGBoost, LSTM, Transformer)
- Walk-forward optimization and backtesting
- Streamlit dashboard with login, metrics, and logs
- CI/CD pipeline and Dockerized deployment
- Monitoring stack (Prometheus, Grafana)

## 📁 Directory Structure

```
Bottie/
├── engine/                 # Core trading logic
├── models/                 # Pre-trained models
├── dashboard/              # Streamlit UI with metrics and logs
├── data/                   # Datasets for training/backtesting
├── scripts/                # Automation and utility scripts
├── Dockerfile*             # Deployment containers
└── README.md               # This file
```

## ⚙️ Setup

```bash
docker-compose up --build
```

## 🛡️ Security

- API keys managed via `.env`
- Authenticated dashboard with hashed login credentials
- Logging and alerting for system monitoring

## 📞 Support

Email: [luigi.rondanini@gmail.com](mailto:luigi.rondanini@gmail.com)

*Not financial advice. Use at your own risk.*
