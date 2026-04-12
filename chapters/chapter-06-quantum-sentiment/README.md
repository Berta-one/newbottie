# Chapter 6 — Quantum-inspired portfolio & sentiment

**Guided time:** 4–5 hours  
**Prerequisites:** [Chapter 5 — ML](../chapter-05-ml/README.md)  

**Next:** [Chapter 7 — Hardening](../chapter-07-hardening/README.md)

---

## 1. Purpose

This chapter covers **two optional differentiators** often highlighted in product marketing but operationally heavy:

1. **Quantum-inspired portfolio optimization** — a research-flavored layer that may run when Qiskit ecosystem imports succeed and environment flags allow it.
2. **Sentiment analysis** — typically Finnhub-backed news flows surfaced over HTTP for dashboards.

You should leave knowing **when to enable** each feature and **what happens when you disable** them.

---

## 2. Objectives

1. Explain how `HybridPortfolioManager` decides between **quantum** and **classical** weighting.
2. Describe **`ENABLE_QUANTUM`** and failure modes (import errors → `HAS_QUANTUM = False`).
3. Locate **sentiment** configuration keys and at least one **HTTP route** returning sentiment JSON.
4. Articulate **operational costs**: dependency weight, cold start time, external API rate limits.

---

## 3. Quantum path (architecture)

**Entry:** `engine/portfolio_manager.py`

- Reads `ENABLE_QUANTUM` (default **on** unless set to `0` / `false`).
- Tries to import `quantum.portfolio_optimizer.QuantumPortfolioOptimizer`.
- On import failure (missing optional deps, version skew), logs a warning and sets **`HAS_QUANTUM = False`**.

**Optimizer:** `quantum/portfolio_optimizer.py`

- Builds a **QUBO** via `_build_mv_qubo` from expected returns and covariance proxies.
- **Current engineering note:** full **QAOA + MinimumEigenOptimizer** wiring for modern `qiskit-algorithms` may still be evolving in your branch; the optimizer may **log** that it returns **uniform weights** while keeping the QUBO builder exercised. Treat quantum outputs as **experimental** until you verify solver behaviour in your fork.

**Backends:** `quantum/backends.py`

- Prefers **IBM** if token + provider packages work.
- Falls back to **Aer** simulator locally.
- IBM provider packages may be **optional**; Aer path should remain available for dev machines.

---

## 4. When quantum runs vs classical fallback

Even with `HAS_QUANTUM = True`, the hybrid manager may require **enough symbols** (historically ≥3) before attempting quantum optimization. With fewer symbols, classical weights are used.

**Teaching moment:** quantum here is **portfolio selection / weighting**, not the same module as **signal generation** ML.

---

## 5. Sentiment path (typical)

**Configuration** (representative keys—verify in your tree):

- `SENTIMENT_ENABLED`
- `FINNHUB_API_KEY`
- Windows / timing: `SENTIMENT_WINDOW_S`, polling intervals, asset lists

**Code locations:**

- `sentiment/` package — services and cycles.
- `render_api.py` — HTTP endpoints aggregating sentiment for dashboards.

**Operational caution:**

- External APIs impose **rate limits**; aggressive polling burns quota.
- News sentiment is **noisy** and may **lag** spot markets.

---

## 6. Labs

### Lab 6.1 — Quantum off (20 min)

Set:

```env
ENABLE_QUANTUM=0
```

Restart API; confirm logs show classical optimizer messaging without quantum attempts.

### Lab 6.2 — Quantum on (60 min, optional)

Set `ENABLE_QUANTUM=1` on a machine with full Qiskit stack installed. Watch logs for import warnings vs successful optimizer construction.

### Lab 6.3 — Sentiment route (45 min)

Call `/sentiment` (or your branch’s equivalent) with and without `FINNHUB_API_KEY`. Document status codes and JSON shapes.

---

## 7. Exercises

1. What env var disables quantum at the portfolio manager gate?
2. Name one practical reason to **disable** sentiment in development.
3. Where is `_build_mv_qubo` defined, and what mathematical structure does it return?

---

## 8. Product narrative (if you sell training)

Be transparent in marketing:

- **Quantum** may be **experimental / fallback-heavy** depending on version pins.
- **Sentiment** is **auxiliary** data, not oracle signal.

Students respect honesty; buyers punish overselling.

---

## 9. Notebook

`notebooks/01_optional_features_matrix.ipynb` — table: feature on/off, deps, risks, mitigations.

---

## 10. Summary

You can now **toggle** headline features without mystique. Chapter 7 converts this knowledge into **durable operations**: secrets, tests, deployment hygiene.

Next: [Chapter 7 — Hardening](../chapter-07-hardening/README.md)
