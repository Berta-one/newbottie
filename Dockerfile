FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /app/start.sh
EXPOSE 8501
ENTRYPOINT [\"/app/start.sh\"]
