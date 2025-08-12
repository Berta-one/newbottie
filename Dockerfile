# Dockerfile (Python 3.11 slim, FastAPI + Uvicorn)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional, keep minimal)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Render provides $PORT; default to 10000
ENV PORT=10000

# Expose for clarity (Render doesn’t require EXPOSE, but it’s fine)
EXPOSE 10000

# Start API (uses $PORT from Render)
CMD ["sh", "-c", "uvicorn api_app:app --host 0.0.0.0 --port ${PORT}"]
CMD uvicorn api.app:app --host 0.0.0.0 --port $PORT 