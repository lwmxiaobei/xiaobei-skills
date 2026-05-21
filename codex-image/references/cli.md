# CLI reference

```
codex-image <subcommand> [args...]
```

## `generate`

```
codex-image generate "<prompt>" [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output-format` | `png` | `png` / `webp` / `jpeg` |
| `--out` | auto | Output path. If omitted, written to `$CODEX_HOME/generated_images/codex-image/<UTC>-<slug>.<ext>`. |
| `--force` | off | Overwrite an existing file at `--out`. |
| `--image-model` | unset | Advanced. When set, sent as `tools[0].model`. **Default is unset** so the request body matches codex byte-for-byte. |

Example:

```
codex-image generate "a red panda eating bamboo" --out panda.png
```

## `edit`

```
codex-image edit --input REF [--input REF ...] "<prompt>" [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | required, repeatable | Path to a reference image (PNG / JPEG / WEBP). Multiple `--input` flags allowed. |
| `--output-format` | `png` | Same as `generate`. |
| `--out` | auto | Same as `generate`. |
| `--force` | off | Same as `generate`. |
| `--image-model` | unset | Same as `generate`. |

Reference images larger than 5 MB are automatically downscaled to a maximum
long edge of 2048 px before being embedded. If downscaling cannot bring them
below 10 MB the command fails with exit code 2.

Example:

```
codex-image edit \
  --input ref1.png \
  --input ref2.jpg \
  "redraw in watercolor style, keep facial features intact" \
  --out edited.png
```

## `login`

```
codex-image login
```

Force the PKCE OAuth browser flow even if a usable `auth.json` already
exists. The resulting tokens are written to `$CODEX_HOME/auth.json` and will
be picked up by both this skill **and** the official `codex` CLI.

## `logout`

```
codex-image logout
```

Removes the `tokens` field from `$CODEX_HOME/auth.json` while keeping
`auth_mode` and `last_refresh`. `codex` will then treat the user as
logged-out without losing the file shape.

## `status`

```
codex-image status
```

Prints a JSON document describing the current credential, e.g.:

```json
{
  "email": "user@example.com",
  "plan": "chatgpt-plus",
  "account_id": "ws_...",
  "expires_at": "2026-05-21T01:23:45+00:00",
  "source": "/Users/you/.codex/auth.json"
}
```

Returns exit code 4 if no credential is present.

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 2    | User input error |
| 3    | File-system error |
| 4    | Auth / plan error (HTTP 403) |
| 5    | Network / rate-limit error (retries exhausted) |
| 6    | Partial success (stream broken mid-flight) |
| 7    | API business error (`response.failed`) |
| 130  | User interrupt (Ctrl+C) |
