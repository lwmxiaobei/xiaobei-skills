---
name: media-montage-video
description: Create an editable Remotion project and rendered MP4 by intelligently mixing multiple user supplied videos and images with generated copy, narration, captions, on screen text, music, and optional source audio. Use when the user asks to turn one or more clips, screen recordings, product demos, photos, or mixed media into a narrated short video, vertical social video, technology explainer, product montage, news style video, or exact duration video.
---

# Media Montage Video

Build a real mixed media timeline from supplied clips and images. Generate three coordinated text layers: narration copy, timed captions, and on screen copy. Deliver an editable Remotion project, a lightweight preview, and the final MP4.

## Core rules

1. Treat user supplied media as the primary visual source. Generate replacement images only when the user requests them or a required visual idea is missing.
2. Never modify the original files. Analyze and normalize portable copies inside the project.
3. Treat requested duration as a narration budget, not permission to add silence. Estimate the copy, synthesize it, probe the real audio, and only then lock scene and final duration.
4. Preserve approved wording. If no script is supplied, write a hook, explanation, evidence or demonstration, and conclusion.
5. Use direct cuts by default. Avoid full frame fades that create black or white flashes.
6. Keep source audio muted when narration replaces it. Preserve source audio only for useful demonstrations, reactions, or original speech.
7. Never clone a voice without authorization. Default Chinese narration may use the bundled authorized F5 TTS reference. Custom voices require user supplied authorized audio and its exact transcript.
8. Verify factual claims before publishing factual content. Check licenses before commercial use.
9. Keep generated narration at least 90 percent of narrated scene time. Never stretch a short voiceover to an exact target by distributing long silent holds across scenes.
10. Size each caption background to the rendered caption text plus horizontal padding. Treat `captionMaxWidth` as a wrapping limit, never as a fixed background width.

## Load references selectively

1. Read [references/media-schema.md](references/media-schema.md) before editing `video.json`.
2. Read [references/copy-and-storyboard.md](references/copy-and-storyboard.md) when writing narration, captions, and on screen copy.
3. Read [references/quality-gates.md](references/quality-gates.md) before rendering and delivery.
4. Use the installed `remotion-best-practices` skill when changing the bundled React template. Keep all animation frame driven.

## Workflow

### 1. Create the project

Run:

```bash
python3 scripts/create_project.py <project-directory>
```

Default to 1080 by 1920, 30 fps, simplified Chinese, the `tech-explainer` layout, and 30 seconds when the user does not specify them.

### 2. Analyze supplied media

Run analysis before deciding which clips to use:

```bash
python3 scripts/analyze_media.py <media-file-or-directory> [...] \
  --output-dir <project-directory>/analysis
```

Review `media-report.json` and every contact sheet. Identify usable moments, scene changes, people, products, interfaces, repeated footage, poor frames, and source audio. Do not select clips only from filenames.

### 3. Normalize portable copies

Run:

```bash
python3 scripts/prepare_media.py <project-directory> <media-file-or-directory> [...]
```

This copies images and converts videos to H.264, AAC, 30 fps, and browser compatible pixel format under `public/assets/source`. Use `media-manifest.json` paths in `video.json`.

### 4. Write the copy and storyboard

Create a clear narrative arc before editing. Use the requested duration to estimate copy length, but do not finalize scene durations before narration exists. Maintain three separate layers:

1. `narrationText` contains natural spoken paragraphs.
2. `captions` contains short phrases synchronized to narration.
3. Text elements and `layout` contain persistent headlines, labels, figures, and conclusions visible inside the video.

For a 30 to 60 second video, use four to eight narration paragraphs, 12 to 30 caption pages, and a visual change every two to four seconds. Match each sentence to a specific clip or image. Use the strongest visual for the hook and save a clear proof or conclusion for the final scene. Estimate Chinese copy near 3.5 to 4.5 characters per second, then revise from measured F5 TTS duration rather than trusting the estimate.

### 5. Build `video.json`

Use video elements for moving footage, image elements for stills, and text elements for scene specific copy. Set `trimBeforeSeconds` and `trimAfterSeconds` from the analyzed usable interval. Use `volume: 0` for narration replacement. Use a restrained nonzero source volume only when the original sound matters.

Use `layout.preset: tech-explainer` for a fixed headline area, central media window, and pill captions. Use `full-frame` when the source footage should fill the composition.

### 6. Create narration and captions

For Chinese narration, use the shared F5 TTS 1.1.21 runtime at
`~/.codex/runtimes/f5-tts/1.1.21/.venv`. On Windows, `~` resolves to the user
profile and the interpreter is `.venv\\Scripts\\python.exe`; on macOS and Linux it
is `.venv/bin/python`. Check it before synthesis:

```bash
python3 scripts/synthesize_f5_speech.py --check-runtime
```

The check first honors an explicit `--python` or configured environment variable, then
checks only the fixed runtime. It does not scan project directories, parent directories,
active environments, or `PATH`. If the fixed runtime is missing or unhealthy, it
automatically runs `scripts/install_f5_runtime.py` and installs the pinned version there.
Do not create a separate F5 TTS environment inside each video project. Use
`--no-install-runtime` only for a read only diagnostic. Explicit overrides remain
available through `MEDIA_MONTAGE_F5_PYTHON`, `VIDEOGEN_F5_PYTHON`, or
`F5_TTS_PYTHON`.

The installer supports macOS and Windows. It uses `fcntl` locking on macOS and
`msvcrt` locking on Windows, discovers `uv` from `PATH` and common per user install
locations, and falls back to Python 3.11 or 3.10. Windows may use the `py` launcher.
FFmpeg and network access to PyPI and Hugging Face are still required.
On Windows, replace command examples that start with `python3` with `py -3.11` or
an available `python` command. The renderer resolves Windows `npm.cmd` and
`remotion.cmd` launchers automatically.

Synthesize four to eight complete scene paragraphs in one manifest session. Do not synthesize every caption as a separate audio clip because repeated sentence starts make the voice flat.

```bash
python3 scripts/synthesize_f5_speech.py --manifest <project-directory>/narration.json
```

For a custom authorized voice, pass both `--reference-audio` and `--reference-text`. If F5 TTS is unavailable, use `scripts/synthesize_speech.py` and disclose the fallback.

Synchronize captions only after audio exists. For an exact target, the script requires narration to cover at least 90 percent of the narrated timeline and rejects excessive per scene holds:

```bash
python3 scripts/sync_captions.py <project-directory> --target-duration <seconds>
```

If synchronization reports insufficient narration coverage, expand or tighten the copy, synthesize the affected paragraphs again, and rerun synchronization. Do not lower the gate, slow the video, loop unrelated footage, or pad every scene with silence merely to hit the target. If the user did not request an exact duration, omit `--target-duration` and let measured narration duration determine the final runtime.

After synchronization, compare the reported narration duration, scene duration, coverage percentage, and largest scene tail. Continue only when coverage is at least 90 percent and no narrated scene has more than 0.60 seconds after its voiceover. Use a direct cut after about 0.08 to 0.20 seconds by default. Longer holds require an intentional, reviewed visual beat.

If source speech must be preserved, use an available timestamped transcription tool and replace estimated captions with the returned timestamps. Do not place new narration over important original speech.

### 7. Validate and render

Run:

```bash
python3 scripts/validate_project.py <project-directory>
python3 scripts/render_video.py <project-directory>
```

Fix every validation error. Rendered outputs are `out/video.mp4` and `out/video_preview_720p.mp4`.

### 8. Inspect and deliver

Run:

```bash
python3 scripts/inspect_video.py <project-directory>/out/video.mp4 \
  --report-dir <project-directory>/out/qa
```

Review the opening, middle, climax, every cut, subtitle safe area, source crop, audio balance, and final frame. Deliver the lightweight preview first, then the final MP4 and editable project.

## Included resources

1. `assets/remotion-template` contains the reusable mixed media Remotion project.
2. `scripts/analyze_media.py` probes media, detects scene changes, and creates contact sheets.
3. `scripts/prepare_media.py` creates portable normalized media and a manifest.
4. `scripts/synthesize_f5_speech.py` creates default or authorized custom F5 TTS narration.
5. `scripts/install_f5_runtime.py` installs the pinned shared F5 TTS runtime when missing.
6. `scripts/sync_captions.py` aligns scene duration and caption pages with narration.
7. `scripts/validate_project.py`, `render_video.py`, and `inspect_video.py` enforce delivery quality.
