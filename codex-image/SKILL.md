---
name: "codex-image"
description: "Use this skill when the user wants to generate images, edit images, or create images with gpt-image / GPT Image / OpenAI image models. Triggers on requests like 'generate an image', 'create a picture', 'edit this image', 'modify the photo', 'use gpt-image', or any image generation/editing task that should run via OpenAI's hosted image_generation tool."
---

# codex-image

Generate or edit images via OpenAI's Responses API by **reusing the user's
ChatGPT subscription** — no `OPENAI_API_KEY` needed. The skill speaks to
`/v1/responses` with the `image_generation` hosted tool while presenting an
HTTP fingerprint indistinguishable from the official `codex` CLI.

## When to invoke

Invoke this skill when the user asks to generate or edit an image **and**:

- They explicitly mention `codex-image` / "codex image" / "use my ChatGPT
  quota", **or**
- They have an active `codex` login (`~/.codex/auth.json` exists) and have
  not asked for an API-key based generator, **or**
- They explicitly want to avoid paying for `OPENAI_API_KEY` usage.

Do **not** use this skill when:

- The user has an `OPENAI_API_KEY` set and wants to use it directly (use a
  generic Images API skill instead).
- The user wants Google / Gemini / Adobe / other vendor image models.
- The user wants pure local background removal (`imagegen` skill covers that).

## Commands

```
codex-image generate "<prompt>" [--output-format png|webp|jpeg] [--out PATH] [--force]
codex-image edit --input REF1.png [--input REF2.png ...] "<prompt>" [--out PATH] [--force]
codex-image login
codex-image logout
codex-image status
```

Run `codex-image --help` for full flags. See
[`references/cli.md`](./references/cli.md) for details and examples.

## Prompting

See [`references/prompting.md`](./references/prompting.md). The guidance is
compatible with the sibling `imagegen` skill so prompts can be reused.

## Auth

The skill resolves an access token like so:

1. Read `$CODEX_HOME/auth.json` (default `~/.codex/auth.json`).
2. If the access token is close to expiry, refresh it.
3. If the file is missing or refresh fails, launch a PKCE OAuth browser flow
   (binds `127.0.0.1:1455`, falling back to `:1457`). On success, write
   `auth.json` so subsequent calls — including `codex` itself — reuse it.

Use `codex-image login` to force the OAuth flow.
Use `codex-image logout` to clear tokens (keeps the file shape; `codex` will
treat it as logged-out).
Use `codex-image status` to inspect the current credential.

## Output

By default images are written to:

```
$CODEX_HOME/generated_images/codex-image/<UTC>-<slug>.<ext>
```

with file mode `0o644`. Pass `--out PATH` for an explicit destination.

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 2    | User input error |
| 3    | File-system error |
| 4    | Auth/plan error (HTTP 403) |
| 5    | Network / rate-limit error (retries exhausted) |
| 6    | Partial success (stream broken) |
| 7    | API business error (`response.failed`) |
| 130  | User interrupt (Ctrl+C) |

## Legal

Unofficial skill. Read [`LEGAL.md`](./LEGAL.md) before use.
