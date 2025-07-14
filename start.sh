#!/bin/bash
echo "�� Starting Railway Bot..."
python main_railway.py &
streamlit run dashboard.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true
wait
