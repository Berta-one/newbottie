
class EnsembleModel:
    def __init__(self, models):
        self.models = models

    def predict(self, X):
        votes = [model.predict(X) for model in self.models]
        return sum(votes) / len(votes)
