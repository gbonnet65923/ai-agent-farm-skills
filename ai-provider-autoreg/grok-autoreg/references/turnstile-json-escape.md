# Turnstile Token JSON Escaping

The Turnstile token returned by 2Captcha is a long opaque string like:
```
1.7iQyv0Qs12EGBU8PpuyVlKig_yZf_G8Q-Tcu8r0OY7mDbX0QjCk...
```

This string can contain dots, underscores, dashes, and other characters that break JavaScript string literals when interpolated directly.

## ❌ Never Do This
```python
await page.evaluate(f"el.value = '{token}';")
# Causes: SyntaxError: Invalid left-hand side in assignment
# When token contains dots or special chars: el.value = 1.7iQyv0Qs... (invalid)
```

## ✅ Always Do This
```python
import json
await page.evaluate(f"const el = document.querySelector('input[name=\"cf-turnstile-response\"]'); if (el) el.value = {json.dumps(token)};")
```

`json.dumps()` produces a properly escaped JavaScript string literal:
- Strings with dots: `"1.7iQyv0Qs..."` (valid JS)
- Strings with quotes: `"it's \"good\""` (properly escaped)
- Null/None: `null` (valid JS)

## Full Injection Pattern
```python
token = await solve_turnstile(sitekey, pageurl)
if token:
    import json
    await page.evaluate(f"const el = document.querySelector('input[name=\"cf-turnstile-response\"]'); if (el) el.value = {json.dumps(token)};")
    await page.wait_for_timeout(500)
```

## Why 2Captcha Returns "unsolvable"
The Turnstile on the verification page is often reported as "unsolvable" by 2Captcha. This is a known issue with Cloudflare Turnstile — the challenge is intentionally easy for humans but hard for automated solvers. The page still advances without the Turnstile being solved (the code submission itself triggers the next step). So treat "unsolvable" as a non-fatal warning, not an error.