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

# Use dynamic PORT from environment, default to 8000 for consistency
ENV PORT=8000
EXPOSE 8000

# Stamp the image with Render commit SHA and start API
CMD ["sh", "-c", "v=${RENDER_GIT_COMMIT:-unknown}; echo $v > /app/VERSION; echo \"Running commit: $v\"; echo \"Starting on port ${PORT}\"; uvicorn api.app:app --host 0.0.0.0 --port ${PORT}"] 