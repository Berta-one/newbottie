
import xgboost as xgb

def train_xgboost(X, y):
    model = xgb.XGBClassifier()
    model.fit(X, y)
    return model
