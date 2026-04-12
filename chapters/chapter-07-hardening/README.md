# Chapter 7 — Hardening & operations

**Guided time:** 5–7 hours  
**Prerequisites:** [Chapter 6 — Quantum & sentiment](../chapter-06-quantum-sentiment/README.md)  

**Back to:** [Home](../index.md)

---

## 1. Purpose

Working code is not finished code. This chapter is your **operational spine**: how to run safely, test meaningfully, deploy without leaking secrets, and recover when something breaks at 02:00.

**The Bottie codebase is the tool as it exists in the repo**—it does not automatically track every Binance or Finnhub change. For a **repeatable playbook** (classify errors, search the repo, align `.env`, read provider docs, upgrade deps carefully), read **[The tool as-is — adapting when things change](../ADAPTING_WHEN_THINGS_CHANGE.md)** first when something used to work and now does not.

---

## 2. Objectives

1. Apply a **pre-flight checklist** before enabling real trading.
2. Manage **secrets** (`.env`, CI variables, logs).
3. Run **`pytest`** and triage common failures.
4. Maintain a **personal runbook** (bullets, not essays) for recurring tasks.

---

## 3. Threat model (proportionate)

You are not defending a national bank—but **API keys** are bearer tokens. Assume:

- Anyone with repo + `.env` can **place trades** if permissions allow.
- Logs may accidentally print **positions** or **keys** if you add debug prints carelessly.
- A public tunnel + weak auth could expose **control routes**.

**Mitigations:** least-privilege API keys, IP allowlists where supported, separate **testnet**, **TRADE_ENABLED** guardrails, structured logging with redaction.

---

## 4. Secrets hygiene

- **Never commit** `.env` (verify `.gitignore`).
- **Rotate** keys if leaked (even “just” in a screenshot).
- **Separate** keys per environment (dev/staging/prod).
- **Document** required variables in `.env.example` **without real values**.

---

## 5. Trading safety ladder

Suggested progression:

1. **Read-only** exchange calls (if available) — verify connectivity.
2. **Testnet** orders — tiny sizes, intentional slippage acceptance.
3. **Mainnet micro size** — after `pytest` green and manual checklist signed.
4. Scale only with **measured** risk caps.

---

## 6. Configuration toggles (review)

Before mainnet sessions, explicitly verify:

- `TRADE_ENABLED` meaning in your branch
- `EXECUTION_RUNTIME_ENABLED` or equivalents- Cooldown and max position env vars
- Sentiment / quantum flags (off unless needed)

Keep a **printed card** beside your monitor while learning.

---

## 7. Testing strategy

### Unit / fast tests

```bash
pytest tests/ -q
```

Expect **tens of seconds to minutes** depending on machine and quantum imports.

### Smoke integration

```bash
python scripts/smoke.py
```

### HTTP integration

Some tests assume `localhost:8000` or remote URLs—read headers in each file. Mark **skipped** tests in forks if you lack network.

### Flaky tests

Retries may be needed for network-bound tests; prefer **deterministic** unit tests for CI gates.

---

## 8. Observability

- **Structured logs** beat `print`.
- **Correlation IDs** help trace a single bar through subsystems (advanced improvement).
- **Metrics** (Prometheus, etc.) are optional but valuable at scale—out of scope for this baseline chapter.

---

## 9. Deployment notes (high level)

Typical PaaS (Render, Railway, etc.):

- Set env vars in the **host UI**, not in repo.
- Align **Python version** with local dev.
- Watch **cold start** time for large imports.
- Put **static frontend** on CDN; restrict CORS accordingly.

Refer to `docs/deployment.md` if maintained in your fork (content may consolidate older notes).

---

## 10. Incident response (lightweight)

If something goes wrong live:

1. **Pause trading** (`TRADE_ENABLED=0` or stop process).
2. **Revoke** API keys if compromise suspected.
3. **Snapshot logs** and config (redact secrets).
4. **Reproduce** in testnet.
5. **Patch** with a test that fails before / passes after.

---

## 11. Checklist (copy into your runbook)

- [ ] `.env` gitignored; `.env.example` current
- [ ] Keys are testnet or minimal-scope mainnet
- [ ] `pytest` green on commit SHA you deploy
- [ ] Smoke script green
- [ ] CORS not wide open in production
- [ ] Dashboard polling interval sane
- [ ] Backup of JSON state files if you rely on them
- [ ] Rollback plan documented (previous container image / git tag)

---

## 12. Labs

### Lab 7.1 — Redact logs (30 min)

Add a temporary debug print—confirm it **does not** ship to prod. Remove it.

### Lab 7.2 — CI stub (60 min)

Write a GitHub Actions / local script that runs `pytest -q` on push (optional).

### Lab 7.3 — Runbook (45 min)

Maintain `RUNBOOK.md` (personal or team) with **10** bullet commands: start, stop, health check, smoke, tests.

---

## 13. Course completion criteria

You completed the guided path when you can **teach** someone else:

1. Architecture diagram (Chapter 1).
2. Clean environment + health check (Chapter 2).
3. TestClient probing (Chapter 3).
4. Bar-to-execution trace (Chapter 4).
5. ML probability contract (Chapter 5).
6. Optional features trade-offs (Chapter 6).
7. Operational checklist (this chapter).

---

## 14. Growing the course with Berta

Add `chapter-08-…` folders with the same skeleton:

- `README.md` (long-form like these)
- `notebooks/`
- `exercises/` (+ `solutions/` if paid tier)

Feed Berta the **file tree** and **contracts** (function signatures, env vars). Human-review every generated claim against the code.

---

Congratulations — now **maintain** the docs when code changes. Stale training hurts more than no training.

Back to [home](../index.md).
