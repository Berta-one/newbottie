import os
import pandas as pd
from quantum.qml_models import QuantumPricePredictor
from quantum.hybrid_models import HybridQuantumEnsemble
from engine.portfolio_manager import SimpleBacktestPortfolio  # exists in backtesting module earlier
from utils import load_training_data


class QuantumBacktester:
    def __init__(self, mode: str = "quantum", initial_capital: float = 10_000):
        self.mode = mode
        self.model = self._init_model()
        self.portfolio = SimpleBacktestPortfolio(initial_capital=initial_capital)

    def _init_model(self):
        if self.mode == "quantum":
            return QuantumPricePredictor()
        elif self.mode == "hybrid":
            return HybridQuantumEnsemble()
        else:
            raise ValueError("Unsupported mode: expected 'quantum' or 'hybrid'.")

    # ------------------------------------------------------------------
    def run_backtest(self, market_df: pd.DataFrame) -> pd.DataFrame:
        print(f"[Backtest] Running in mode: {self.mode}")

        features = market_df[["open", "high", "low", "close", "volume"]].values
        labels = (market_df["close"].shift(-1) > market_df["close"]).astype(int).values

        # Fit (use all-but-last for training for now)
        if hasattr(self.model, "train"):
            self.model.train(features[:-1], labels[:-1])

        results = []
        for idx in range(len(features) - 1):
            x = features[idx].reshape(1, -1)
            raw_pred = self.model.predict(x)

            # Handle different return types (numeric vs tuple)
            if isinstance(raw_pred, tuple):
                signal_str, conf = raw_pred
                signal = signal_str.upper()
            else:
                signal = "BUY" if raw_pred == 1 else "SELL"
                conf = None

            self.portfolio.update(signal, float(market_df.iloc[idx]["close"]))

            results.append({
                "timestamp": market_df.index[idx],
                "price": float(market_df.iloc[idx]["close"]),
                "signal": signal,
                "confidence": conf,
                "capital": self.portfolio.capital,
            })

        report_df = pd.DataFrame(results)

        # Persist for dashboard
        os.makedirs("backtest_results", exist_ok=True)
        report_df.to_csv("backtest_results/latest_quantum_report.csv", index=False)

        return report_df


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("sample_data/historical_data.csv", index_col=0, parse_dates=True)
    tester = QuantumBacktester(mode="hybrid")
    report = tester.run_backtest(df)
    print(report.tail())