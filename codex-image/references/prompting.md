# Prompting guide

This guide is compatible with the sibling `imagegen` skill so prompts can be
ported between the two.

## Generate

A strong prompt usually contains three layers:

1. **Subject** — what is in the frame (`a red panda`, `a runway model`).
2. **Composition / style** — camera angle, lighting, art style
   (`extreme close-up, golden-hour lighting, shallow depth of field`,
   `flat illustration, bold outlines, pastel palette`).
3. **Mood / context** — atmosphere or storytelling beat
   (`peaceful, contemplative`, `urgent, neon-lit cyberpunk alley`).

Example:

```
codex-image generate \
  "A red panda eating bamboo, extreme close-up, golden-hour lighting,
   shallow depth of field, peaceful mood" \
  --out panda.png
```

## Edit

Provide one or more reference images plus a prompt describing the **change**
you want — not the entire scene.

```
codex-image edit \
  --input ref.png \
  "make it nighttime, add lantern lighting, keep the subject pose unchanged" \
  --out edited.png
```

Multiple references (e.g. subject + style sheet) can be combined:

```
codex-image edit \
  --input subject.png --input style-sheet.png \
  "redraw subject.png in the visual style of style-sheet.png" \
  --out merged.png
```

Reference images larger than 5 MB are automatically downscaled to a maximum
long-edge of 2048 px before being embedded as data URIs. Files that still
exceed 10 MB after downscaling are rejected (exit code 2).

## Output format

```
--output-format png    # default; lossless, supports alpha
--output-format webp   # smaller; supports alpha
--output-format jpeg   # smallest; no alpha
```

## Negative prompting

The Responses API hosted `image_generation` tool does not expose a negative
prompt field. Bake exclusions into positive language instead
(e.g. write `clean background` rather than `no clutter`).
