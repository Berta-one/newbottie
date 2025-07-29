# tests/test_qml_models.py

import unittest
import numpy as np
from quantum.qml_models import QuantumPricePredictor

class TestQuantumPricePredictor(unittest.TestCase):

    def test_training_and_prediction(self):
        X = np.random.rand(20, 4)
        y = np.random.randint(0, 2, size=20)

        qp = QuantumPricePredictor()
        qp.train(X, y)

        # Predict on a single sample; the model returns a float probability
        # representing the likelihood of an upward move.
        prob = qp.predict(X[:1])

        self.assertIsInstance(prob, float)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

if __name__ == '__main__':
    unittest.main()