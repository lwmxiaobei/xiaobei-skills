# codex-image

A Claude / Codex **Skill** that lets an AI assistant generate or edit images using your **ChatGPT subscription quota** — **no `OPENAI_API_KEY` required**.

> This is a **skill**, not a CLI you operate by hand. Just describe what you want in natural language to your AI assistant; it will detect the intent, invoke this skill, and complete the task for you.

> 中文版本：[`README_CN.md`](./README_CN.md)

## What is this

`codex-image` is an extension you install into Skill-capable AI assistants (e.g. Claude Code, Codex). Once installed, whenever you tell your assistant something like "generate an image" or "edit this photo", it will:

1. Detect the intent and auto-activate this skill
2. Reuse the existing `codex` login on your machine (`~/.codex/auth.json`); if absent, automatically launch a one-time browser OAuth flow
3. Call OpenAI's Responses API via the `image_generation` hosted tool to generate / edit the image
4. Save the result locally and return the file path

The whole flow consumes your **ChatGPT subscription (Plus / Pro / Business)** quota — it does **not** bill an API key.

> ⚠️ This is an unofficial skill. Please read [`LEGAL.md`](./LEGAL.md) before use.

## Installation

### Option 1: `npx skills add` (recommended)

One-liner to install from the GitHub repo into your local skill directory:

```bash
npx skills add https://github.com/lwmxiaobei/xiaobei-skills
```

This pulls the skill collection (including this `codex-image`) into a location your AI assistant can discover. Restart / open a new session to make it available.

### Option 2: Manual install

Drop this directory into wherever your AI assistant looks for skills (for Claude Code, that's typically `~/.claude/skills/` or a project-level `.claude/skills/`). The assistant loads `SKILL.md` on startup.

### Runtime dependency

Either way, the underlying scripts need a Python environment. It is recommended to prepare one ahead of time:

```bash
uv pip install -e .
```

Or just add `scripts/` to your `PATH`. The AI assistant runs the underlying script automatically when invoking the skill — you don't need to run anything manually.

## How to use (drive it with natural language)

You don't need to memorize commands — **just talk to your AI assistant**. Here are typical triggers.

### 1. Generate a new image

> "Generate an image of a red panda eating bamboo and save it to `panda.png`"
>
> "Generate an image of a cyberpunk cat sitting on a neon-lit rooftop"
>
> "Use gpt-image to draw me a minimalist landscape painting"

Once the assistant detects a generation intent, it activates this skill and writes the image to your specified path (or the default output directory).

### 2. Edit / modify an image (with reference images)

> "Turn this photo into a nighttime scene" (with `photo.jpg` attached)
>
> "Combine `ref1.png` and `ref2.png` into a new poster"
>
> "Edit this image to make the background snowy"

As long as you provide reference image paths and describe the edit, the assistant runs the skill's edit flow.

### 3. Account management

> "Check my codex login status"
>
> "I want to log in to my ChatGPT account again"
>
> "Log out of the current account"

The assistant will dispatch the skill's `login` / `logout` / `status` sub-commands accordingly.

## When the skill triggers

`SKILL.md` declares the trigger rules; the AI assistant uses them to decide whether to invoke:

Will trigger when:

- You mention generating / editing / drawing / modifying / producing an image
- You explicitly name `codex-image` / "use my ChatGPT quota"
- You already have a `codex` login locally and the request is for image generation

Will **not** trigger when:

- You explicitly want to use `OPENAI_API_KEY` (use a generic Images API skill instead)
- You want Google / Gemini / Adobe / other vendors' image models
- You only need local background removal (use the `imagegen` skill)

## Output location

Default output path:

```
$CODEX_HOME/generated_images/codex-image/<UTC-timestamp>-<slug>.<ext>
```

You can also specify a filename in the conversation, e.g. "save it to `~/Desktop/out.png`", and the assistant will forward it as `--out`.

## How it works (in short)

Under the hood, the skill sends requests to `https://api.openai.com/v1/responses` using the `image_generation` hosted tool. Its HTTP fingerprint is byte-for-byte aligned with the official `codex` CLI, which is what allows it to reuse ChatGPT subscription auth. See [`references/fingerprint.md`](./references/fingerprint.md) for the spec.

## Further reading

- [`SKILL.md`](./SKILL.md) — skill metadata and trigger guide (the entry point the AI assistant actually reads)
- [`references/cli.md`](./references/cli.md) — full flags of the underlying script (the assistant calls it for you; no need to memorize)
- [`references/prompting.md`](./references/prompting.md) — how to write effective image prompts
- [`references/fingerprint.md`](./references/fingerprint.md) — HTTP fingerprint alignment with the official CLI
- [`LEGAL.md`](./LEGAL.md) — legal notice and disclaimer

## Directory layout

```
codex-image/
├── SKILL.md       # skill metadata + trigger guide (AI assistant entry point)
├── scripts/       # Python implementation (auto-invoked by the assistant)
├── references/    # prompting / CLI / fingerprint docs
├── agents/        # sub-agent definitions
├── tests/         # pytest unit tests
├── pyproject.toml
├── LEGAL.md
└── README.md
```
