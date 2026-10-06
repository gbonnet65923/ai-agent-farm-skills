# Turnstile Shadow DOM Bypass

## Discovery

The Cloudflare Turnstile widget on `accounts.x.ai` uses **shadow DOM** to encapsulate the challenge iframe. The standard approach of injecting the token into `cf-turnstile-response` hidden inputs often fails because the React SPA reads the token from the widget's callback, not from the DOM.

## The Bypass

The DrissionPage-based approach (from ReinerBRO/grok-register) directly accesses the shadow root of the Turnstile widget container and clicks the challenge button inside the iframe. This triggers the Turnstile challenge, which is auto-solved because the browser's `MouseEvent.screenX/screenY` are patched to realistic values.

## Code Pattern

```python
# Find the cf-turnstile-response input
challengeSolution = page.ele("@name=cf-turnstile-response")
# Get its parent (the widget container with shadow DOM)
challengeWrapper = challengeSolution.parent()
# Access the shadow root to get the iframe
challengeIframe = challengeWrapper.shadow_root.ele("tag:iframe")
# Inject JavaScript into the iframe to patch MouseEvent
challengeIframe.run_js("""
    window.dtp = 1
    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
    let screenX = getRandomInt(800, 1200);
    let screenY = getRandomInt(400, 600);
    Object.defineProperty(MouseEvent.prototype, 'screenX', { value: screenX });
    Object.defineProperty(MouseEvent.prototype, 'screenY', { value: screenY });
""")
# Access the iframe's body shadow root to find the challenge button
challengeIframeBody = challengeIframe.ele("tag:body").shadow_root
challengeButton = challengeIframeBody.ele("tag:input")
# Click the button to trigger the challenge
challengeButton.click()
```

## Why It Works

Cloudflare Turnstile uses behavioral detection to determine if the visitor is human. One signal is the `screenX/screenY` coordinates of mouse events. In headless/automated browsers, these are often 0 or unrealistic values. By patching `MouseEvent.prototype.screenX/screenY` to random values between 800-1200 (x) and 400-600 (y), the behavioral detection passes, and the Turnstile auto-solves without showing a challenge.

## When to Use

- When 2captcha fails to solve the profile-page Turnstile (sitekey `0x4AAAAAAAhr9JGVDZbrZOo0`)
- When you need faster account creation without external captcha services
- The code-page Turnstile (sitekey `0x4AAAAAAADnQ4F4U8W2nQyH`) is also bypassed by this method

## Requirements

- DrissionPage library (`pip install DrissionPage==4.1.0.9`)
- Chrome/Chromium browser
- The Turnstile Patcher Chrome extension (in `turnstilePatch/` directory of the repo) — this patches MouseEvent at the content script level for the initial page load

## Limitations

- This only works with DrissionPage (not Playwright) because DrissionPage provides `shadow_root` access
- The Chrome extension must be loaded at browser startup
- Some Turnstile challenges may still require manual solving if the behavioral detection is more sophisticated