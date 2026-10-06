# DuckMail API Reference

**Base URL**: `https://api.duckmail.sbs`
**Auth**: Most endpoints require no auth. Only `/messages` and `/messages/{id}` need a Bearer token.

## Endpoints

### GET /domains
Returns available email domains. No auth needed.
```bash
curl https://api.duckmail.sbs/domains
```
Returns: `{"hydra:member": [{"domain": "duckmail.sbs", ...}, ...], "hydra:totalItems": 19}`

### POST /accounts
Create a new temporary email account. No auth needed.
```bash
curl -X POST https://api.duckmail.sbs/accounts \
  -H "Content-Type: application/json" \
  -d '{"address": "user@duckmail.sbs", "password": "StrongPass123!"}'
```
Returns: `{"id": "...", "address": "...", "isActive": false, "expiresAt": "2026-08-14T..."}`

### POST /token
Get JWT auth token for an account. No auth needed.
```bash
curl -X POST https://api.duckmail.sbs/token \
  -H "Content-Type: application/json" \
  -d '{"address": "user@duckmail.sbs", "password": "StrongPass123!"}'
```
Returns: `{"id": "...", "token": "eyJhbG..."}`

### GET /messages
List messages in the inbox. Requires Bearer token.
```bash
curl https://api.duckmail.sbs/messages \
  -H "Authorization: Bearer <token>"
```
Returns: `{"hydra:member": [...], "hydra:totalItems": 0}`

### GET /messages/{id}
Get a specific message. Requires Bearer token.
```bash
curl https://api.duckmail.sbs/messages/{id} \
  -H "Authorization: Bearer <token>"
```
Returns: Full message with subject, intro, text, html fields.

## Notes
- mail.tm-compatible API — code written for mail.tm works with s/base URL change
- No bearer token needed for account creation or token retrieval
- No rate limiting observed (tested with 170+ accounts in ~7 minutes)
- 19 domains available, rotates automatically
- Emails expire after ~24 hours
- `isActive: false` on creation — accounts are created inactive but still receive email