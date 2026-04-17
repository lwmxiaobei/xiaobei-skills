---
name: cloudflare-registrar
description: Search, price-check, and register domain names through the Cloudflare Registrar API. Use this whenever the user wants to look up domain availability, compare domain prices, check if a domain is registrable, or buy/register a domain — even if they don't mention "Cloudflare" by name. Also use when the user asks to "find a domain for X" or "register example.com". This skill enforces the safety workflow (search → real-time check → user confirmation → register → poll status) that domain registration requires because registrations are billable and non-refundable.
---

# Cloudflare Registrar

This skill wraps the Cloudflare Registrar API (beta) for three tasks:

1. **Search** candidate domain names from a keyword (discovery, cached, fast)
2. **Check** real-time availability and price for specific domains (registry truth, must do before buying)
3. **Register** a domain (billable, non-refundable)

## Why the workflow matters

Search results come from a cache and only show API-supported extensions — they're good for brainstorming, not for deciding. The Check endpoint hits the registry live and returns the current price. Skipping Check and going straight from Search to Register is how you end up with a failed registration or a surprise price. **Always Check immediately before you Register.**

Registrations charge the account's default payment method and cannot be refunded once they complete. Never call `/registrations` without:
- a fresh `domain-check` result for the exact domain,
- the user having seen and confirmed the domain name **and** the price from that check.

## Required environment

Both must be set in the shell before running any script:

- `ACCOUNT_ID` — Cloudflare account ID
- `CLOUDFLARE_API_TOKEN` — API token with Registrar write permission

If either is missing, tell the user and stop. Do not prompt them to paste tokens into the chat; ask them to `export` the variables in their shell.

## Scripts

All scripts live in `scripts/` alongside this file. They print the JSON response to stdout and exit non-zero on HTTP or network errors. Prefer them over hand-written curl — they handle auth headers, the base URL, and JSON escaping consistently.

| Task | Script | Notes |
| --- | --- | --- |
| Search candidates | `search.sh "<keyword>" [limit]` | `limit` defaults to 10. GET request. |
| Check availability/price | `check.sh <domain> [<domain> ...]` | Up to 20 domains per call. POST. |
| Register a domain | `register.sh <domain>` | **Billable.** Waits up to ~10s. Returns 201 (done) or 202 (in progress). |
| Poll registration status | `status.sh <domain>` | Use after a 202 or to check a past registration. |

Read each script before running it if you need to understand exact arguments.

## The workflow, step by step

### 1. Search (optional — only if user doesn't already have a domain in mind)

```bash
scripts/search.sh "acme corp" 5
```

Present the candidates as a list with name, registrable flag, and registration cost. Make it clear these prices are **indicative** and will be re-confirmed before any purchase.

### 2. Check (mandatory before any registration)

```bash
scripts/check.sh acmecorp.dev
```

If `registrable: false`, report the `reason` and stop. Common reasons:

- `domain_unavailable` — someone already owns it
- `extension_not_supported_via_api` — Cloudflare supports this TLD in the dashboard but not the API (user must use the dashboard)
- `extension_not_supported` / `extension_disallows_registration` — TLD cannot be registered through Cloudflare at all

### 3. Confirm with the user (mandatory before registration)

Before calling `register.sh`, show the user a clear summary and **wait for an explicit confirmation** such as "yes, register it" or "go ahead". For example:

```
About to register:
  Domain:  acmecorp.dev
  Price:   $10.11 USD (one year)
  Renewal: $10.11 USD/year (auto-renew OFF by default)
  Payment: Cloudflare account default payment method
This is non-refundable. Proceed?
```

If the user hesitates, asks a question, or gives a vague "ok I guess", do **not** proceed — clarify first. A typo here costs real money.

### 4. Register

```bash
scripts/register.sh acmecorp.dev
```

Interpret the response by `state`:

- `succeeded` + `completed: true` → done, report the expiry date.
- `in_progress` / `completed: false` → the API returned 202. Go to step 5.
- `failed` → read `error.code` / `error.message`, surface to user, do **not** retry silently.
- `action_required` → stop, surface the required action to the user.
- `blocked` → stop, surface to user.

### 5. Poll status (only if step 4 returned in_progress)

```bash
scripts/status.sh acmecorp.dev
```

Poll roughly every 5–10 seconds, up to a reasonable cap (say 2 minutes). Stop immediately if `state` becomes `action_required` or `failed`. **Do not poll in a silent infinite loop** — if it's taking unusually long, tell the user and let them decide whether to keep waiting.

## Defaults you should know

The API applies these defaults unless the registration request overrides them:

- `auto_renew`: **false** (we don't override — opt-in is safer)
- `privacy_mode`: `redaction` where the TLD supports it, otherwise `off`
- Registrant contact: the account's default registrant (configured in the dashboard)
- Payment: the account's default payment method

If the user wants auto-renew on, or a different registrant contact, say so explicitly — don't assume. Those overrides require extra JSON that `register.sh` doesn't pass by default; you'll need to call the API directly via curl for those cases and should re-read the Registrar API docs.

## Error handling guidance

- Any HTTP 401/403 → token problem. Ask the user to check the token's Registrar write scope.
- Any HTTP 4xx with a `messages`/`errors` array → show the message verbatim, don't paraphrase.
- Network errors → retry once, then give up and tell the user.

## What this skill does NOT cover (yet)

The Registrar API beta does not support:

- Renewals
- Transfers
- Contact updates
- Premium-domain fee acknowledgement (may be added)

For any of those, direct the user to the Cloudflare dashboard.

## Base URL reference

All endpoints are under `https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/registrar/`. Auth is `Authorization: Bearer $CLOUDFLARE_API_TOKEN`. Full API reference: https://developers.cloudflare.com/registrar/registrar-api/
