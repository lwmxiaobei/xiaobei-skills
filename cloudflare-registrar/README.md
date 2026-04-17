# cloudflare-registrar

A Claude Code skill that wraps the Cloudflare Registrar API (beta) for domain search, availability/price checks, and registration.

## What it does

Gives Claude a safe, consistent workflow for three tasks:

- **Search** candidate domain names from a keyword (cached, fast, for discovery).
- **Check** real-time availability and price for specific domains (registry-truth, required before buying).
- **Register** a domain (billable, non-refundable).

Registration is enforced through a guardrail: Claude always runs a live price check and asks the user to confirm the domain and price in plain language before calling `/registrations`.

## Requirements

- A Cloudflare account.
- An API token with **Registrar write** permission.
- A billing profile with a default payment method on the account.
- A default registrant contact configured, and the Domain Registration Agreement accepted, in the Cloudflare dashboard.
- `curl` in the shell.

## Install

Drop the skill folder into your user-level Claude skills directory:

```
~/.claude/skills/cloudflare-registrar/
```

Claude Code picks it up after a restart (or `/reload-plugins`).

Set two environment variables so the scripts can authenticate. Put them in `~/.zshenv` so every shell context sees them (including Claude Code, cron, IDE terminals):

```bash
export ACCOUNT_ID="<your cloudflare account id>"
export CLOUDFLARE_API_TOKEN="<your registrar-scoped api token>"
```

> Do not paste the token into a chat with Claude. If the skill's scripts report "env var is required", export the variables in your shell — don't send them in messages.

## Use it through Claude

Just ask in natural language. The skill's description is written to trigger on domain-related intent even without the word "Cloudflare":

- "Find me five available `.dev` domains for a new AI expense tracker."
- "Is `acme-robotics.ai` registrable right now, and how much?"
- "Register `mybrand.dev` on my Cloudflare account."

Claude will:

1. Run `search.sh` (if needed) to produce candidates.
2. Run `check.sh` for the live price before anything billable.
3. Show you a confirmation summary (domain + price + non-refundable) and wait for explicit approval.
4. Run `register.sh` only after you say yes.
5. Poll `status.sh` if the registration goes async.

## Use the scripts directly

All scripts live in `scripts/`. They print the API response JSON to stdout and exit non-zero on HTTP errors.

| Command | Purpose |
| --- | --- |
| `scripts/search.sh "<keyword>" [limit]` | Candidate domains (cached, discovery). |
| `scripts/check.sh <domain> [<domain> ...]` | Real-time availability + price. Up to 20 per call. |
| `scripts/register.sh <domain> [--async]` | **Billable.** Registers with account defaults. |
| `scripts/status.sh <domain>` | Workflow status for an in-progress or completed registration. |

Example:

```bash
scripts/check.sh acme.dev acme.ai acme.com
```

## Registration defaults

The `register.sh` script uses account defaults intentionally:

- `auto_renew`: **false** (opt-in is safer)
- `privacy_mode`: registry default (usually `redaction` where the TLD supports it)
- Registrant contact: the account's default contact
- Payment: the account's default payment method

To override any of these, call the Registrar API directly with `curl` — the script doesn't support inline overrides.

## Error cases to expect

From `check.sh`, a domain can be non-registrable for a few reasons:

- `domain_unavailable` — someone already owns it.
- `extension_not_supported_via_api` — Cloudflare supports this TLD in the dashboard but not the API. Use the dashboard.
- `extension_not_supported` / `extension_disallows_registration` — Cloudflare doesn't sell this TLD at all.

From `register.sh`, the workflow can return:

- `succeeded` — done.
- `in_progress` — poll with `status.sh`.
- `failed` — inspect `error.code` / `error.message`; don't silently retry.
- `action_required` / `blocked` — stop and surface to the user.

## Not supported (yet)

The Registrar API beta does not currently cover:

- Renewals
- Transfers
- Contact updates
- Premium-domain fee acknowledgement

For any of those, use the Cloudflare dashboard.

## Files

```
cloudflare-registrar/
├── README.md           (this file)
├── SKILL.md            instructions Claude reads when the skill triggers
├── scripts/
│   ├── _lib.sh         shared auth + base URL
│   ├── search.sh       GET  /registrar/domain-search
│   ├── check.sh        POST /registrar/domain-check
│   ├── register.sh     POST /registrar/registrations        (billable)
│   └── status.sh       GET  /registrar/registrations/<d>/registration-status
└── evals/
    └── evals.json      test prompts for evaluating skill behavior
```

## Reference

- Cloudflare Registrar API docs: https://developers.cloudflare.com/registrar/registrar-api/
- Create an API token: `https://dash.cloudflare.com/<ACCOUNT_ID>/api-tokens`
- Billing profile: `https://dash.cloudflare.com/<ACCOUNT_ID>/billing/payment-info`
