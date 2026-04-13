# Bottie — course book (MkDocs)

This repository contains **only** the **Berta Chapters–style course**: guided chapters, exercises slots, and links to concepts—built with **MkDocs**.

- **Live site:** [https://newbot.berta.one](https://newbot.berta.one)
- **Build locally (matches the live site):** `pip install -r requirements-docs.txt` then `mkdocs serve -f mkdocs-material.yml`
- **Lighter local build (ReadTheDocs theme, no Material):** `pip install mkdocs pymdown-extensions` then `mkdocs serve -f mkdocs.yml`

The full **Bottie trading application** (FastAPI, engine, ML, etc.) is maintained separately; this repo is documentation and learning material only.

## Contents

| Path | Purpose |
|------|--------|
| [`chapters/`](chapters/index.md) | Course spine (Chapter 0–7, curriculum, getting started) |
| [`mkdocs.yml`](mkdocs.yml) | Default ReadTheDocs-style theme |
| [`mkdocs-material.yml`](mkdocs-material.yml) | Optional Material theme |
| [`requirements-docs.txt`](requirements-docs.txt) | MkDocs dependencies for CI/Netlify |

## License

[MIT](LICENSE)
