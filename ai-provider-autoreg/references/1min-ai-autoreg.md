# 1min.ai Auto-Registration Reference

## Platform Profile (Sep 2026)

| Field | Value |
|---|---|
| URL | `app.1min.ai` |
| API | `api.1min.ai` |
| Social API | `social-api.1min.ai` |
| Framework | React SPA (NOT Next.js — no `__NEXT_DATA__`) |
| Auth | Google Identity Services (`accounts.google.com/gsi/client`) + email/password fallback |
| Payments | LemonSqueezy (`app.lemonsqueezy.com/js/lemon.js`) |
| Analytics | Google Analytics, Hotjar, Sentry, Cloudflare Insights |
| Anti-bot | Hotjar blocks `HeadlessChrome` UA; Cloudflare CDN; no Turnstile/reCAPTCHA detected |
| Main JS | `app.1min.ai/assets/index-Bo_qGH04.js` |
| Captcha | None detected on signup page |

## Available Models (from user report)

- GPT-6 Astra
- GPT-5.6 Terra / Sol / Luna
- Claude 4.8 Opus
- Claude Fable 5.1
- + Qwen, Gemini, DeepSeek models

## API Details

- **Base**: `https://api.1min.ai`
- **Chat endpoint**: `POST /api/chat-with-ai`
- **Rate limit**: 180 req/min per key
- **Free credits**: issued automatically on signup + API key creation
- **No credit card required** for free tier
- **Referral program**: accumulates bonus credits

## Signup Flow

1. Navigate to `app.1min.ai`
2. Click "Sign Up" button in header → triggers modal (SPA routing — `/sign-up` exists but shows main feed without auth state)
3. Google OAuth is primary (Google Identity Services loaded)
4. Email/password fallback available
5. Email verification: OTP code or verification link sent to email
6. After verification → API key page at `/members`

## API Key Extraction

- Key management page: `app.1min.ai/members`
- Key format: unknown (not standard `sk-` prefix) — extract with fallback regex `[a-zA-Z0-9_-]{32,64}`
- "Show Key" / "Create API Key" button on members page

## Multi-Account Strategy

- Gmail aliases (`user+1minN@gmail.com`) — confirmed working
- IMAP: `baradok609@gmail.com` with app password
- Proxy rotation supported (no extreme anti-bot, but Hotjar UA filtering)
- Headless works with proper UA spoofing (avoid `HeadlessChrome` string)

## Autoreg Script

`C:\Users\User\Desktop\1min_autoreg.py` — Playwright-based:
- `--count N` — number of accounts
- `--headless` — headless mode
- Gmail alias pool + IMAP OTP
- Auto API key extraction
- Saves to `C:\Users\User\tmp\1min_keys.json`

## Pitfalls

1. **Hotjar blocks headless UA** — `HeadlessChrome/153.0.0.0` detected. Spoof as regular Chrome.
2. **Sign-up page is auth-gated** — clicking "Sign Up" opens modal; direct `/sign-up` navigation shows feed without auth. Need to interact with modal.
3. **Google OAuth is primary** — if email/password button not immediately visible, click "Sign up with email" or similar link.
4. **API key format unknown** — use broad regex fallback. If not found, save page HTML for manual analysis.
5. **No captcha** — 1min.ai relies on Hotjar + Cloudflare, no Turnstile/reCAPTCHA on signup. Good for automation.