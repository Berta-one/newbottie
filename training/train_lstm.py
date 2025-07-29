import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler

def train_lstm(data_path='sample_data/historical_data.csv'):
    df = pd.read_csv(data_path)
    prices = df['close'].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    prices_scaled = scaler.fit_transform(prices)

    X, y = [], []
    for i in range(50, len(prices_scaled)):
        X.append(prices_scaled[i-50:i])
        y.append(prices_scaled[i])
    X, y = np.array(X), np.array(y)

    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
        tf.keras.layers.LSTM(50),
        tf.keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=10, batch_size=32)

    model.save('models/lstm_model.h5')
    print("LSTM model trained and saved to models/lstm_model.h5")
