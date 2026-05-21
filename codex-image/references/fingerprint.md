# codex fingerprint specification

Byte-level spec of the HTTP fingerprint this skill must reproduce. All
values are taken from the open-source `codex` Rust client. Source file
references are relative to the `codex` repository checkout in
`/Users/linweimin/codes/agent-learn/claude-code-mini/codex`.

## 1. OAuth authorize URL

`GET https://auth.openai.com/oauth/authorize`

| Query | Value |
|-------|-------|
| `response_type` | `code` |
| `client_id` | `eci-prd-pub-codex-123` (`rmcp-client/src/perform_oauth_login.rs:720`) |
| `redirect_uri` | `http://localhost:1455/auth/callback` (fallback `1457`) (`login/src/server.rs:55,57,156`) |
| `scope` | `openid profile email offline_access api.connectors.read api.connectors.invoke` (`login/src/server.rs:496-498`) |
| `code_challenge` | PKCE S256 of `code_verifier` |
| `code_challenge_method` | `S256` (`login/src/server.rs:504`) |
| `state` | 32-byte random base64url |
| `id_token_add_organizations` | `true` (`login/src/server.rs:505-512`) |
| `codex_cli_simplified_flow` | `true` (same) |
| `originator` | `codex_cli_rs` (same) |

## 2. `/v1/responses` request headers

| Header | Value | codex source |
|--------|-------|--------------|
| `Authorization` | `Bearer <access_token>` | `responses-api-proxy/src/lib.rs:196-221` |
| `originator` | `codex_cli_rs` | `login/src/auth/default_client.rs:36,234` |
| `User-Agent` | `codex_cli_rs/<version> (<os_type> <os_ver>; <arch>) <terminal>` | `login/src/auth/default_client.rs:133-157` |
| `Accept` | `text/event-stream` | `codex-api/src/endpoint/responses.rs:139` |
| `Content-Type` | `application/json` | (set by reqwest body) |
| `session-id` | UUIDv4, regenerated per CLI invocation | `codex-api/src/requests/headers.rs:8` |
| `x-codex-installation-id` | UUIDv4, persisted to disk | `core/src/client.rs:135` |

### Headers we must NOT send

These are emitted by codex only in multi-turn / internal contexts. Sending
them in a single-shot Responses call would itself become a fingerprint:

- `x-codex-turn-state`
- `x-codex-turn-metadata`
- `x-openai-subagent`
- `x-openai-memgen-request`
- `x-responsesapi-include-timing-metrics`
- `thread-id`
- `x-client-request-id`
- `x-openai-internal-codex-residency`

## 3. `User-Agent` template

```
codex_cli_rs/{version} ({os_type} {os_ver}; {arch}) {terminal}
```

- `version` — hardcoded `CODEX_PRETEND_VERSION` constant. Currently
  `0.45.0`. Review quarterly against
  https://github.com/openai/codex/releases.
- `os_type` — `platform.system()` (`Darwin` / `Linux`).
- `os_ver` — `platform.release()`.
- `arch` — `platform.machine()` (`arm64` / `x86_64`).
- `terminal` — `$TERM_PROGRAM` or `unknown`.

## 4. `auth.json` file shape

```json
{
  "auth_mode": "Chatgpt",
  "tokens": {
    "id_token": "<JWT>",
    "access_token": "<JWT>",
    "refresh_token": "<string>",
    "account_id": "<workspace_id>"
  },
  "last_refresh": "<ISO8601 UTC>"
}
```

File mode: `0o600`.

`logout` removes the `tokens` key but keeps `auth_mode` and `last_refresh`.
codex correctly interprets a tokens-less file as "logged out".

## 5. Token refresh

`POST https://auth.openai.com/oauth/token`

```json
{
  "client_id": "eci-prd-pub-codex-123",
  "grant_type": "refresh_token",
  "refresh_token": "<token>"
}
```

Errors:

- `refresh_token_expired` / `refresh_token_reused` /
  `refresh_token_invalidated` — delete tokens and fall back to interactive
  login.
- Other 4xx — same.
- 5xx — exponential back-off retry up to 3 times (2 s / 4 s / 8 s).

## 6. `/v1/responses` request body — `generate`

```json
{
  "model": "gpt-5.5",
  "input": [
    {
      "role": "user",
      "content": [
        {"type": "input_text", "text": "<prompt>"}
      ]
    }
  ],
  "tools": [
    {"type": "image_generation", "output_format": "png"}
  ],
  "stream": true
}
```

- Top-level `model` is `gpt-5.5`.
- `tools[0]` does **not** include `model`; the backend chooses the default
  (`gpt-image-2`), matching codex byte-for-byte.
- No `tool_choice`, `instructions`, `previous_response_id`, or `store`
  fields are sent.

## 7. `/v1/responses` request body — `edit`

Same as above but with extra `input_image` items in `content`:

```json
{
  "type": "input_image",
  "image_url": "data:image/png;base64,<...>"
}
```

Reference images are downscaled to a max long edge of 2048 px when source
exceeds 5 MB. The skill rejects any single reference still over 10 MB after
downscaling (exit code 2).

## 8. Verification protocol

Before declaring fingerprint parity, capture both a codex-native
`image_gen` request and this skill's request with `mitmproxy`. Diff
field-by-field:

- HTTP method, path, version — must match.
- Header set — must match (UUID-bearing headers differ in value only).
- Request body JSON keys — must match (prompt text and image data differ).

Record the diff in a follow-up section of this file when the spec is
re-verified.
