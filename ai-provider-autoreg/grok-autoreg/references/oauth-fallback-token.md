# OAuth Fallback Token Retrieval

After signup completes (profile form submitted), the browser is logged in but the device auth CLI may not have received the callback. The reliable fallback:

## Flow
1. `subprocess.run([grok_exe, "logout"], capture_output=True, timeout=10)` — clear old auth
2. `subprocess.Popen([grok_exe, "login", "--oauth"], ...)` — start OAuth flow
3. Parse OAuth URL from CLI output: `re.search(r'(https://auth\.x\.ai/oauth2/authorize\?\S+)', line)`
4. `page.goto(oauth_url)` — navigate browser to OAuth URL
5. If browser is logged in → auto-redirects to `127.0.0.1:XXXXX/callback?...`
6. If not logged in → try clicking "Continue" or "Allow" buttons
7. `proc.communicate(timeout=30)` — wait for CLI to finish
8. Check `auth.json` for any key with `access_token`

## Code
```python
subprocess.run([GROK_EXE, "logout"], capture_output=True, timeout=10)
proc = subprocess.Popen([GROK_EXE, "login", "--oauth"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
oauth_url = None
for line in iter(proc.stdout.readline, ''):
    if not line and proc.poll() is not None: break
    m = re.search(r'(https://auth\.x\.ai/oauth2/authorize\?\S+)', line)
    if m: oauth_url = m.group(1); break

if oauth_url:
    await page.goto(oauth_url, timeout=15000)
    await page.wait_for_timeout(5000)
    for w in range(15):
        if "127.0.0.1" in page.url or "localhost" in page.url: break
        btn = page.locator("button:has-text('Continue'), button:has-text('Allow')").first
        if await btn.count() > 0: await btn.click()
        await page.wait_for_timeout(2000)
    proc.communicate(timeout=30)

auth = json.load(open(AUTH_JSON))
for key in auth:
    tok = auth[key].get("access_token") or auth[key].get("key", "")
    if tok: return tok
```

## Why It Works
The OAuth flow is simpler than device auth: the CLI prints an OAuth URL, the browser opens it, and since the browser is already logged in, it auto-redirects to localhost with the authorization code. The CLI picks up the redirect and writes the token to `auth.json`.