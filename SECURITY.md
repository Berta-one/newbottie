# Security policy

## Supported versions

Security-sensitive fixes are applied to the **default branch** (`main`) as maintainers are able. There is no long-term guarantee of backports to older tags.

## Reporting a vulnerability

**Do not** open a **public** issue for undisclosed security problems in this codebase — that can put other users at risk before a fix is ready.

**Preferred:** use GitHub’s **private vulnerability reporting** for this repository:

1. Open the repo on GitHub → **Security** tab.
2. Choose **Report a vulnerability** (or follow the flow under **Security advisories**).

If that option is missing, the repository owner must enable **Private vulnerability reporting** in **Settings** → **Code security and analysis** → **Private vulnerability reporting** for this repo.

In your report, please include:

- A clear description and suspected impact
- Steps to reproduce (if safe to share)
- Affected area of the code or dependency (if known)

Maintainers will aim to acknowledge within a few business days and coordinate a fix and disclosure timeline.

## What is in scope

- Security defects in **code in this repository** (for example: unsafe handling of untrusted input in the app, auth/session issues in the API surface we control, dependency issues we can reasonably address).

## What is out of scope

- Problems with **third-party** services (Binance, Finnhub, hosting providers) — report those to the vendor.
- Issues that require **your** leaked API keys or a misconfigured `.env` — rotate keys with the exchange/provider and keep secrets out of git.
- General trading risk, market loss, or “the bot lost money” — not a software vulnerability.

## Secure use

- Never commit `.env`, API keys, or tokens. Use [`.env.example`](../.env.example) as a template only.
- Prefer **testnet** and **least-privilege** API keys while developing.
