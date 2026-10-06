# AI Provider Autoreg Pipeline Status — August 2026

## Working

### g0i.ai (g0i_fast_reg.py)
- Script: `C:/Users/User/Desktop/_PROJECTS/hermes-unified/data/skills/registration/g0i-bulk-registration/scripts/g0i_fast_reg.py`
- Uses persistent Chrome MCP profile: `mcp-chrome-b32b429`
- Email: t-online.de from `working_mails.txt` (17,895 emails)
- Flow: Playwright → g0i.ai/register → Turnstile → IMAP OTP → API key extraction
- API key format: `sk-[a-f0-9]{64}`
- Base URL: `https://api.g0i.ai/v1`

### Email Infrastructure
- **baradok609@gmail.com**: IMAP `imap.gmail.com:993` / `baradok609@gmail.com` / `[REDACTED_IMAP_APP_PASSWORD]` (App Password)
- Dot-trick aliasing: `b.aradok609@gmail.com`, `ba.radok609@gmail.com`, etc. → all to same inbox
- **t-online.de**: 17,895 emails in `working_mails.txt` (format: `email:password`), IMAP `secureimap.t-online.de:993`
- t-online.de IMAP has encoding issues: "unknown-8bit" errors on some emails

## Broken (as of August 2026)

### ai_gateway_autoreg.py
- Script: `C:/Users/User/Desktop/авторег проект/ai_gateway_autoreg.py`
- 13 providers: Groq, Mistral, DeepSeek, Cohere, OpenRouter, Together AI, Fireworks AI, NVIDIA NIM, HuggingFace, Replicate, Google AI, Vercel, ZhipuAI
- All 5 tested (Groq, Mistral, DeepSeek, Cohere, OpenRouter) returned 0 keys
- Issues:
  - Playwright selectors outdated (forms changed)
  - t-online.de IMAP encoding: "unknown-8bit"
  - Cloudflare blocks on multiple platforms
  - Old verification codes picked up from inbox instead of fresh ones

### github-farm (d4ncboz/github-farm)
- Repo: `C:/Users/User/Desktop/farm/gh-farm/`
- Actually an OAuth HARVESTER, not GitHub account creator
- Requires pre-existing GitHub accounts to OAuth into Tabi AI ($120), GoRouter ($70), CodeBuddy (250 credits)
- Cannot be used standalone — needs GitHub account creation pipeline first
- ZTE proxy (192.168.0.4:8080-8091) blocked by Cloudflare on GitHub signup

## Proxy Infrastructure

### ZTE 4G (lifecell Ukraine)
- Script: `C:/Users/User/Desktop/farm/farm_proxy.py`
- Bind: 192.168.0.4, ports 8080-8091 (12 ports)
- Status: Working, IP rotates on ZTE modem reconnect
- Limitation: Cloudflare blocks ZTE IPs for many sites
- IP rotation via ZTE web interface is unreliable