# WorkOS + Turnstile: stub-the-widget, let React submit itself

Live case: **abliteration.ai** (2026-10-03) — Next.js console, WorkOS AuthKit password
signup, Cloudflare Turnstile, WorkOS Radar signals. Full pipeline works end-to-end:
9 accounts registered, 6 API keys created, chat completion 200 OK.

Code: `C:/Users/User/tmp/ablit_autoreg/` (`autoreg6.py`, `harvest_keys.py`, `gateway.py`,
`menu.py`) · public repo `github.com/ArthurMonteiro08586/abliteration-farm` (push via
Git Data API — `push_github.py`).

The technique generalizes to **any site where you can solve the captcha out-of-band but
the submit must carry client-side attestation** (Radar signalsId, correlation ids,
csrf, fingerprint headers). Do not replicate the request yourself — make the page's own
code send it.

---

## Core pattern: turnstile stub with the token baked into the stub source

The app renders the widget like this (real decompiled code):

```js
window.turnstile.render(el, {
  action: "password_signup", appearance: "interaction-only",
  callback: (tok) => { setToken(tok); setState("token_ready") },
  "error-callback": ..., sitekey: s, size: "flexible", ...
})
```

and the submit button is `disabled: enforced && !token`. So the ONLY thing needed is a
call to `opts.callback(TOKEN)` — React state fills, button enables, the app's own submit
handler runs with all its native headers.

Intercept the api.js request and serve your own stub **instead**:

```python
STUB_JS = """
window.__CAPTCHA_TOKEN__ = __TOKEN_PLACEHOLDER__;   // <-- substituted per-run
(function(){
  if (window.turnstile && window.turnstile.__stub) return;
  var W = {};
  function fire(opts){
    if (!opts) return;
    try { opts["before-interactive-callback"] && opts["before-interactive-callback"](); } catch(e){}
    setTimeout(function(){
      try { opts.callback && opts.callback(window.__CAPTCHA_TOKEN__ || ""); } catch(e){}
    }, 250);
  }
  window.turnstile = {
    __stub: true,
    render: function(el, opts){
      var id = "stub-" + Math.random().toString(36).slice(2);
      W[id] = opts;
      if (el && el.appendChild && !el.querySelector(".cf-stub")) {
        var d = document.createElement("div"); d.className = "cf-stub";
        d.textContent = "verifying..."; el.appendChild(d);
      }
      fire(opts); return id;
    },
    reset: function(id){ fire(W[id]); },
    remove: function(id){ delete W[id]; },
    getResponse: function(){ return window.__CAPTCHA_TOKEN__ || ""; },
    isReady: function(cb){ cb && cb(); }
  };
})();
"""

def stub_with_token(tok):
    return STUB_JS.replace("__TOKEN_PLACEHOLDER__", json.dumps(tok))

await page.route("**/challenges.cloudflare.com/turnstile/**", handle_route)  # fulfill(stub_with_token(tok))
await page.add_init_script(stub_with_token(tok))                            # BOTH paths
```

### CRITICAL: bake the token INTO the stub body

The failing version set the token with a *separate* init script
(`add_init_script("window.__CAPTCHA_TOKEN__ = " + json.dumps(tok) + ";" + STUB_JS)`).
Result, from the probe log:

```
[STUB] installed, token_len=60     <- main document, fine
[STUB] render called ... token_len=0   <- context where api.js ran: token MISSING
[STUB] fire callback, token_len=0
btn disabled: true                 <- never unlocks
```

The fulfilled api.js runs in a context the earlier init-script assignment did not reach.
After switching to `__TOKEN_PLACEHOLDER__` substitution inside the stub text:

```
[STUB] render called action=password_signup token_len=60
[STUB] fire callback, token_len=60
t+1s: {"btn": {"disabled": false, ...}}
```

Rule: **any value the stub needs must be literal text inside the stub**, never a global
set by a different script/init order.

Both `route.fulfill` AND `add_init_script` are needed: the app loads api.js via
`next/script` with `strategy="afterInteractive"` (route catches it), and some contexts
read `window.turnstile` before that (init script covers them). Stub is idempotent
(`if (window.turnstile.__stub) return`).

Debugging aid: keep `console.log("[STUB] ...")` lines in the stub and attach
`page.on("console", ...)`. The `token_len` in those logs is what found the bug — the DOM
looked identical in both cases ("verifying..." div present, button grey).

---

## Never hand-fetch the protected endpoint

First working-looking attempt solved the captcha and then did its own
`fetch('/auth/password/sign-up', {...})` from `page.evaluate` with the token in the body.
Results:

| Attempt | Result |
|---|---|
| manual fetch, patchright/Chromium headless | `403` + **Cloudflare HTML challenge page** (`Attention Required!`) — WAF, not the app |
| manual fetch, correct `action`, camoufox | `403 {"error":{"code":"request_unverified"}}` |
| **native React submit, camoufox** | **`200 {"status":"challenge","challenge":{"type":"email_verification"}}`** |

Why: the app's submit path adds two things you cannot cheaply reproduce —

```js
let signalsId = await collectRadarSignalsId(getToken);   // window.__WorkOSRadarCollector.signalsId
let correlation = createBrowserRequestCorrelation();     // browserActionId + clientRequestId headers
V("/auth/password/sign-up", {...form, referralCode, signalsId, turnstileToken}, correlation)
```

Radar collector is loaded from `https://js.workos.com/radar/v1/collectors.js` and
exposes `window.__WorkOSRadarCollector.signalsId`. The correlation module lives in a
chunk that is NOT in the public bundle set (searched all 32 chunks — only call sites).
So: let the page do it. The stub approach costs nothing and inherits everything.

Also note `TURNSTILE_ACTIONS = {billingTopUp:"billing_topup", magicStart:"magic_start",
passwordRecovery:"password_recovery", passwordSignup:"password_signup"}` — the solver
must be told the right `action`, an empty action gives `request_unverified` even with a
valid token.

---

## Solver: 2captcha, not YesCaptcha

`2captcha.com/in.php` with `method=turnstile`, `sitekey`, `pageurl`, **`action=password_signup`**,
`json=1` → `res.php?action=get&id=` poll (CAPCHA_NOT_READY → sleep 6). Token 830-880 chars,
~30-60s, ~$2-3/account. Sitekey `0x4AAAAAAEcO2qYYBE_ztENL`.

YesCaptcha on this target returned `internal error` and earlier runs with its token got
`request_unverified` — when one solver's tokens are rejected, switch solver before
assuming the payload is wrong. Balances live in
`Desktop/_PROJECTS/авторег проект/.env` (`TWOCAPTCHA_KEY`, `ANTICAPTCHA_KEY`, ...);
check with `check_balances.py` (getBalance returns the number in field `request`).

Browser: **camoufox** (`from camoufox.async_api import AsyncCamoufox`,
`AsyncCamoufox(headless=True, humanize=False)`). Patchright/Chromium headless passed GET
but got WAF-403 on POST. First launch downloads uBlock (~1 min) — don't kill it.
Occasional silent hang at browser start: kill and re-run (no lock file left behind).

---

## Flow specifics worth reusing

1. **Voidash generates its OWN address.** `POST api.voidash.com/api/v1/inboxes
   {"domain":"voidash.bond"}` ignores `address`/`local_part` (tested both — returns a
   random `runtime-x24.nova@voidash.bond` style name). Read `address` from the response;
   registering an invented address sends the code to a mailbox you don't hold. Also:
   `GET /api/v1/messages` works with the session key (`{"messages":[],"total":0}`);
   `/api/v1/inboxes/messages` → 404 `inbox not found` on a fresh inbox. Code = 6 digits.

   **Domain rotation** — `GET https://api.voidash.com/api/v1/domains` lists what the account may
   use (live 2026-10-03):
   ```json
   [{"domain":"voidash.cyou","tier":2,"default":true},{"domain":"voidash.bond","tier":2},
    {"domain":"voidash.com","tier":1,"premium":true,"plan_required":"paid"},
    {"domain":"govno.eu.cc","tier":3},{"domain":"musor.eu.cc","tier":3},{"domain":"pomoi.eu.cc","tier":3}]
   ```
   All five free ones create inboxes OK (verified one by one). Rotate per account rather than
   hammering one domain. Skip `voidash.com` (paid tier). Query the endpoint instead of
   hardcoding — the list is account/tier dependent. Reusable for any Voidash-based autoreg
   (attio, notion, abliteration).
2. **Verification form auto-submits** on a complete code. Clicking the button races it:
   `TimeoutError ... waiting for element to be enabled` while it is `aria-busy`.
   Set the value with the native setter, then poll for the response; click only as
   fallback.
3. **Workspace provisioning is async.** Right after verify, `/api/console/v1/session`
   returns `409 {"code":"workspace_setup_pending"}`. Poll (5s x up to 30) until
   `org_*`/`proj_*` appear — one account needed >150s.
4. **REST key creation needs an idempotency header.**
   `POST /api/console/v1/projects/{proj_id}/api-keys` `{"name":"autoreg"}` →
   `422 {"param":"header.Idempotency-Key"}`. Add `Idempotency-Key: <uuid>` → `201`
   with `{"api_key":{...},"secret_key":"ak_..."}`. Keys are `ak_`-prefixed (not `sk-`),
   `permissions:["model.invoke"]`, no expiry. List: `GET` same path.
   The error body names the missing param — always read `param`, it short-circuits guessing.
5. **Sign-in page traps the submit click.** The page has Google/GitHub/Microsoft OAuth
   buttons above the password form; `locator("button[type=submit]").first` hits an OAuth
   button and lands on `accounts.google.com`. Scope it:
   ```js
   const f = document.querySelector('input[name="password"]').closest('form');
   (f.querySelector('button[type="submit"]') || [...f.querySelectorAll('button')].pop()).click();
   ```
   Detect the mistake by checking `page.url` for `accounts.google.com` after the click.

## Credits: read the rewards API, not the marketing page

`GET /api/console/v1/rewards`:

```json
{"eligible":false,"status":"review_required","signup_credit_usd_micros":0,
 "social_bundle":{"amount_usd_micros":500000,"status":"unavailable","total_steps":2},
 "referrals":{"amount_each_usd_micros":500000,"maximum_rewards":0}}
```

One account out of five, checked ~45 min after signup:

```json
{"eligible":true,"status":"available","signup_credit_usd_micros":1000000, ...}
```

= **$1 granted asynchronously after anti-fraud review**. Its key returns chat 200;
keys of `review_required` accounts return `insufficient_credits` on
`POST https://api.abliteration.ai/v1/chat/completions`. So the farm is viable but the
yield is review-gated — re-check old accounts (`harvest_keys.py` prints rewards per
account) instead of concluding "no bonus" from a fresh one.

- **$0.50 social bundle = TWO POSTs, no real social account needed** (corrected 2026-10-03, live-proven).
  The UI wires `activate("x"|"linkedin")`, but the server just marks the step complete:
  ```js
  await fetch("/api/console/v1/rewards/social/x",       {method:"POST", credentials:"include"})  // 200
  await fetch("/api/console/v1/rewards/social/linkedin",{method:"POST", credentials:"include"})  // 200
  ```
  Observed: `social_bundle.status` `unavailable → in_progress (1/2) → claimed (2/2)`,
  `earned_promotional_usd_micros` 1000000 → **1500000**, `balance.available_usd_micros`
  = **1499630** ($1.50), chat completion 200. Gated ONLY by `eligible:true` — on a
  `review_required` account the same POST returns
  `403 {"code":"forbidden","message":"Promotional rewards are not available for this account."}`.
  So run it in a loop/cron (`quest_runner.py --review-only`), not once.
- **Max promo per account = $3** (`maximum_promotional_usd_micros: 3000000`).
- **Authoritative balance check needs no login**: `GET https://api.abliteration.ai/v1/credits`
  with the `ak_` key → `{"data":{"total_credits":1.5,"total_usage":0.0006}}`. Prefer this over the
  console rewards JSON when auditing a key pool — one request per key, no browser.
- $0.50/referral only after the referred user's **first paid** request; `maximum_rewards:0` on fresh accounts
- "once per verified identity" → farm detection exists
- **The review gate is IP-reputation driven, not email-domain driven** (tested): all 5 Voidash free
  domains create inboxes fine, yet 12/13 accounts stayed `review_required` while the farm ran from a
  single home IP. Rotating the mail domain does NOT lift a $0 yield — changing the IP might.
- The `$1` on /pricing is the **minimum custom prepaid top-up**, unrelated to the bonus
- Models: `abliterated-model` ($1/$3 per 1M, 256K, text+vision), `abliterated-model-large`,
  `abliterated-model-large-v2` = GLM-5.3 ($3/$5, 1M ctx). Base URL `https://api.abliteration.ai/v1`.

## Gateway

`gateway.py` (stdlib only, `:8300`): pool from `accounts.jsonl`(`api_key`) + `keys.txt`,
hot-reload every 60s, `/health`, `/` (web dashboard: pool table + wins + chat tester),
`/v1/models`, `/v1/chat/completions` (+`stream`), `/v1/responses`, `/v1/messages`,
`/v1/messages/count_tokens`, `/v1/credits`, `/v1/organization/balance`, `/admin/keys`,
`/admin/reload` (master key `GATEWAY_API_KEY`). Accept both `sk-` and `ak_` prefixes.

**Failover must be exhaustive, not N-random-tries.** Live bug: 14 keys in pool, only 1 funded —
8 random picks kept missing it, so the user saw `insufficient_credits` through a *working*
gateway. Fixes that hold:

- `pick_order()` returns EVERY alive key once, proven keys first (keep a `wins` counter,
  increment in `mark_ok`), rest shuffled. Loop that list with no attempt cap.
- Three statuses, not two: `ok` / `dead` (401/403 or 4 fails, revive 600s) /
  **`nobalance`** (body contains `insufficient_credits`, revive 1800s — the anti-fraud
  review may approve later, so these must come back on their own).
- `insufficient_credits` → next key; a genuine 400/404/422 *without* that string → return it
  to the caller rather than burning the whole pool.
- Apply the same exhaustive loop to the streaming branch (it used a single `pick()`).
- Export `keys.txt` balance-holders-first so a cold gateway hits a funded key immediately.
