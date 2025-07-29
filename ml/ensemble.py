from models.xgboost_model import load_model as load_xgb
from models.lstm_model import load_lstm_model

def vote(signals):
    return max(set(signals), key=signals.count)

def get_ensemble_signal(data):
    xgb_model = load_xgb()
    lstm_model = load_lstm_model()
    signals = ['buy', 'sell']  # placeholder
    return vote(signals)
