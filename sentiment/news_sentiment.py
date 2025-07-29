# sentiment/news_sentiment.py

import requests
import hashlib
import time
import os

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
CACHE_TTL = 3600  # 1 hour
CACHE = {}

def fetch_cached_sentiment(query):
    key = hashlib.md5(query.encode()).hexdigest()
    now = time.time()

    # Return cached if fresh
    if key in CACHE and now - CACHE[key]["time"] < CACHE_TTL:
        return CACHE[key]["score"]

    url = (
        f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt"
        f"&apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return 0.0

    articles = response.json().get("articles", [])[:10]
    text = " ".join([a["title"] + " " + a.get("description", "") for a in articles])
    score = sentiment_score(text)

    # Cache result
    CACHE[key] = {"score": score, "time": now}
    return score

def sentiment_score(text):
    from textblob import TextBlob
    blob = TextBlob(text)
    return round(blob.sentiment.polarity, 4)