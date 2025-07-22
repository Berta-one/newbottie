#!/bin/bash
set -e

# Set PORT to 8501 if not specified
PORT=${PORT:-8501}

echo "STARTING ENTRYPOINT at $(date)" > railway.log
echo "PORT is: $PORT" >> railway.log

python bot_service.py >> railway.log 2>&1 &
streamlit run hybrid_bot.py --server.port=$PORT --server.address=0.0.0.0 >> railway.log 2>&1

wait