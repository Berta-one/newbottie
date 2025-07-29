# Fetches and scores real sentiment from News API
# sentiment/news_sentiment.py

import requests
from textblob import TextBlob
from datetime import datetime, timedelta

class NewsSentimentAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://newsapi.org/v2/everything"
        self.positive_threshold = 0.1
        self.negative_threshold = -0.1

    def fetch_news(self, query="crypto OR bitcoin OR ethereum", from_date=None, to_date=None, max_results=10):
        if not from_date:
            from_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.utcnow().strftime("%Y-%m-%d")

        params = {
            "q": query,
            "from": from_date,
            "to": to_date,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": max_results,
            "apiKey": self.api_key,
        }

        response = requests.get(self.endpoint, params=params)
        if response.status_code != 200:
            print(f"[Error] News API failed: {response.status_code} - {response.text}")
            return []

        return response.json().get("articles", [])

    def analyze_sentiment(self, articles):
        sentiment_score = 0
        count = 0

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            content = f"{title} {description}"
            analysis = TextBlob(content)
            sentiment_score += analysis.sentiment.polarity
            count += 1

        if count == 0:
            return 0.0

        return sentiment_score / count

    def get_sentiment_score(self):
        articles = self.fetch_news()
        score = self.analyze_sentiment(articles)
        return round(score, 3)
