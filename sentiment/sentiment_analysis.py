# sentiment/sentiment_analysis.py

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import logging

nltk.download("vader_lexicon", quiet=True)

class SentimentAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text):
        """
        Analyze the sentiment of the given text.
        Returns a score between -1 (negative) and 1 (positive).
        """
        if not text or not isinstance(text, str):
            self.logger.warning("Invalid input to sentiment analyzer.")
            return 0.0

        sentiment = self.analyzer.polarity_scores(text)
        compound_score = sentiment['compound']
        self.logger.debug(f"Sentiment score for input: {compound_score}")
        return compound_score

    def batch_analyze(self, texts):
        """
        Analyze a list of texts and return the average sentiment score.
        """
        scores = [self.analyze(t) for t in texts if isinstance(t, str)]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        self.logger.info(f"Batch sentiment score: {avg_score}")
        return avg_score