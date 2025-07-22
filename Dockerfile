FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install supervisor
EXPOSE 8501
CMD supervisord -c /app/supervisord.conf
