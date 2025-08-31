module.exports = {
  apps: [{
    name: "bottie-api",
    script: "uvicorn",
    args: "api.app:app --host 0.0.0.0 --port 8000 --workers 1",
    interpreter: "python3",
    cwd: "/workspace",
    instances: 1,
    exec_mode: "fork",
    watch: false,
    max_memory_restart: "500M",
    env: {
      PORT: "8000",
      ENVIRONMENT: "production",
      PYTHONPATH: "/workspace"
    },
    env_production: {
      PORT: "8000",
      ENVIRONMENT: "production",
      TRADE_ENABLED: "1",
      LIVE_TRADING_ENABLED: "true"
    },
    log_file: "/workspace/logs/combined.log",
    out_file: "/workspace/logs/out.log",
    error_file: "/workspace/logs/error.log",
    log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    merge_logs: true
  }]
}