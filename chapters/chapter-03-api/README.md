# Chapter 3 — API & backend services

**Guided time:** 5–7 hours  
**Prerequisites:** [Chapter 2 — Environment](../chapter-02-environment/README.md)  

**Next:** [Chapter 4 — Engine](../chapter-04-engine/README.md)

---

## 1. Purpose

The HTTP layer is what operators and dashboards see first. Understanding it separates **“the server is up”** from **“the strategy is sane.”** This chapter focuses on **`render_api.py`** as the primary app, how **CORS** and **static** assets fit a Netlify-style frontend, and how to **probe** routes safely with **FastAPI TestClient**.

---

## 2. Objectives

1. Describe responsibilities of `render_api.py` at a high level.
2. Explain when to read **`api/app.py`** instead (legacy / parallel features / tests).
3. Use **`TestClient`** for repeatable local checks without manual curl.
4. Identify **read-only** vs **mutating** routes before you call them against real keys.

---

## 3. `render_api.py` — how to read a large FastAPI file

Large apps accumulate routes. Use a **systematic** approach:

1. **App construction** — `FastAPI(...)`, middleware, global state.
2. **Startup** — `on_event("startup")` or lifespan hooks (depending on FastAPI version in your branch).
3. **Auth** — JWT, bearer tokens, `/auth/token` patterns if present.
4. **Core trading / portfolio** — `/status`, `/positions`, `/trades`, `/signals`.
5. **ML / analytics** — `/ml/status`, `/ml/performance`, etc.
6. **Sentiment / quantum** — `/sentiment`, `/quantum/analysis`.
7. **Admin / reports** — report generators, logs, toggles.

**Teaching trick:** assign each student **one vertical slice** (e.g. “all `/ml/*` routes”) and have them diagram data sources.

---

## 4. `api/app.py` vs `render_api.py`

Reasons a repository keeps **two** apps:

- **Historical evolution** — `api/app.py` may predate the unified Render-oriented file.
- **Test fixtures** — some tests import `api.app:app` directly.
- **Feature divergence** — one path may include experimental admin routes.

**Rule of thumb for new work:** follow whatever the **root README** names as official (`render_api.py` today). If you merge apps, do it deliberately with a migration note.

---

## 5. Routers and modularity

`api/routes_grid.py` demonstrates **`APIRouter`**: mount related endpoints under a prefix in the main app (exact prefix depends on your `include_router` call—verify in `render_api.py` or `api/app.py`).

**Why routers matter:** they let you **document** and **test** cross-pair grid logic without scrolling a 2k-line file.

---

## 6. CORS

Browser-based dashboards on another **origin** (e.g. Netlify) require **CORS** headers. You will see `CORSMiddleware` with permissive settings in development-oriented configs.

**Production hardening** (your responsibility when you deploy):

- Restrict `allow_origins` to your real frontend hostnames.
- Review `allow_credentials` and cookie/JWT patterns.

This course does not prescribe your final CORS policy—only that you **know** it exists.

---

## 7. TestClient mini-course

### Minimal health test

```python
from fastapi.testclient import TestClient
import render_api

client = TestClient(render_api.app)
response = client.get("/health")
assert response.status_code == 200
body = response.json()
assert isinstance(body, dict)
```

### Why TestClient beats curl in teaching

- Assertions in **code** become **regression tests** later.
- Students practice **Python**, not only shell one-liners.

### Caveat

Some routes assume **background tasks**, **websockets**, or **global singletons** initialized at startup. TestClient may not perfectly mirror production unless you trigger startup events—read FastAPI docs for `lifespan` / startup in your version.

---

## 8. Route inventory lab

Run a search:

```bash
rg "@app\\.(get|post|put|delete)" render_api.py
```

Pick **five** routes:

| Route | GET/POST | Suspected read/write | Needs auth? |
|-------|----------|----------------------|-------------|
| … | … | … | … |

Fill the table from reading docstrings and function bodies.

---

## 9. Example routes (verify in your tree)

Your checkout may include paths similar to:

- `/health` — liveness / feature flags
- `/status` — richer dashboard payload
- `/signals` — strategy outputs
- `/trades` / `/trades/recent` — history views
- `/sentiment` — sentiment snapshot
- `/ml/status` — model health metrics
- `/quantum/analysis` — quantum-inspired analytics
- `/trading/start`, `/trading/stop` — control endpoints

**Never assume** semantics without reading the handler—names drift.

---

## 10. Security mindset

Before you point a browser at a public tunnel (ngrok, etc.):

- **Keys live server-side only.**
- **Disable trading** until intentional.
- **Rate-limit** aggressive polling endpoints in your frontend.

Chapter 7 expands operational security.

---

## 11. Labs

### Lab 3.1 — TestClient script (45 min)

Create `labs/api_probe.py` (gitignore `labs/` if needed) that:

1. GET `/health`
2. GET `/api-info` if present
3. Prints keys of JSON responses (sorted)

### Lab 3.2 — Error handling (30 min)

Call a route that **requires** missing credentials or data. Capture status code and body shape; document in markdown.

### Lab 3.3 — Router trace (45 min)

Find where `routes_grid` router is included. Diagram **full URL path** clients must use.

---

## 12. Exercises

1. Why might `allow_origins=["*"]` be acceptable in class but risky in production?
2. Name one route that returns **P&L or equity-related** fields (read the handler to confirm).

---

## 13. Notebook

`notebooks/01_testclient_tour.ipynb` — cells for each probe; markdown interpretation under each cell.

---

## 14. Summary

You can now **navigate** the HTTP layer deliberately. The engine chapter explains what happens **after** a signal is requested or a bar is injected—two different entry patterns that converge in operations.

Next: [Chapter 4 — Engine](../chapter-04-engine/README.md)
