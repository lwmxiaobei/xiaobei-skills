# codex-image

Generate or edit images via OpenAI's Responses API using your **ChatGPT account
subscription quota** — no `OPENAI_API_KEY` required.

The skill reuses the `auth.json` produced by the official `codex` CLI when it
exists, and falls back to a PKCE OAuth browser flow when it doesn't.

## Status

Unofficial skill. See [`LEGAL.md`](./LEGAL.md).

## Installation

```bash
uv pip install -e .
```

Or simply add the `scripts/` directory to `PATH` and run
`python scripts/codex_image.py`.

## Quick start

```bash
# Generate
codex-image generate "a red panda eating bamboo" --out panda.png

# Edit (supply one or more reference images)
codex-image edit --input ref1.png --input ref2.png "make it nighttime" --out night.png

# Auth management
codex-image login
codex-image status
codex-image logout
```

See [`references/cli.md`](./references/cli.md) for the full CLI reference, and
[`references/prompting.md`](./references/prompting.md) for prompt-writing
guidance.

## How it works

The skill speaks to `https://api.openai.com/v1/responses` with the
`image_generation` hosted tool while presenting an HTTP fingerprint
indistinguishable from the official `codex` CLI. See
[`references/fingerprint.md`](./references/fingerprint.md) for the byte-level
spec.

## Layout

```
codex-image-skill/
├── SKILL.md                # skill metadata + invocation guide
├── scripts/                # Python entry point + library modules
├── references/             # prompting / CLI / fingerprint docs
├── tests/                  # pytest unit tests
├── pyproject.toml
├── LEGAL.md
└── README.md
```
