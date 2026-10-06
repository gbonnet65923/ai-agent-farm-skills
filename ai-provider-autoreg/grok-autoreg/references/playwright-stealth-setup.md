# Playwright Stealth Setup for x.ai

## Installation

```bash
pip install playwright-stealth
```

## Import Pattern (2026-08-14 verified)

```python
from playwright_stealth import Stealth

# Correct usage:
stealth = Stealth()
await stealth.apply_stealth_async(page)

# WRONG - does NOT work:
# from playwright_stealth import stealth_async  # ImportError
# from playwright_stealth import stealth         # module, not callable
# await stealth(page)                            # TypeError
```

## Why Stealth Is Needed

Without stealth, Cloudflare detects the automated browser and blocks the Clerk JS library from loading. The page HTML loads fine, but `window.Clerk` is `undefined`. The form submission triggers a 403 error from Cloudflare.

With stealth applied, the Clerk JS loads successfully and form submission works (when combined with residential proxy).

## Stealth + Residential Proxy

Stealth alone may not be enough — Cloudflare also checks the IP. Always combine with:
- bpproxy residential hardsession proxies (`C:/Users/User/tmp/bpproxy_hardsession_pool.txt`)
- Filter for `residential` lines (port 1000), not `datacenter` (port 2000)

## Launch Args

```python
browser = await p.chromium.launch(
    headless=headless,
    proxy={"server": proxy_url},
    args=["--no-sandbox"]  # --disable-blink-features=AutomationControlled breaks stealth
)
```

Do NOT use `--disable-blink-features=AutomationControlled` with stealth — stealth handles this internally.