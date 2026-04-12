# The tool as it is — and how to sort things out when the world changes

This page states a **contract** between you and this repository, then teaches a **repeatable process** for when Binance, Finnhub, Python packages, or URLs **change** without warning.

---

## 1. What stays “as it is”

**The Bottie codebase is the tool.** It is provided **as it exists in the repository**: same layout, same entry points (`render_api.py`, `engine/`, `ml/`, etc.), same spirit of documentation in `chapters/`.

- **We do not promise** that every line will track every external API revision the day it ships. Exchanges and data vendors move fast.
- **We do promise** that you can **learn** how the project is wired, so **you** can adjust configuration, environment variables, dependency versions, or small code edits when something breaks.

Think of it as **shipping a car with a manual**: the vehicle is what it is; when road rules or fuel types change, you use the manual and general mechanic skills—not a guarantee that the manufacturer repaints the car for every new law.

---

## 2. What changes without asking you (external world)

| Layer | Examples of change |
|-------|-------------------|
| **Exchange APIs** | New endpoints, stricter rate limits, renamed fields, testnet URL moves, regional restrictions. |
| **News / sentiment APIs** | Finnhub tiers, quotas, deprecated routes. |
| **Python ecosystem** | New `numpy` / `pandas` / `ccxt` / `qiskit` releases; deprecations. |
| **Your OS** | Python install path, antivirus blocking pip, long paths on Windows. |

None of that is controlled by this repo. **Sorting it out is part of running real software.**

---

## 3. How to sort things out (repeatable playbook)

Work **top to bottom** until the symptom changes.

### Step A — Capture the real error

- Read the **full traceback** (Python) or **HTTP status + JSON body** (API).
- Copy the **exact** message into a note (search works better on exact strings).

### Step B — Classify: our code vs library vs network vs provider

| Clue | Likely layer |
|------|----------------|
| `ModuleNotFoundError`, `ImportError` | Dependencies / venv |
| `401`, `403`, `Invalid API-key` | Keys, permissions, IP allowlist, wrong testnet vs main |
| `429`, `rate limit` | Too many requests; backoff; websockets vs REST |
| `ConnectionError`, timeouts | Network, firewall, DNS, provider outage |
| `KeyError`, `Key 'xyz' not in response` | **Provider changed JSON shape** — compare response to what code expects |

### Step C — Search this repository

```bash
rg "BINANCE|FINNHUB|api.binance|testnet" --glob "*.py"
rg "getenv|os.environ" --glob "*.py"
```

Find **which file** reads the variable or URL. That tells you **what to edit** (`.env`, config, or a one-line URL constant).

### Step D — Read the **current** provider docs

- **Binance:** official API documentation and changelog (spot vs futures differ).
- **Finnhub:** [https://finnhub.io/docs/api](https://finnhub.io/docs/api)
- **ccxt** (used for many exchanges): [https://docs.ccxt.com/](https://docs.ccxt.com/) — if Binance changes, `ccxt` often adapts in a **new release**; you may need `pip install -U ccxt` **after** reading this project’s pinned version in `requirements.txt` (upgrading blindly can break other things—test in a branch).

### Step E — Align environment with reality

- **Wrong base URL** — mainnet keys on testnet host or vice versa: fix `.env` and any `sandbox` / `testnet` flags in code.
- **Wrong permissions** — API key missing “read” or “trade” when the route needs it: regenerate key on the exchange with correct permissions.
- **Stale secret** — rotated on the website but not in `.env`: update and restart the process.

### Step F — Align dependencies (carefully)

1. Note **pinned versions** in `requirements.txt`.
2. If an upgrade is required (security, compatibility), create a **branch**, bump **one** major dependency at a time, run `pytest` and smoke tests.

### Step G — If the course text is outdated

Chapter URLs in `chapters/` (e.g. Binance settings links) are **signposts**, not legal contracts. If a link 404s:

1. Search the provider’s site for **API Management**, **testnet**, **dashboard**.
2. Optionally open a **pull request** or issue on the repo with the new official URL so others benefit.

---

## 4. Minimum skills to “self-serve”

- **Read** a Python traceback (file name + line number).
- **Use** `rg` / IDE search across the repo.
- **Compare** two JSON blobs (old response vs new).
- **Read** release notes for `ccxt`, `python-binance`, or FastAPI when you upgrade.

The [course chapters](CURRICULUM.md) exist to build those skills in context—not to replace official vendor documentation.

---

## 5. One-page checklist when something breaks after an upgrade

- [ ] Reproduce with **one** command (`pytest` one test, or `curl` one endpoint).
- [ ] `git diff` / remember what changed (deps, `.env`, OS update).
- [ ] Provider **status page** (outage?) and **API changelog**.
- [ ] Search repo for failing string or env var.
- [ ] Fix smallest change; re-run smoke (`scripts/smoke.py`) then API.

---

Back to [home](index.md) · [Chapter 0 — APIs & keys](chapter-00-beginners-apis-and-keys/README.md) · [Getting started](GETTING_STARTED.md)
