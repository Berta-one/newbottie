# Chapter 0 — New to Python and APIs? Start here {#chapter-00-beginners}

This chapter is **self-contained**: you do not need prior courses. It explains what an **API** is, how **Python** fits in, and **exactly where on the web** to obtain the keys this project can use (Binance, Finnhub, optional others). Follow it once before [Getting started](../GETTING_STARTED.md) if these ideas are new to you.

**The Bottie tool stays as it is in the repo**—we do not silently rewrite the whole project every time Binance or Finnhub updates a dashboard URL. **Links and steps below can drift**; when they do, use **[When things change — how to adapt](../ADAPTING_WHEN_THINGS_CHANGE.md)** to find the current provider pages and fix your setup.

**Time:** 2–4 hours (reading + installing Python + optional key creation)

---

## Part A — What is an API? (no jargon first)

**An API (Application Programming Interface)** is a **contract** that lets one program ask another service a question or send a command **over the network**, in a structured way.

- **You** (or your bot) do not log into Binance’s website by clicking buttons for every action.
- Instead, your **code** sends an **HTTP request** (like a letter with a form) to Binance’s **servers**. The server answers with **JSON** (structured text: balances, prices, errors).

Think of it as:

| Everyday idea | Technical name |
|---------------|----------------|
| Address of the service | **URL** (e.g. `https://api.binance.com/...`) |
| Letter asking “what is my balance?” | **GET request** |
| Letter saying “place this order” | **POST request** |
| The reply | **Response** (often **JSON**) |
| Your membership card | **API key** + often a **secret** to sign requests |

**Why keys?** The exchange must know **which account** is calling and that **you** authorized the software. **Never** paste keys into public chats, screenshots, or GitHub.

---

## Part B — What is Python?

**Python** is a **programming language** your computer runs. This repository is mostly Python: files ending in `.py`. You install **Python** once, then use **`pip`** to install **libraries** (packages) like FastAPI or `ccxt` that talk to exchanges.

You do **not** need to master Python before opening this repo—but you need to:

1. Install Python from the official site (below).
2. Open a **terminal** (PowerShell on Windows, Terminal on Mac).
3. Run commands exactly as written in [Getting started](../GETTING_STARTED.md).

### Where to install Python

- **Official download (all platforms):** [https://www.python.org/downloads/](https://www.python.org/downloads/)
- Pick **Python 3.11.x** if available (this project is tested on 3.11).
- **Windows:** During install, check **“Add Python to PATH”** so `python` works in the terminal.

### Check that it works

Open a terminal and run:

```bash
python --version
```

You should see something like `Python 3.11.x`. On some systems the command is `python3`:

```bash
python3 --version
```

### What is `pip`?

**`pip`** is Python’s package installer. Example:

```bash
pip install -r requirements.txt
```

That reads the project’s `requirements.txt` and downloads the listed libraries into your environment (preferably a **virtual environment**—see Getting started).

---

## Part C — Keys this project may use (where to get them)

Below are **official entry points**. Always log in only via **HTTPS** and **bookmark** the real site—avoid phishing links.

### 1. Binance (spot / main API) — trading & market data

Bottie-style code often uses **environment variables** such as:

- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`

**Where to create API keys (logged-in Binance account):**

- **API Management (Spot / general):**  
  [https://www.binance.com/en/my/settings/api-management](https://www.binance.com/en/my/settings/api-management)  
  (If that path changes, use the Binance website: **Profile → API Management**.)

**What to do there:**

1. Create a new API key pair.
2. **Restrict permissions** while learning: e.g. **read-only** first; add **spot trading** only when you intentionally test orders.
3. **Restrict by IP** if your server has a fixed IP (advanced).
4. Store the **secret** immediately—it may be shown only once.

**Testnet (fake money, for developers):**  
Binance maintains a **Spot Test Network** for API practice without real money. As of this writing, the testnet landing page is typically:

- [https://testnet.binance.vision/](https://testnet.binance.vision/)

Log in with GitHub or the method Binance testnet requires **on that site**, generate **testnet** API keys there, and use the **testnet base URLs** from Binance’s current documentation—not the main `api.binance.com` URLs. **Always** read Binance’s latest testnet docs because URLs and signup steps change.

**Main site keys ≠ testnet keys.** Never mix them in the same `.env` without understanding which base URL your code uses.

**Important:** Regulations and product names vary by country; Binance may not serve your region. If Binance is unavailable to you, the **same ideas** apply to other exchanges supported by **`ccxt`**—but you must change configuration and endpoints in your own fork; this course uses Binance as the documented example.

---

### 2. Finnhub — news / sentiment (optional)

Used when sentiment features are enabled. Typical env var:

- `FINNHUB_API_KEY`

**Where to get a key:**

1. Open **[https://finnhub.io](https://finnhub.io)**.
2. **Register** for an account.
3. In the **dashboard**, find your **API key** (free tiers have rate limits—read their pricing page).

**Docs (reference):** [https://finnhub.io/docs/api](https://finnhub.io/docs/api)

---

### 3. IBM Quantum (optional — only if you enable IBM backends)

The `quantum/backends.py` path may use an IBM token if you want IBM hardware/simulators instead of local Aer only. Typical env vars mentioned in code:

- `QISKIT_RUNTIME_TOKEN` or `IBMQ_API_KEY` / `IBMQ_TOKEN` (see your checkout of `quantum/backends.py`)

**Where to look:**

- **[https://quantum.ibm.com/](https://quantum.ibm.com/)** — create an IBM Quantum account; obtain API token from the account / platform settings as documented by IBM.

Most learners can **skip** this entirely and rely on **classical** portfolio code or local simulators.

---

### 4. Other APIs (not required for the core Bottie course)

The repository may contain **subfolders** (e.g. Node tools, Claude/OpenAI selectors) that mention:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Those are for **other experiments** in those folders, not for the minimal “Python engine + FastAPI” path. You can ignore them until you open those projects.

---

## Part D — How keys reach this project

1. You create keys on the **provider’s website** (Binance, Finnhub, …).
2. You put them in a **`.env`** file in your project folder (or in your host’s secret store for production)—**never commit** `.env` to Git.
3. The Python code reads `os.environ["BINANCE_API_KEY"]` etc., or `python-dotenv` loads `.env` at startup.

See [Getting started — full application repo](../GETTING_STARTED.md#environment-variables-full-app) for where `.env` lives when you run the stack (this **docs** repo has no app entry point).

---

## Part E — Minimal “first week” path

| Day | You do |
|-----|--------|
| 1 | Install Python; verify `python --version`. |
| 2 | Clone **this docs** repo; venv; `pip install -r requirements-docs.txt`; run `mkdocs serve` and read Chapter 1. |
| 3 | When ready for hands-on code: clone the **application** repo; venv; `pip install -r requirements.txt`; run `scripts/smoke.py` without exchange keys. |
| 4 | (Optional) Create **Binance testnet** keys; add `.env` in the **application** repo; explore read-only endpoints. |
| 5 | (Optional) Add Finnhub key; enable sentiment per application repo docs. |

---

## Part F — Self-check

1. In one sentence, what is an API?
2. Name two pieces Binance usually gives you for API access.
3. Where do you **not** put those pieces? (Name one place.)

**Sample answers:** (1) A machine-readable way for programs to talk to a service over the network. (2) API key and secret. (3) Public GitHub, Discord, email to strangers, screenshots on social media.

---

## Next steps

- [Getting started — install and run](../GETTING_STARTED.md)
- [Chapter 1 — Architecture](../chapter-01-overview/README.md)

---

## For course creators: charge money or ask for donations?

See [Note for creators — pricing and donations](../NOTE_FOR_CREATORS.md).
