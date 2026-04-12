# Chapter 5 — ML & ensemble integration

**Guided time:** 6–8 hours  
**Prerequisites:** [Chapter 4 — Engine](../chapter-04-engine/README.md)  

**Next:** [Chapter 6 — Quantum & sentiment](../chapter-06-quantum-sentiment/README.md)

---

## 1. Purpose

Machine learning here is **not** a Kaggle leaderboard exercise—it is a **probability supplier** for a trading policy. This chapter explains the **contract** between `ml/ensemble_model.py` and `engine/signal_generator.py`, how **missing models** behave, and how to **safely** plug in trained classifiers.

**Disclaimer:** Teaching **integration** does not guarantee profitable trading. Stationarity, fees, slippage, and regime change dominate live results.

---

## 2. Objectives

1. State the **`predict_proba` batch contract** (input shape, output shape, class order).
2. Configure **`XGB_MODEL_PATH`** / **`ENSEMBLE_MODEL_PATH`** (or repo default paths) to load joblib models.
3. Explain **`SafeModel`** in `ml/model_loader.py` and why it exists.
4. Compare **`ensemble_model`** path with **`xgb_model.py`** (alternative wiring; may need `load_xgb` completion in your fork).

---

## 3. Contract: what `SignalGenerator` expects

`SignalGenerator.generate` calls (conceptually):

```text
P = ensemble_predict_proba([feature_row])
```

Where:

- Input is a **list of rows**; each row is a list of floats (one bar → one row typical).
- Output is a **list of rows**; each row has **three** probabilities aligned to **[SELL, BUY, HOLD]** after normalization inside the generator’s logic.

If the list is empty or malformed, the generator **falls back to HOLD** with zero confidence—safe default.

---

## 4. `Ensemble` class (lazy singleton pattern)

`ml/ensemble_model.py` defines:

- **`Ensemble`** — loads a model from disk via `load_model(path)` when a path is provided.
- **`predict_proba(X)`** — for each feature row:
  - If a model is loaded, call `model.predict_proba([feats])` and map **two-class** or **three-class** outputs into normalized triples.
  - If no model, emit **[1/3, 1/3, 1/3]** per row so the pipeline still runs (smoke tests rely on this).

**Pedagogy point:** distinguish **“no model”** (explicit neutral distribution) from **“model predicts uncertainty”** (learned probabilities).

---

## 5. `SafeModel` wrapper

`ml/model_loader.py` wraps raw sklearn-like estimators:

- If `predict_proba` exists, use it.
- If not, **synthesize** probabilities from `predict` outputs (including scalar mappings).

This reduces crashes when experimenting with heterogeneous model types—at the cost of **semantic** ambiguity if you feed the wrong estimator. Review synthesized paths before live trading.

---

## 6. Bringing your own model

### Training (outside this repo)

Typical pattern:

1. Build a labeled dataset aligned with your feature definition in `signal_generator.py` (or replace features deliberately).
2. Train a classifier with **`predict_proba`** (two-class is common).
3. **`joblib.dump(model, "models/xgb.pkl")`** (path illustrative).

### Wiring

Set env vars or place files where `ensemble_model._default_model_path()` searches:

- `XGB_MODEL_PATH`
- `ENSEMBLE_MODEL_PATH`
- `models/xgb.pkl`
- `models/ensemble.pkl`

Restart the process after changes—module-level singletons cache the ensemble.

---

## 7. Evaluation mindset (lightweight)

Before live deployment, at minimum:

- **Calibration** — raw probabilities may be miscalibrated; consider Platt scaling or isotonic regression if you rely on thresholds.
- **Leakage** — ensure labels do not peek into the future relative to features.
- **Fees** — policy thresholds should be interpreted **net** of costs if you simulate P&L.

This course does not implement a full backtester; add a chapter if you productize one.

---

## 8. Labs

### Lab 5.1 — Neutral path (30 min)

Run smoke **without** any model file. Confirm triple `[~0.33, ~0.33, ~0.33]` appears in logs.

### Lab 5.2 — Stub model (120+ min)

Train a trivial `sklearn` model on random data **only** to exercise plumbing:

- Same feature dimension as `_to_feature_vector`.
- Save via joblib.
- Point env path to it.
- Re-run smoke; observe whether BUY/SELL ever appears (may still be rare).

### Lab 5.3 — Contract test (45 min)

Write a **unit test** (in `tests/` or personal folder) that mocks `predict_proba` to return an extreme BUY vector and asserts `SignalGenerator` returns BUY with high confidence.

---

## 9. Exercises

1. Why is batching `predict_proba([row])` preferred over per-row import side effects?
2. What breaks if class order were **[BUY, SELL, HOLD]** but code assumes **[SELL, BUY, HOLD]**?
3. Locate `_to_feature_vector` and list the numeric features it constructs.

---

## 10. Notebook

`notebooks/01_feature_vector_and_proba.ipynb`:

- Reimplement `_to_feature_vector` in a cell.
- Plot histograms of dummy probabilities under neutral vs synthetic BUY-skewed model outputs.

---

## 11. Summary

The ML layer’s job is to **emit probabilities** the policy can threshold. The policy’s job is to **stay safe** when ML is absent or wrong. Chapter 6 adds **optional** quantum portfolio shaping and **external** sentiment feeds on top of this foundation.

Next: [Chapter 6 — Quantum & sentiment](../chapter-06-quantum-sentiment/README.md)
