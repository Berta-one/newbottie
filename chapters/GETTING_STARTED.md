# Getting started

If you are **new to Python or APIs**, read **[Chapter 0 — New to Python and APIs](chapter-00-beginners-apis-and-keys/README.md)** first (install Python, what an API is, where to get Binance and Finnhub keys on the official sites). Then return here.

**The codebase is the tool, as it exists here.** When Binance, Finnhub, or your Python libraries change behaviour, you adapt configuration and dependencies—see **[The tool as-is — adapting when things change](ADAPTING_WHEN_THINGS_CHANGE.md)** for a step-by-step playbook.

This guide takes you from **empty folder** to **running API + passing smoke + optional docs site**. Expect to spend **half a day** if nothing goes wrong, or **a full day** if you fight Python installs on Windows.

---

## 1. Prerequisites

### Required

- **Python 3.11** (this repo is verified on 3.11; 3.10 may work; 3.12+ may need dependency checks).
- **Git**.
- Terminal: PowerShell on Windows, bash/zsh on macOS/Linux.
- **Network** for `pip install` (corporate proxies may need `pip`/`HTTPS_PROXY` configuration—not covered here).

### Optional (enable when you are ready)

- **Binance** API key + secret — prefer **testnet** and **minimal permissions** while learning.
- **Finnhub** API key — for news/sentiment features if you turn them on in config.

### Skills

- Create folders, run commands, read tracebacks.
- Edit environment variables without pasting secrets into chat logs or screenshots you share publicly.

---

## 2. Clone the repository

```bash
git clone <YOUR_REPO_URL> bottie
cd bottie
```

If you maintain a fork, clone your fork so `git push` is natural when you add course chapters or fixes.

---

## 3. Create and activate a virtual environment

**Why:** The repo pins versions (e.g. `bcrypt` with `passlib`) and pulls scientific stack packages. A venv avoids clashes with a broken global install (common on Windows after partial upgrades).

### Windows (PowerShell)

```powershell
cd d:\Bottie
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If execution policy blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### macOS / Linux

```bash
cd bottie
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Sanity check

```bash
python -c "import fastapi, ccxt, numpy, pandas; print('deps ok')"
```

---

## 4. Environment variables (`.env`)

**Never commit secrets.** The repo should list `.env` in `.gitignore`.

Typical workflow:

1. Copy a template if the repo provides `.env.example` (name may vary).
2. Create `.env` beside `render_api.py`.
3. Fill only what you need for the lab you are running.

**Conservative starter set for local learning:**

```env
LOG_LEVEL=INFO
TRADE_ENABLED=0
```

Add Binance keys only when you intentionally exercise authenticated endpoints:

```env
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
```

Add when testing sentiment:

```env
FINNHUB_API_KEY=...
SENTIMENT_ENABLED=1
```

`python-dotenv` is used by the app when present; if import fails, the process still reads the real OS environment.

---

## 5. Run the official API

From repo root with venv active:

```bash
python render_api.py
```

Default listen address is usually `0.0.0.0` and port from `PORT` or **8000**—check the startup log line.

### Health check

**curl** (Git Bash / WSL / macOS / Linux):

```bash
curl -s http://127.0.0.1:8000/health | python -m json.tool
```

**PowerShell** (no curl JSON pretty-print):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json
```

You should see HTTP **200** and a JSON body describing service mode and feature flags. Exact keys evolve with the codebase; the important part is **stable 200** and **no traceback** in the server terminal.

---

## 6. Run the engine smoke test (paper, synthetic bars)

This exercises **signal → portfolio → executor** without requiring exchange connectivity:

```bash
python scripts/smoke.py
```

**Expected:** process exits with code **0** and log lines from `SignalGenerator`, `ExecutionManager`, etc. With a neutral ML fallback you will mostly see **HOLD** and “signal not confirmed”—that is normal.

---

## 7. Run automated tests

Install test runners if not already present:

```bash
pip install pytest pytest-asyncio
pytest tests/ -q
```

Many tests are **integration-style** (HTTP, optional keys). If a subset fails on your machine, read the failure: often missing env, wrong port, or network. Chapter 7 expands on triage.

---

## 8. Troubleshooting (common)

### `ModuleNotFoundError: No module named 'engine'`

Run `scripts/smoke.py` from the **repository root**, or ensure `sys.path` includes the root (the script patches this—if you copied snippets into another folder, add the root manually).

### `numpy.dtype size changed` or pandas import errors

Your environment has **binary mismatches**. Fix: new venv + `pip install -r requirements.txt` only inside that venv.

### `passlib` / `bcrypt` errors

The repo pins **`bcrypt==4.0.1`** for `passlib` compatibility. Do not upgrade bcrypt arbitrarily inside this project without testing auth paths.

### Port 8000 already in use

- Stop the other process, or set `PORT` to another value for `render_api.py`, or run docs on another port (below).

### Import is slow the first time

`render_api` pulls many optional subsystems. First import can take **tens of seconds** on a laptop; subsequent imports are faster if the interpreter stays warm.

---

## 9. Documentation site {#documentation-site}

You can read chapters as Markdown on GitHub, or build a local site.

### Default site (ReadTheDocs theme, no Material)

Works with **`mkdocs` + `pymdown-extensions`** only (recommended on Windows if Material fails to install):

```bash
pip install mkdocs pymdown-extensions
mkdocs serve -f mkdocs.yml -a 127.0.0.1:8001
```

### Lite theme (minimal install)

```bash
pip install mkdocs
mkdocs build -f mkdocs-lite.yml
mkdocs serve -f mkdocs-lite.yml -a 127.0.0.1:8001
```

Browse `http://127.0.0.1:8001`.

### Material theme (closer to chapters.berta.one)

```bash
pip install -r requirements-docs.txt
mkdocs serve -f mkdocs-material.yml -a 127.0.0.1:8001
```

**Windows:** If `pip install mkdocs-material` fails with `OSError: [Errno 22] Invalid argument` (often when extracting theme assets under `.venv`), use **`mkdocs.yml`** or **`mkdocs-lite.yml`** instead—the content is the same. Alternatives: install from **WSL**, a **shorter path** (e.g. `C:\src\bottie`), or enable **Windows long paths**.

If Material install is slow, use the default or lite config first; content is the same.

---

## 10. What to do next

Open [Chapter 1 — Overview](chapter-01-overview/README.md) and keep the terminal open—you will alternate **reading** and **running** for the rest of the course.
