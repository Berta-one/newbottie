#!/bin/bash
set -e

echo \"STARTING ENTRYPOINT at \07/22/2025 10:35:37\" > railway.log
echo \"PORT is: \\" >> railway.log

# Start worker in background, log output
python bot_service.py >> railway.log 2>&1 &

# Start Streamlit dashboard, log output
streamlit run hybrid_bot.py --server.port=\ --server.address=0.0.0.0 >> railway.log 2>&1

wait
