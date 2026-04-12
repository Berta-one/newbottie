# Chapter 2 — Environment & first run

**Guided time:** 4–6 hours  
**Prerequisites:** [Chapter 1 — Overview](../chapter-01-overview/README.md)  

**Next:** [Chapter 3 — API](../chapter-03-api/README.md)

---

## 1. Purpose

This chapter makes your machine a **reliable lab**: isolated Python, correct wheels, working imports, a running API, and a **smoke test** that proves the engine pipeline executes. If you skip venv discipline here, you will lose days to “works on my machine” noise later.

---

## 2. Objectives

1. Create and use a **virtual environment** exclusively for Bottie.
2. Install **`requirements.txt`** without polluting global site-packages.
3. **Import** `render_api` and start the server; receive **200** from `/health`.
4. Run **`scripts/smoke.py`** with exit code **0**.
5. Recognize **three** common failure modes (path, ABI mismatch, bcrypt/passlib).

---

## 3. Python version

Target **3.11**. Older3.x may work; newer 3.12+ may need you to verify wheels for scientific and quantum packages. If you teach this course, standardize the class on **one** patch version to reduce support load.

---

## 4. Virtual environment (deep dive)

### Why not `pip install --user` globally?

Global installs **accumulate** conflicting numpy/pandas/scikit-learn builds. A classic symptom: `numpy.dtype size changed` when importing pandas. A clean venv fixes most of these instantly.

### Disk and paths

On Windows, keep the repo path **short** and **ASCII** if you hit MAX_PATH issues with some wheels (rare but real).

---

## 5. Installing dependencies

Always upgrade **pip** inside the venv first:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Notable pins (teaching notes)

- **`bcrypt==4.0.1`** — `passlib[bcrypt]` expects a compatible bcrypt major/minor; random upgrades break password hashing paths.
- **Quantum stack** — `qiskit`, `qiskit-aer`, `qiskit-optimization`, `qiskit-algorithms` add weight; first install can take minutes.

### Optional docs dependencies

Documentation builds use `requirements-docs.txt` (Material) or plain `mkdocs` for `mkdocs-lite.yml`. Do not mix docs requirements into the trading venv unless you want that bloat—many instructors use **two venvs**.

---

## 6. Environment variables

### `.env` file

If `python-dotenv` is installed, apps may call `load_dotenv()`. Keep `.env` **out of git**; commit only templates.

### Minimal safe starter

```env
LOG_LEVEL=INFO
TRADE_ENABLED=0
```

### When you add keys

- **Binance:** start with **testnet** URLs / sandbox flags as documented in your fork.
- **Finnhub:** required only if you enable sentiment routes that call out.

### PowerShell tip

```powershell
$env:LOG_LEVEL = "DEBUG"
python render_api.py
```

Session-only; good for one-off debugging.

---

## 7. First server run

```bash
python render_api.py
```

Watch the console:

- **Import errors** — fix before anything else.
- **Warnings** about optional modules (quantum, websocket helpers) — often non-fatal; learn which are fatal in your branch.

### Health probe

See [Getting started](../GETTING_STARTED.md) for curl vs PowerShell examples.

---

## 8. Smoke test (`scripts/smoke.py`)

The smoke script:

1. Adds the **repo root** to `sys.path` (so `engine` imports work when launched as a file).
2. Builds `IntegratedPortfolioEngine` with a couple of symbols.
3. Feeds **synthetic** alternating bars.
4. Exits **0** if no unhandled exception.

**Interpretation:** lots of `HOLD` and “signal not confirmed” lines are **expected** when ML returns neutral probabilities—read Chapter 4 for why.

```bash
python scripts/smoke.py
echo ExitCode: $LASTEXITCODE # PowerShell
```

---

## 9. Verification checklist (print this)

- [ ] `python -c "import render_api; print('import ok')"`
- [ ] Server starts without traceback
- [ ] `/health` returns 200
- [ ] `scripts/smoke.py` exit 0
- [ ] `pytest tests/ -q` (note: full suite may need time; see Chapter 7)

---

## 10. Troubleshooting guide

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No module named 'engine'` | cwd wrong | Run from repo root; see smoke script path fix. |
| dtype / binary errors | mixed numpy/pandas | New venv; reinstall requirements only inside it. |
| bcrypt / passlib noise | version skew | Keep `bcrypt==4.0.1` from requirements.txt. |
| Port in use | another uvicorn | Change `PORT` or stop other process. |
| Slow first import | heavy optional imports | Wait once; consider lazy imports in your fork if profiling shows win. |

---

## 11. Labs

### Lab 2.1 — Clean room (60–90 min)

1. Archive or rename your current venv.
2. Create a new `.venv`.
3. Reinstall from `requirements.txt`.
4. Re-run import + health + smoke.

### Lab 2.2 — DEBUG logs (30 min)

Set `LOG_LEVEL=DEBUG`. Restart API. Pick **one** log line you can explain to a peer.

### Lab 2.3 — `TRADE_ENABLED` (20 min)

Search the repo for `TRADE_ENABLED`. Summarize what toggling it does in **two sentences**.

---

## 12. Exercises

1. Document your exact Python version and pip version in a `labs/env_notes.md` file (personal notes, gitignored if you prefer).
2. What happens if you run `python scripts/smoke.py` from inside `scripts/` without the path fix? (Try it; restore after.)

---

## 13. Notebook suggestion

`notebooks/01_env_and_imports.ipynb`:

- Cells that import `render_api`, `engine.integrated_portfolio_engine`, `ml.ensemble_model` one by one.
- A markdown cell listing which imports are optional vs required.

---

## 14. Chapter summary

You now have a **reproducible lab**. Everything in Chapter 3+ assumes this foundation. If anything failed, fix it here—do not drag environment mystery into API debugging.

Next: [Chapter 3 — API](../chapter-03-api/README.md)
