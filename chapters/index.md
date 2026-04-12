# Bottie — build the trading stack

Welcome to the **in-repo course** for Bottie: a chapter-based path through a real **FastAPI** backend, **execution engine**, **ML hooks**, optional **quantum-inspired** portfolio code, and **sentiment** integration. You read, you run the code on your machine, and you extend the system with a clear picture of how the pieces connect.

**The tool is the repository as it is.** The codebase is provided **as-is**: this course teaches you to **run it, understand it, and adapt it** when exchanges, APIs, or libraries change. It does **not** promise that every external URL or provider rule will stay frozen forever—**[when things change, use this playbook](ADAPTING_WHEN_THINGS_CHANGE.md)** to sort them out systematically.

**Never used Python or unsure what an “API” is?** Start with **[Chapter 0 — New to Python and APIs](chapter-00-beginners-apis-and-keys/README.md)** (where to install Python, what an API is, and where to get Binance / Finnhub keys on the real websites). It is written to be **self-contained**.

Publishing or selling this material? See **[Note for creators — pricing and donations](NOTE_FOR_CREATORS.md)**.

The **folder layout** mirrors the [Berta Chapters](https://chapters.berta.one/) idea: each chapter has a `README.md` as the spine, room for **Jupyter notebooks**, **exercises**, and pointers into the **production code** at the repository root. You can still use **[Berta AI](https://berta.one/)** to draft additional notebooks or chapters and merge them here the same way you grow the main Berta curriculum.

**Disclaimer:** This material is **software engineering education**, not investment, tax, or legal advice. Cryptocurrency markets are volatile. **If you ever decide to use it** for live trading or real funds, start with **testnet** and **paper mode**, keep **size small**, and only scale once you trust your setup and your own risk controls.

For context on **expectations vs how markets actually work** (including why an AI assistant is not a substitute for discipline, infrastructure, and risk management), see Luigi’s article: [Claude didn’t earn $10k overnight — and that isn’t how markets work](https://medium.com/@info_38412/claude-didnt-earn-10k-overnight-and-that-isn-t-how-markets-work-b2bb2717aa76).

---

## Who this is for

- **Complete beginners** — after [Chapter 0](chapter-00-beginners-apis-and-keys/README.md), you can continue even if you had never installed Python before.
- Developers who want a **guided tour** of a non-trivial Python trading stack (not a toy script).
- Former users of Bottie who want a **structured reference** to teach or sell a “build it yourself” product without appearing on camera.
- Students of your Berta-style pedagogy who expect **objectives → reading → labs → exercises → troubleshooting**.

If you already code: you should be comfortable with **Python**, **virtual environments**, and **HTTP basics** (GET/POST, JSON). If not, Chapter 0 + [Getting started](GETTING_STARTED.md) close the gap.

---

## What you will be able to do

After working through the curriculum (and doing the labs, not only skimming):

1. **Explain** the path from an HTTP request to optional trade execution.
2. **Run** `render_api.py` locally and interpret `/health` and related payloads.
3. **Run** `scripts/smoke.py` and map log lines to `engine/` modules.
4. **Configure** environment variables safely (no secrets in git).
5. **Extend** or replace the ML probability layer without breaking the signal pipeline.
6. **Decide** when quantum and sentiment features are worth the operational complexity.

---

## How long it takes

| Path | Chapters | Guided hours (read + labs) |
|------|----------|----------------------------|
| API + deploy focus | 1, 2, 3, 7 | ~12–15 h |
| Signals + paper trading | 1, 2, 4, 5, 7 | ~18–22 h |
| Full linear track | 1 → 7 | ~30–40 h |

The “guided hours” assume you type the commands, break things once or twice, and read error messages. Power users go faster; first-time FastAPI learners should **double the estimate** for Chapters 2–4.

---

## Start here

| Step | Link |
|------|------|
| Install, env, first commands | [Getting started](GETTING_STARTED.md) |
| Full syllabus and learning paths | [Curriculum](CURRICULUM.md) |
| Big-picture architecture | [Chapter 1 — Overview](chapter-01-overview/README.md) |
| Hands-on environment | [Chapter 2 — Environment](chapter-02-environment/README.md) |

---

## Quick links into the repo

| Goal | Where |
|------|--------|
| Official HTTP entry (Render / local) | `render_api.py` |
| Alternate / legacy monolith API | `api/app.py` |
| Bar → signal → weights → executor | `engine/` |
| Batch probabilities for signals | `ml/ensemble_model.py` |
| Paper integration smoke (no exchange keys required for basic path) | `scripts/smoke.py` |
| Automated tests | `pytest tests/` |

---

## Glossary (short)

| Term | Meaning in this repo |
|------|---------------------|
| **Bar** | One candle / tick summary: symbol, OHLCV-style fields consumed by `SignalGenerator`. |
| **Paper** | Simulated execution (no real exchange orders), controlled via executor / env. |
| **Quote** | Usually USDT (or configured quote currency) for pair symbols like `BTC/USDT`. |
| **Smoke** | `scripts/smoke.py` — synthetic bars through the integrated engine to verify imports and control flow. |

---

## Building this site locally

See [Getting started — Build this documentation site](GETTING_STARTED.md#documentation-site).

---

*Structure inspired by Berta Chapters; Bottie-specific content is maintained in this repository.*
