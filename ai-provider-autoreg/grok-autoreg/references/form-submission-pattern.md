# Form Submission Pattern (v16 Working)

## The Problem
The profile page "Завершить регистрацию" (Complete sign up) form submission is unreliable. After solving the Turnstile and clicking the button, the form sometimes:
- Redirects to the consent page (success — ~50% of runs)
- Stays on sign-up page with GET params appended (failure — form submits as GET instead of POST)
- Stays on sign-up page with no URL change (button click doesn't trigger form)

## Root Cause
The Turnstile token injection works, but the form submission behavior depends on whether the Cloudflare Turnstile server-side validation accepts the token. When the token is valid:
- Button click → POST redirect → consent page
When the token is invalid:
- Button click → GET params → same page (server rejects the form)

The sitekey is `0x4AAAAAAAhr9JGVDZbrZOo0` (fallback; actual sitekey extracted from iframe `src` attribute).

## Working Pattern (dani.thaler99 run)
```
[S10] Turnstile solved!
[S11] Clicked 'Завершить регистрацию' -> https://accounts.x.ai/account
[S11] After submit: https://accounts.x.ai/oauth2/consent?...
[S12] Redirected: https://accounts.x.ai/oauth2/consent?...
```

The button click redirected to `/account`, then `form.submit()` redirected to `/oauth2/consent`. This was with Chromium (not Chrome), `--disable-blink-features=AutomationControlled`, and `--no-sandbox`.

## Working Pattern (p261250 run, v15)
```
[10] Turnstile solved!
[10] Clicked 'Завершить регистрацию' -> https://accounts.x.ai/oauth2/device?user_code=TGQT-FDR8
[11] Redirected to: https://accounts.x.ai/oauth2/device?user_code=TGQT-FDR8
```

This was with `channel="chrome"` (system Chrome), `launch_persistent_context` with temp user_data_dir.

## Non-Working Pattern (bobozkurt, christian.klausch87, felixschade)
```
[S10] Turnstile solved!
[S11] Clicked 'Завершить регистрацию' -> https://accounts.x.ai/sign-up
[S11] After submit: https://accounts.x.ai/sign-up?email=...&givenName=Max&familyName=Mustermann
```

The form submits as GET with query params. The account may or may not be created. The OAuth fallback navigates to the OAuth URL but the sign-in page is shown (account not created).

## Code Pattern
```python
# Click button
btn = page.locator(f"button:has-text('Завершить регистрацию'):not([class*='onetrust'])").first
if await btn.count() > 0:
    await btn.click()
    await page.wait_for_timeout(3000)
    # Force form submission
    await page.evaluate("""
        const forms = document.querySelectorAll('form');
        for (const f of forms) {
            if (f.querySelector('input[type="password"]')) {
                f.submit();
                break;
            }
        }
    """)
    await page.wait_for_timeout(5000)
```

## Key Insight
Even when the form doesn't redirect, the account MIGHT still be created. The OAuth fallback (navigating to the OAuth URL after signup) can still work if the browser is logged in. But if the sign-in page is shown, the account was NOT created.