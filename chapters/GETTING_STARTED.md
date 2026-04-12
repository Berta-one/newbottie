# Getting started

This repository contains **only the Bottie course** (Markdown chapters + MkDocs). There is **no** application code here—no `render_api.py`, no trading engine to run from this clone.

If you are **new to Python or APIs**, read **[Chapter 0 — New to Python and APIs](chapter-00-beginners-apis-and-keys/README.md)** first, then return here.

**The full Bottie codebase** (FastAPI, engine, ML, tests) lives in a **separate repository**—clone it when you are ready to run the stack on your machine. This course describes that architecture and how to operate it; the implementation is maintained alongside it, not inside this docs repo.

When exchanges or libraries change, use **[The tool as-is — adapting when things change](ADAPTING_WHEN_THINGS_CHANGE.md)** (written for the full project; paths refer to that codebase).

---

## 1. Prerequisites

- **Python 3.12** (recommended; matches Netlify / `PYTHON_VERSION`).
- **Git** and a terminal (PowerShell on Windows, bash/zsh on macOS/Linux).
- **Network** for `pip install`.

---

## 2. Clone this repository (course only)

```bash
git clone https://github.com/luigipascal/newbottie.git
cd newbottie
```

(Use your fork URL if you forked the site.)

---

## 3. Virtual environment and MkDocs

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-docs.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-docs.txt
```

**Build the documentation site locally:**

```bash
mkdocs serve -f mkdocs.yml -a 127.0.0.1:8001
```

Open **http://127.0.0.1:8001** — you should see the same structure as [newbot.berta.one](https://newbot.berta.one).

### Optional: Material theme

```bash
pip install -r requirements-docs-material.txt
mkdocs serve -f mkdocs-material.yml -a 127.0.0.1:8001
```

On Windows, if Material install fails (`Errno 22`), stay on **`mkdocs.yml`** or **`mkdocs-lite.yml`**—content is the same.

---

## 4. Full application (separate repo) {#environment-variables-full-app}

To **run the API, engine, smoke tests, and pytest** as described in later chapters, clone the **application** repository (example):

```bash
git clone https://github.com/luigipascal/Bottie.git
cd Bottie
# follow that repo's README: venv, requirements.txt, render_api.py, scripts/smoke.py, pytest
```

Chapter text refers to files like `render_api.py`, `engine/`, and `api/` **in that codebase**, not in this docs-only tree.

**Environment variables:** in the application repo, copy `.env.example` to `.env` beside `render_api.py` (or use your host’s secret store in production). **Never commit** `.env` or API keys.

---

## 5. Troubleshooting

### `mkdocs` not found

Activate your venv first, or run `python -m mkdocs serve ...`.

### Port 8001 in use

Use another port: `mkdocs serve -f mkdocs.yml -a 127.0.0.1:8010`

---

## 6. What to do next

Open **[Chapter 1 — Overview](chapter-01-overview/README.md)** and continue the path in **[Curriculum](CURRICULUM.md)**.
