# engine/portfolio_manager.py
import os
import logging
from typing import Dict, List, Tuple
import numpy as np

from .classical_optimizer import ClassicalPortfolioOptimizer

# Quantum optional import
ENABLE_QUANTUM = os.getenv("ENABLE_QUANTUM", "1") not in ("0", "false", "False", None)
if ENABLE_QUANTUM:
    try:
        from quantum.portfolio_optimizer import QuantumPortfolioOptimizer
        HAS_QUANTUM = True
    except Exception as e:
        logging.getLogger("PortfolioManager").warning("Quantum import failed: %s", e)
        HAS_QUANTUM = False
else:
    HAS_QUANTUM = False

log = logging.getLogger("PortfolioManager")


def _conf_to_mu_cov(symbols: List[str], conf_map: Dict[str, float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build a tiny expected returns & covariance from confidences:
      mu_i = conf_i
      cov   = diag(max(1e-4, 0.05 - 0.04*conf_i))  (lower variance for higher confidence)
    This is a proxy when you don't have full historical return covariance here.
    """
    mu = np.array([float(conf_map.get(s, 0.0)) for s in symbols], dtype=float)
    variances = np.clip(0.05 - 0.04 * mu, 1e-4, None)
    cov = np.diag(variances)
    return mu, cov


class HybridPortfolioManager:
    """
    Quantum-first portfolio manager with classical fallback.
    Produces target weights per symbol (sum ~ 1) given signal confidences.
    """
    def __init__(self, max_pos_pct: float = 0.5, lambda_risk: float = 0.1):
        self.max_pos_pct = float(max_pos_pct)
        self.classical = ClassicalPortfolioOptimizer(max_pos_pct=max_pos_pct)
        self.quantum = QuantumPortfolioOptimizer(lambda_risk=lambda_risk) if HAS_QUANTUM else None

    def target_weights(self, symbols: List[str], conf_map: Dict[str, float]) -> Dict[str, float]:
        """
        Map conf_map (e.g., BUY confidences) to portfolio weights using quantum QAOA if available.
        """
        if not symbols:
            return {}

        # If quantum is enabled and at least 3 assets, try QAOA
        if self.quantum and len(symbols) >= 3:
            try:
                mu, cov = _conf_to_mu_cov(symbols, conf_map)
                w = self.quantum.optimize(mu=mu, cov=cov)  # shape [n], sum ~1
                # Cap per-asset exposure and renormalize
                w = np.clip(w, 0.0, self.max_pos_pct)
                s = w.sum()
                if s > 0:
                    w = w / s
                out = {smb: float(wi) for smb, wi in zip(symbols, w)}
                log.info("Quantum weights: %s", out)
                return out
            except Exception as e:
                log.warning("Quantum optimizer failed, using classical: %s", e)

        # Classical fallback (conf map to weights)
        out = self.classical.target_weights(symbols, conf_map)
        log.info("Classical weights: %s", out)
        return out