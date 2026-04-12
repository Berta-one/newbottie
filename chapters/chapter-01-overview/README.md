# Chapter 1 — Overview & architecture

**Guided time:** 3–4 hours  
**Prerequisites:** Basic Python, HTTP familiarity  

**Next:** [Chapter 2 — Environment](../chapter-02-environment/README.md)

---

## 1. Why this chapter exists

Bottie is not a single script: it is a **networked system** with a public HTTP surface, background behaviour, optional exchange connectivity, and a **decision pipeline** that turns market updates into signals and (sometimes) actions. Before you change code, you need a **map**. This chapter builds that map so later chapters feel like “zooming in” rather than guessing.

---

## 2. Learning objectives

By the end you should be able to:

1. **Name** the four big layers: client, API, engine/ML, external data.
2. **Identify** `render_api.py` as the primary entry used in README deployment flows.
3. **Contrast** `render_api.py` with `api/app.py` (historical / alternate monolith).
4. **Sketch** data flow from an HTTP GET to JSON that may reflect positions, ML, or sentiment—without claiming you understand every branch yet.

---

## 3. Deployment topology (typical)

The project README describes a common split:

- **Frontend** (e.g. static dashboard on Netlify) talks to the backend over HTTPS.
- **Backend** (e.g. FastAPI on Render or your VPS) holds trading logic and secrets.
- **Data sources:** exchange APIs, WebSockets, third-party sentiment (Finnhub), etc.

You do not need to deploy both tiers to learn: **localhost** API + browser or `curl` is enough for most labs.

---

## 4. Mental model (diagram)

```mermaid
flowchart TB
  subgraph clients [Clients]
    DASH[Dashboard static site]
    CURL[Scripts / curl / TestClient]
  end

  subgraph api_layer [HTTP layer]
    RAPI[render_api.py FastAPI app]
    ALT[api/app.py alternate app]
  end

  subgraph core [Decision core]
    ENG[engine: signals execution portfolio]
    ML[ml: ensemble probabilities]
  end

  subgraph external [External]
    EX[Exchange ccxt / REST / WS]
    SENT[Sentiment Finnhub etc]
  end

  DASH --> RAPI
  CURL --> RAPI
  RAPI --> ENG
  RAPI --> ML
  ENG --> ML
  RAPI --> EX
  RAPI --> SENT
  ENG --> EX ALT -.->|legacy or parallel| ENG
```

**Reading tip:** arrows are **logical** (“may call / may depend on”), not a strict UML sequence diagram.

---

## 5. Repository map (where to look)

| Concern | Primary location | Notes |
|---------|------------------|--------|
| Main FastAPI app | `render_api.py` | Large file: routes, startup, trading loops, integrations. |
| Alternate API surface | `api/app.py` | Useful for comparison; tests may import it. |
| Diagnostics router | `api/diagnostics.py` | Version / health-style helpers when mounted. |
| Grid / cross-pair router | `api/routes_grid.py` | Example of `APIRouter` pattern. |
| Bar → signal → trade | `engine/` | Heart of automation: `signal_generator`, `execution_manager`, `portfolio_manager`, `executor`. |
| ML probabilities | `ml/ensemble_model.py`, `ml/model_loader.py` | Engine expects a **batch** `predict_proba` contract. |
| Quantum portfolio (optional) | `quantum/` | Classical fallback always available. |
| Sentiment workers | `sentiment/` | Finnhub and related config. |
| Integration smoke | `scripts/smoke.py` | Synthetic path through engine without live keys. |
| Tests | `tests/` | Mix of unit and integration tests. |

---

## 6. Representative HTTP surface (`render_api.py`)

The exact list changes over time; **discover** routes in your checkout with search:

```bash
rg "@app\\.(get|post)" render_api.py
```

Examples you are likely to find include: `/`, `/health`, `/status`, `/signals`, `/positions`, `/trades`, `/sentiment`, `/ml/status`, `/quantum/analysis`, trading control routes, and report endpoints. Treat this list as **inventory**, not a contract for your fork.

---

## 7. The engine in one paragraph

A **market bar** (symbol + OHLCV-like fields) enters `IntegratedPortfolioEngine`, which delegates to `ExecutionManager`. The manager asks `SignalGenerator` for a **discrete label** (BUY / SELL / HOLD) and a **confidence**. Guards (cooldown, minimum confidence, HOLD handling) decide whether to proceed. If proceeding, **portfolio weights** are computed (classical always; quantum path optional), then the **executor** syncs targets—often in **paper** mode during learning.

You will **re-read** this paragraph after Chapter 4; it should then feel concrete.

---

## 8. Labs

### Lab 1.1 — Inventory routes (20 min)

1. Open `render_api.py`.
2. List **ten** distinct path strings from `@app.get` / `@app.post`.
3. For each, one word: **read** vs **write** vs **control** (your judgement).

### Lab 1.2 — Two entry points (30 min)

1. Search the repo for `uvicorn.run` and for `FastAPI(`.
2. Note which files construct apps.
3. Write **three sentences** explaining why a project might keep two apps (`render_api` vs `api.app`).

### Lab 1.3 — Diagram (45 min)

Re-draw the mental model diagram **without looking**, then compare. Fix mistakes.

---

## 9. Exercises (short answers)

1. **Primary entry:** Which file does the root README name as the official launch command?
2. **Engine orchestration:** What class in `engine/integrated_portfolio_engine.py` wraps the execution manager?
3. **Client assumption:** Why does CORS appear in FastAPI middleware for this project type?

---

## 10. Self-check quiz

1. True or false: all trading logic lives only in `render_api.py`.
2. True or false: `scripts/smoke.py` requires Binance keys to exit successfully.
3. Name one external data source mentioned in README or this chapter.

**Answers (hide until tried):** (1) False — `engine/` is core logic. (2) False — smoke uses synthetic bars; keys not required for that path. (3) Binance, Finnhub, WebSocket feeds—any one.

---

## 11. Notebooks to add

Create `notebooks/01_architecture_inventory.ipynb`:

- Cell 1: your diagram.
- Cell 2: table of routes you care about.
- Cell 3: “open questions” list for Chapter 2–3.

---

## 12. Further reading (in-repo)

- Root `README.md` — feature list and endpoint summary.
- `chapters/CURRICULUM.md` — time budgeting.

Next: [Chapter 2 — Environment](../chapter-02-environment/README.md)
