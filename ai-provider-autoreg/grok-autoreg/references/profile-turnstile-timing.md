# Profile Turnstile Detection Timing

## Problem
The v13 script checks for the profile Turnstile at line 406:
```python
turnstile2 = page.locator("iframe[src*='challenges.cloudflare.com']").first
if await turnstile2.count() > 0:
    sitekey = await turnstile2.get_attribute("src")
    ...
```

But `count()` returns 0 if the Turnstile iframe hasn't loaded yet. The profile form renders BEFORE the Turnstile widget, so the script misses it and submits without solving the captcha.

## Fix
Replace the `count()` + `get_attribute()` pattern with `wait_for_selector()` + explicit timeout:

```python
try:
    turnstile_iframe = page.locator("iframe[src*='challenges.cloudflare.com']").first
    await turnstile_iframe.wait_for(state="attached", timeout=10000)
    # Extract sitekey from the fully loaded iframe
    src = await turnstile_iframe.get_attribute("src")
    sk = re.search(r'sitekey=([^&]+)', src or "")
    if sk:
        sitekey = sk.group(1)
        token = await solve_turnstile(sitekey, page.url, timeout=45)
        if token:
            await page.evaluate(f"""document.querySelector('input[name="cf-turnstile-response"]').value = {json.dumps(token)}""")
except Exception:
    print("  Profile Turnstile: not found or timed out")
```

## Sitekey
Profile page Turnstile uses sitekey `0x4AAAAAAAhr9JGVDZbrZOo0` — this IS solvable via 2captcha (~30s avg).

Code page Turnstile uses sitekey `0x4AAAAAAADnQ4F4U8W2nQyH` — ALWAYS unsolvable via 2captcha. Do not wait more than 30s for it.