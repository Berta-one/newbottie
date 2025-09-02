"""Utilities for performing sentiment analysis using VADER."""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore[import-untyped]


class SentimentAnalyzer:
    def __init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> float:
        score: dict[str, float] = self.analyzer.polarity_scores(text)
        return score["compound"]
