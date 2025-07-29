import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class WalkForwardTester:
    def __init__(self, strategies, data, n_splits=3, results_path: str = "results/wfo_equity.csv"):
        self.strategies = strategies
        self.data = data
        self.n_splits = n_splits

        # will store individual equity DataFrames from each window for later aggregation
        self.equity_curves = []
        self.results_path = results_path

    def split_data(self):
        split_size = len(self.data) // self.n_splits
        for i in range(self.n_splits):
            start = i * split_size
            end = start + split_size
            yield self.data[start:end]

    def retrain_model(self, data):
        X = data[['rsi', 'macd']]
        y = data['label']
        model = RandomForestClassifier()
        model.fit(X, y)
        return model

    def _save_results(self):
        """Persist concatenated equity curves to CSV for dashboard consumption."""
        if not self.equity_curves:
            return
        import os, pandas as pd
        os.makedirs(os.path.dirname(self.results_path), exist_ok=True)
        equity_df = pd.concat(self.equity_curves, ignore_index=True)
        equity_df.to_csv(self.results_path, index=False)

    def run(self):
        """Execute walk-forward optimization loop and store equity curves."""
        try:
            from backtesting.quantum_backtester import QuantumBacktester as MultiStrategyBacktester  # type: ignore
        except ImportError:
            # Fallback minimal stub to avoid hard dependency during dashboard demo
            class MultiStrategyBacktester:  # type: ignore
                def __init__(self, strategies):
                    self.strategies = strategies
                    self.data = None
                    self.portfolio_equity = None

                def run_backtest(self):
                    # Simple placeholder equity curve (flat)
                    import pandas as pd, numpy as np
                    if self.data is None:
                        return
                    self.portfolio_equity = pd.DataFrame({
                        "timestamp": self.data.index if hasattr(self.data, "index") else range(len(self.data)),
                        "equity": np.linspace(100000, 100000, len(self.data))
                    })

        for i, window in enumerate(self.split_data()):
            # Split current window into in-sample and out-of-sample
            train_size = int(len(window) * 0.8)
            train_data = window[:train_size]
            test_data = window[train_size:]

            # (Optional) retrain model on train_data
            _ = self.retrain_model(train_data)

            # Initialise backtester
            backtester = MultiStrategyBacktester(self.strategies)
            backtester.data = test_data
            backtester.run_backtest()

            # Collect equity curve
            if backtester.portfolio_equity is not None:
                import pandas as pd
                df_eq = backtester.portfolio_equity if isinstance(backtester.portfolio_equity, pd.DataFrame) else pd.DataFrame(backtester.portfolio_equity)
                df_eq["walk_forward_step"] = i
                self.equity_curves.append(df_eq.reset_index(drop=True))

        # Persist for dashboard
        self._save_results()
