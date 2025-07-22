#!/bin/bash
echo \"Starting container at \07/22/2025 10:31:58\" > /app/railway.log
echo \"PORT value is: \\" >> /app/railway.log

# Start the worker bot in the background
python bot_service.py >> /app/railway.log 2>&1 &

# Start Streamlit dashboard
streamlit run hybrid_bot.py --server.port=\ --server.address=0.0.0.0 >> /app/railway.log 2>&1

wait
