# tests/test_qml_models.py

import unittest
import numpy as np
from quantum.qml_models import QuantumPricePredictor

class TestQuantumPricePredictor(unittest.TestCase):

    def test_training_and_prediction(self):
        X = np.random.rand(20, 4)
        y = np.random.randint(0, 2, size=20)

        qp = QuantumPricePredictor()
        qp.fit(X, y)
        preds = qp.predict(X)

        self.assertEqual(len(preds), len(y))
        self.assertTrue(set(preds).issubset({0, 1}))

if __name__ == '__main__':
    unittest.main()