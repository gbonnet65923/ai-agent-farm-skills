# ready_grok_reg — DrissionPage Grok Registration Tool

Рабочая директория: `C:\Users\User\Desktop\авторег проект\ready_grok_reg\`

## Why this works when Playwright fails

accounts.x.ai uses Cloudflare Turnstile with CDP-browser detection. Playwright, Playwright-stealth, rebrowser-playwright, and nodriver all fail because Cloudflare checks `MouseEvent.screenX/screenY` — CDP sends (0,0) for every mouse event, which is a hard bot signal.

The `turnstilePatch/` Chrome extension (MV3, `document_start`, MAIN world) patches `MouseEvent.prototype.screenX` and `screenY` to random values before any page script runs. DrissionPage supports Chrome extensions, Playwright doesn't.

## Key files

| File | Purpose |
|------|---------|
| `DrissionPage_example.py` | Main script (1401 lines) — full registration flow |
| `email_register_t_online.py` | t-online.de IMAP module (reads `working_mails.txt`) |
| `email_register.py` | DuckMail module (fallback, requires config.json) |
| `config.json` | Config (browser_proxy, run.count, API settings) |
| `turnstilePatch/manifest.json` | MV3 manifest, `document_start`, MAIN world |
| `turnstilePatch/script.js` | Patches `MouseEvent.screenX/screenY` to random values |

## Registration flow

1. `start_browser()` — DrissionPage Chromium with Turnstile extension + browser_proxy from config.json
2. `open_signup_page()` — navigate to `https://accounts.x.ai/sign-up?redirect=grok-com`
3. `click_email_signup_button()` — JS-based button finder (multi-language)
4. `fill_email_and_submit()` — gets email from `email_register_t_online.py`, fills via native value setter + React events
5. `fill_code_and_submit()` — polls IMAP for OTP, fills OTP input (single-field or multi-box)
6. `fill_profile_form()` — fills name + password, clicks through
7. Extract SSO token → write to `sso/sso_<timestamp>.txt`

## Config

```json
{
    "run": {"count": 3},
    "browser_proxy": "http://bpuser-XXX:YYY_hardsession-ZZZ@residential-x.bpproxy.at:1000",
    "proxy": "",
    "duckmail_api_base": "https://api.duckmail.sbs",
    "duckmail_bearer": "",
    "api": {"endpoint": "", "token": "", "append": true}
}
```

## Dependencies

- `DrissionPage==4.1.0.9`
- `curl_cffi>=0.7.0`
- Python 3.10+ (not in hermes venv — use system Python)

## Pitfalls

1. **Cloudflare blocks datacenter proxies** — use residential bpproxy only
2. **t-online.de IMAP** — `email_register_t_online.py` reads from `C:\Users\User\Downloads\Telegram Desktop\working_mails.txt` (17,893 emails)
3. **config.json must exist** — create from `config.example.json` if missing
4. **DrissionPage version** — 4.1.0.0b14 works, exact version not critical
5. **Do NOT use Playwright for Grok** — it will always hit Cloudflare. Use this tool.