---
name: story-card-video
description: Turn a user supplied article, URL, video, screenshot set, photos, or mixed evidence into a high density vertical story card video with a persistent clickworthy headline, rotating proof visuals, a readable persistent summary, default background music, cover image, publish copy, and fixed branded outro. Use when Codex is asked to make, recreate, or template a news card, evidence carousel, screenshot story, AI news short, mute readable social video, or a video matching the title plus proof plus summary formula.
---

# Story Card Video

Create a 1080×1920, 30 FPS vertical video whose information hierarchy is:

1. Persistent four beat headline at the top
2. Rotating source evidence in the middle
3. Persistent readable summary at the bottom
4. Music instead of narration by default
5. An information-complete centered cover
6. Fixed branded outro, short title, and publish copy

Do not modify the user's source files.

## Required workflow

### 1. Ingest and inspect

Create a project and analyze every supplied local file:

```bash
python3 {baseDir}/scripts/analyze_inputs.py --project <project-dir> <input> [<input> ...]
```

For an article URL, fetch the page, preserve its title, author, date, source URL, and useful screenshots. For pasted article text, save a portable copy inside the project. For video, inspect the generated contact sheet and extracted frames. For screenshots, view every image at original detail.

If a source video contains important speech, transcribe it before writing claims. Do not treat filenames or thumbnails as proof.

### 2. Build the evidence story

Read [references/story-formula.md](references/story-formula.md). Write `<project-dir>/story.json` using [references/project-schema.md](references/project-schema.md).

Trace every factual statement to the supplied material. Keep emotional wording inside the boundary of the evidence. Never turn “started a new job” into “saved from poverty” unless the source supports it.

Write `cover_lines` as two to four centered lines that remain understandable without opening the video. Include the subject or event, the key qualification or boundary, and the concrete result. Include decisive numbers when the source provides them. Use `cover_kicker` for compact context and `cover_evidence` for no more than two short supporting facts. Do not rely on a vague short title as the complete cover message.

Prefer this evidence order:

1. Human face or strongest subject image
2. Original statement or article excerpt
3. Independent explanation or reaction
4. Product, result, or concrete proof
5. Tool, company, or conclusion image

For text only articles, create quote segments with `text` and `label`; do not invent documentary images. Use generated imagery only when the user asks or when it is clearly marked as illustrative.

### 3. Let content determine duration

Omit `main_duration` unless the user requests an exact duration. The renderer computes:

```text
max(8 seconds, summary characters ÷ 5.5 + 2 seconds, evidence count × 2.2 seconds)
```

Keep the summary between 45 and 180 Chinese characters. Supply enough evidence for a visual change every 2.2 to 4 seconds. If the calculated hold is longer, add real evidence, article quote cards, alternate verified details, or useful crops. Do not pad with empty scenes.

### 4. Validate, render, and inspect

Run:

```bash
python3 {baseDir}/scripts/validate_project.py <project-dir>
python3 {baseDir}/scripts/render_video.py <project-dir>
python3 {baseDir}/scripts/inspect_output.py <project-dir>/out/video.mp4 --report-dir <project-dir>/out/qa
```

Fix every validation error. Open the contact sheet and inspect the first frame, every transition, the last story frame, and the outro. Check title wrapping, screenshot legibility, summary size, source crop, and safe margins. Open the cover at original detail and verify that every text block is horizontally centered, the information hierarchy is clear, the claim boundary remains visible, and the cover can be understood without the publish description.

The default background track is `assets/default-bgm.m4a`, extracted from the reference video supplied by the user. Loop it to the content duration and fade only at the start and story ending. Its copyright status is unknown; warn before commercial publication if rights have not been confirmed.

Append the complete 2 second `assets/logo-outro.mp4` animation unless the user explicitly cancels or replaces the outro. Do not extend the logo hold beyond 2 seconds.

### 5. Deliver

Deliver these artifacts:

1. `<project-dir>/out/video_preview_720p.mp4`
2. `<project-dir>/out/video.mp4`
3. `<project-dir>/out/cover.png`
4. `<project-dir>/out/publish.txt`
5. The editable project and `story.json`

Keep `short_title` natural and no longer than 16 characters. The renderer also copies the final HD video to `~/Documents/videos/<short_title>.mp4` unless `delivery_dir` is explicitly set to an empty string.

## Design invariants

1. Keep the headline persistent and visually dominant.
2. Use yellow for hook and conflict lines, white for the conclusion.
3. Use a dark textured or blurred evidence background.
4. Reserve the middle for evidence, not decoration.
5. Keep the summary persistent only when it can be read within the computed duration.
6. Use short white flashes sparingly, normally after only the first two evidence cards; use direct cuts elsewhere.
7. Keep narration off by default. If the user requests narration, use the `media-montage-video` skill instead of forcing narration into this template.
8. Preserve source identity in the card, embedded screenshot, or `source_label`.
9. Never claim the video is publication ready before reviewing the rendered contact sheet and probe report.
10. Center every cover text block, including the kicker, main lines, evidence lines, source label, and date when present.
11. Make the cover relatively complete: name the subject or event, state the important qualification, and show the concrete result or key number.
12. Keep supporting cover evidence subordinate to the main message. Use at most two short evidence lines.
