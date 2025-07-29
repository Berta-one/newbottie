import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from quantum.qml_models import QuantumPricePredictor
from utils import load_training_data


def train_quantum_model():
    print("[Quantum Training] Loading data...")
    X, y = load_training_data(normalize=True)

    # Basic sanity check in case of empty data
    if len(X) == 0:
        raise ValueError("Training data is empty – ensure `sample_data/historical_data.csv` is populated.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    print("[Quantum Training] Initializing model...")
    model = QuantumPricePredictor(num_qubits=X.shape[1])

    print("[Quantum Training] Training...")
    model.train(X_train, y_train)

    print("[Quantum Training] Predicting on test set...")
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"[Quantum Training] Accuracy: {acc:.4f}")

    return model


if __name__ == "__main__":
    train_quantum_model()