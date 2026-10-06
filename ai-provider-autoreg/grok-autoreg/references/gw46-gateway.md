# Grok46 Gateway (gw46.py)

## Location
`C:\Users\User\Documents\grok46gw\gw46.py`

## Overview
A ready-made OpenAI-compatible API gateway for xAI's Grok models with OAuth auto-registration, device code flow, and SQLite-based account management.

## Features
- **OpenAI-compatible API**: `/v1/chat/completions`, `/v1/models`, `/v1/responses`
- **Multi-model support**: grok-4.6, grok-4.5, grok-4.3, grok-build-0.1
- **OAuth PKCE flow**: `/oauth/login` → user signs in browser → callback → token
- **Device code flow**: `/oauth/device` → user_code + verification_uri → `/oauth/device/poll`
- **SQLite database**: accounts stored in `grok46_accounts.db` with refresh tokens
- **API key pool**: round-robin rotation across all stored credentials
- **Token refresh**: automatic refresh for expired tokens (if refresh_token is available)

## Usage

```bash
# Start the gateway
cd ~/Documents/grok46gw
python gw46.py
# Listens on 127.0.0.1:20146 by default (configurable via GROK46_PORT)
```

## Getting Tokens via Device Code Flow

1. Start the gateway: `python gw46.py`
2. Request a device code: `GET http://127.0.0.1:20146/oauth/device`
3. Response includes `user_code` (e.g. `J2QB-MGQC`) and `verification_uri_complete` (e.g. `https://accounts.x.ai/oauth2/device?user_code=J2QB-MGQC`)
4. Open the verification URI in a browser
5. Sign in with an existing x.ai account (or create a new one)
6. Enter the user_code and authorize the application
7. Poll for the token: `GET http://127.0.0.1:20146/oauth/device/poll`
8. When authorized, the response includes the `access_token` and the token is saved to the database

## Account Management

- `GET /accounts` — list all stored accounts and API keys
- `POST /accounts/api-key?key=...&label=...` — add a manual API key
- `GET /health` — health check with credential count

## Environment Variables

- `GROK46_PORT` — port (default: 20146)
- `GROK46_HOST` — bind host (default: 127.0.0.1)
- `GROK46_DB` — SQLite DB path (default: `./grok46_accounts.db`)
- `XAI_API_KEYS` — comma-separated xAI API keys to add to the pool

## Database Schema

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at REAL,
    scope TEXT,
    created_at REAL DEFAULT (strftime('%s','now')),
    last_used_at REAL,
    use_count INTEGER DEFAULT 0
);

CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    label TEXT,
    created_at REAL DEFAULT (strftime('%s','now')),
    last_used_at REAL,
    use_count INTEGER DEFAULT 0
);
```

## OAuth Auto-Registration Flow

The gateway implements the full PKCE OAuth flow:
1. `GET /oauth/login` — redirects to x.ai OAuth authorization page with PKCE challenge
2. User signs in and authorizes in the browser
3. Browser redirects to `http://127.0.0.1:20146/oauth/callback?code=...`
4. Gateway exchanges the code for tokens using the PKCE verifier
5. Tokens are saved to the SQLite database and added to the credential pool

## Token Refresh

Tokens with `refresh_token` are automatically refreshed when they expire. The gateway calls the xAI token endpoint with `grant_type=refresh_token` to get new access tokens.