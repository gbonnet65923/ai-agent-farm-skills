# Device Auth Flow Completion

## Critical Pattern
After signup is complete, the device auth CLI does NOT automatically receive the token. The browser must be explicitly navigated back to the device auth URL to complete the authorization.

## Flow
1. Signup completes (profile form submitted)
2. **Navigate back to device auth URL**: `await page.goto(url, ...)`
3. **Click "Continue"**: User is now logged in, so the sign-in page shows the authorization card
4. **Click "Authorize"** or "Allow": This redirects to the localhost callback URL
5. Device auth CLI receives the callback and writes the token to `auth.json`

## Working Code
```python
# After signup (profile form submitted)
print(f"Going back to device auth URL: {url}")
await page.goto(url, timeout=30000, wait_until="domcontentloaded")
await page.wait_for_timeout(3000)

# Click Continue (should show authorization page now)
btn = page.locator("button:has-text('Продолжить')").first
if await btn.count() == 0:
    btn = page.locator("button:has-text('Continue')").first
if await btn.count() > 0:
    await btn.click()
    await page.wait_for_timeout(5000)

# Click Authorize
auth_btn = page.locator("button:has-text('Authorize'), button:has-text('Allow')").first
if await auth_btn.count() > 0:
    await auth_btn.click()
    await page.wait_for_timeout(5000)

# Now wait for token in auth.json
for w in range(60):
    await asyncio.sleep(2)
    auth = load_auth()
    if f"https://auth.x.ai/oauth2/{email_addr}" in auth:
        # Token received!
        break
```

## Common Failure
Without this step, the account is created but the token is NEVER saved. The device auth CLI times out after 300 seconds waiting for a callback that never arrives because the browser never redirected to localhost.