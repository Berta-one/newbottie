class TradingCore:
    def __init__(self, model, signal_threshold=0.7):
        self.model = model
        self.signal_threshold = signal_threshold

    def generate_signal(self, price_data):
        prob = self.model.predict_proba(price_data)[0][1]
        if prob > self.signal_threshold:
            return "buy", prob
        elif prob < 1 - self.signal_threshold:
            return "sell", 1 - prob
        else:
            return "hold", prob
