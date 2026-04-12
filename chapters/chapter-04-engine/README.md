# Chapter 4 — Engine & execution

**Guided time:** 6–8 hours  
**Prerequisites:** [Chapter 3 — API](../chapter-03-api/README.md)  

**Next:** [Chapter 5 — ML](../chapter-05-ml/README.md)

---

## 1. Purpose

The **engine** is where market information turns into **signals**, **portfolio targets**, and (optionally) **executed trades**. If you sell a “build this bot” course, this chapter is the **technical heart**: students must see the actual control flow, not only REST JSON.

---

## 2. Objectives

1. Trace **`on_bar`** from `IntegratedPortfolioEngine` through **`ExecutionManager`**.
2. Explain **`SignalGenerator`** thresholds: buy/sell minima, hold band, confidence gap.
3. Describe how **`HybridPortfolioManager`** chooses classical vs optional quantum weights.
4. Relate **`scripts/smoke.py`** log lines to specific modules.
5. Distinguish **paper** execution from **live** paths at the executor boundary.

---

## 3. Module map

| File | Role |
|------|------|
| `engine/integrated_portfolio_engine.py` | Thin orchestrator: receives bar dicts, calls execution manager. |
| `engine/execution_manager.py` | Cooldowns, confirmation, builds `conf_map`, asks portfolio for weights, calls executor. |
| `engine/signal_generator.py` | Feature vector from bar → ML `predict_proba` → discrete signal + confidence. |
| `engine/portfolio_manager.py` | `target_weights(symbols, conf_map)`; optional quantum if imports succeed and env allows. |
| `engine/classical_optimizer.py` | Long-only weighting from nonnegative confidences; caps per asset. |
| `engine/executor.py` | Applies targets (paper vs live depending on configuration / mode). |

Read files in **this order** the first time.

---

## 4. Data structure: what is a “bar”?

The engine expects a **dictionary** with at least:

- `symbol` — e.g. `"BTC/USDT"`
- `close` — float (also used as price reference)
- `high`, `low`, `volume` — used in simple features (defaults tolerate missing keys with sensible fallbacks)

Bars may carry additional keys depending on your upstream feed; `SignalGenerator` documents its minimal contract in code comments.

---

## 5. Signal generation (conceptual)

Steps (simplified):

1. **Features** — `_to_feature_vector(bar)` builds a short numeric vector.
2. **Probabilities** — `ml.ensemble_model.predict_proba([features])` returns a **batch** of rows; each row is `[p_sell, p_buy, p_hold]` (normalized three-way).
3. **Decision rules** — compare probabilities against **thresholds** loaded from environment (buy min, sell min, hold max, min gap between top-1 and top-2 classes).
4. **Output** — `(signal, confidence)` where signal ∈ {`BUY`,`SELL`,`HOLD`}.

**Why HOLD dominates in smoke tests:** without a trained on-disk model, the ensemble may return **neutral** probabilities; thresholds then favor HOLD and low confidence—by design, the pipeline stays safe.

---

## 6. Execution policy

`ExecutionManager` implements **guardrails**:

- **Cooldown** — `TRADE_COOLDOWN_S` prevents hammering the same symbol.
- **Minimum confidence** — `MIN_TRADE_CONF` (env) drops weak signals.
- **HOLD handling** — typically no trade when signal is HOLD.
- **Confirmation** — may ignore repeated same-direction noise unless confidence improves materially.

After guards pass, the manager builds a **per-symbol confidence map** (BUY gets positive confidence; other cases may map to zero for long-only classical path) and calls **`target_weights`**.

---

## 7. Portfolio weights

`HybridPortfolioManager`:

- If **quantum** is available **and** symbol count ≥ 3 (see source), it may attempt quantum optimization; failures log a warning and **fall back** to classical weights.
- **Classical** path: proportional weights from nonnegative confidences, renormalized, capped by `max_pos_pct`.

Weights are then **capped again** in `ExecutionManager` against `MAX_POS_PCT` / `max_pos_per_symbol` semantics—read the exact variable names in your branch.

---

## 8. Executor

The executor translates target weights into **account actions** depending on **mode** (paper vs live). This course stresses: **run paper until you trust logs and risk controls**.

---

## 9. Smoke test walkthrough (`scripts/smoke.py`)

The script:

1. Inserts repo root on `sys.path`.
2. Instantiates `IntegratedPortfolioEngine(["BTC/USDT", "ETH/USDT"], initial_capital=...)`.
3. Alternates synthetic bars with small price drift.
4. Sleeps briefly between bars so time-based cooldown logic can matter.

**Student task:** capture logs and **annotate** each phase: bar received → signal → guard outcome → (if any) weights.

---

## 10. Environment variables (engine-relevant)

Search the engine for `os.getenv`. Common knobs include:

- `MIN_TRADE_CONF`, `TRADE_COOLDOWN_S`, `MAX_POS_PCT`
- `SIG_BUY_MIN`, `SIG_SELL_MIN`, `SIG_HOLD_MAX`, `SIG_MIN_GAP` (signal thresholds)
- `BOT_MODE` or equivalent for executor mode
- `ENABLE_QUANTUM` — toggles quantum import path in portfolio manager

**Lab:** print a table of env vars you find and their default values in code.

---

## 11. Labs

### Lab 4.1 — Log annotation (60 min)

Run smoke with `LOG_LEVEL=INFO`. Highlight three lines: signal line, cooldown line, “not confirmed” line.

### Lab 4.2 — Threshold sweep (90 min)

Vary `SIG_BUY_MIN` upward and downward (reasonable bounds). Record how often BUY appears on synthetic data (may still be never—explain why).

### Lab 4.3 — Code trace (90 min)

Without running, **walk line-by-line** through `ExecutionManager.on_bar` with a highlighter. Write marginal notes in a PDF or notebook.

---

## 12. Exercises

1. What function computes the feature vector for a bar?
2. Where is `target_weights` called, and with what arguments?
3. Why might quantum optimization **not** run for only two symbols?

---

## 13. Misconceptions (FAQ)

**“If signal is BUY, I always trade.”**  
False—confidence and cooldowns can block execution.

**“Neutral ML means the code is broken.”**  
Often false—neutral probabilities are an explicit fallback when no model file is present.

**“Portfolio weights always use quantum.”**  
False—quantum is optional and gated by imports, env, and asset count.

---

## 14. Notebook

`notebooks/01_smoke_trace.ipynb` — paste logs, annotate, embed small reproduction cells for feature vectors.

---

## 15. Summary

You now understand **where** decisions happen and **why** smoke output looks conservative. Chapter 5 opens the ML box feeding probabilities into this layer.

Next: [Chapter 5 — ML](../chapter-05-ml/README.md)
