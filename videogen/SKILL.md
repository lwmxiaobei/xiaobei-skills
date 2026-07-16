---
name: videogen
description: Generate a complete editable Remotion video project and rendered MP4 from a topic, article, script, webpage, document, or supplied media. Use when the user asks to make, generate, adapt, render, or storyboard a short video, explainer, history video, product video, paper collage animation, realistic layered character video, narrated vertical video, horizontal video, or an exact duration video. Default Chinese narration uses the bundled authorized female reference with F5 TTS.
---

# Videogen

Turn a topic or source into a validated, editable Remotion project, then render and inspect the final MP4. Prefer autonomous execution when the user asks for a finished video. Use review checkpoints only when the user asks to approve the script, storyboard, or assets first.

## Core constraints

1. Treat this as a two dimensional layered video generator. Do not promise lip sync, complex character acting, three dimensional scenes, or cinematic generated footage unless another suitable video model is explicitly available and requested.
2. Infer missing creative defaults instead of asking routine questions. Default to 30 seconds, 1080 by 1920, 30 fps, simplified Chinese, concise narration, and the `paper-collage` style. Treat any duration named by the user as a hard target.
3. Verify factual claims before rendering factual content. Keep a source list in the project notes when browsing was needed.
4. Never clone a real person's voice without clear authorization. The bundled default reference is authorized for distribution with this skill and for use as its default narration reference. Also support a custom reference only when the user supplies it or confirms authorization.
5. Check licenses for fonts, music, generated assets, reference images, and voice models before commercial use.
6. Preserve user supplied wording when the user provides an approved script. Only split it into scenes and captions unless editing was requested.

## Load references selectively

1. Read [references/video-schema.md](references/video-schema.md) before creating or editing `video.json`.
2. Read [references/style-presets.md](references/style-presets.md) when selecting visual direction or writing image prompts.
3. Read [references/quality-gates.md](references/quality-gates.md) before rendering and final delivery.
4. For Remotion implementation details, use the installed `remotion-best-practices` skill when available. All animation must be frame driven. Do not use CSS animations or transitions.

## Workflow

### 1. Convert the request into a brief

Identify topic, source content, audience, platform, duration, aspect ratio, language, style, voice, and call to action. If the user only gives a topic, write a focused narrative with one idea per scene. If the user supplies content, preserve its intent and prioritize its strongest points.

Lock the target duration before writing narration or generating audio. Allocate scene durations first, reserve roughly 10 to 15 percent for visual breathing room, then fit narration to the remaining time. For Chinese F5 TTS at speed `1.0`, begin with roughly 3.5 to 4.5 Chinese characters per spoken second and verify against generated audio. Do not solve an overlong script by time stretching or speeding up the finished narration.

Choose defaults from the request context. Common platform defaults:

1. Short vertical social video uses 1080 by 1920.
2. General horizontal video uses 1920 by 1080.
3. Square feed video uses 1080 by 1080.

### 2. Create the project

Run:

```bash
python3 scripts/create_project.py <output-directory>
```

This copies `assets/remotion-template` into the target directory. Never edit the bundled template for a single user project.

### 3. Write the script and storyboard

Create three to eight scenes for a typical short video. A 60 second narrative usually needs six to ten scenes. Each scene must have:

1. A single narrative purpose.
2. Narration text that can be spoken within the scene duration.
3. A background or background color.
4. Zero or more image and text elements.
5. Captions synchronized to the narration.

Write the result to `video.json` using the schema reference. Keep important composition decisions in data rather than hard coding them in React.

### 4. Generate and prepare assets

Create a manifest before generating images. For each asset record its scene, purpose, prompt, dimensions, and expected transparency.

Use an available image generation tool or image generation skill for new artwork. Generate backgrounds without main characters. Generate foreground characters and props as isolated transparent PNG files when supported. Use chroma key removal only as a fallback. For realistic historical illustration, build the image from a clean full frame background plate plus separate foreground characters instead of baking the main character into every background.

Place all local media under `public/`. Use simple lowercase file names with no spaces. Keep reusable items under `public/assets/`, narration under `public/audio/`, and fonts under `public/fonts/`.

Check every generated character for complete head, hands, feet, intended direction, transparent edges, and consistency with the style preset. Regenerate failures before rendering.

Set `motionPreset` to `character` for a person layer. Combine entrance motion with subtle breathing, weight shift, sway, and perspective movement. Keep motion restrained enough to avoid a puppet effect. Use `drift` for props and `static` for elements that must not float.

### 5. Create narration and captions

If the user supplies narration audio, copy it into `public/audio/` and use its real duration.

For Chinese narration, use the bundled authorized female reference and F5 TTS by default when the user does not choose another voice. The bundled reference may be distributed with this skill. Keep the default speed at `1.0`; do not stretch or accelerate the generated speech afterward. Use the portable runtime check before synthesis:

```bash
python3 scripts/synthesize_f5_speech.py --check-runtime
```

The script searches an explicit `--python` value, `VIDEOGEN_F5_PYTHON`, `F5_TTS_PYTHON`, the active virtual environment, the active Conda environment, nearby `.venv`, `venv`, and `env` directories, then Python interpreters on `PATH`. It reexecutes itself with the first interpreter that can import `f5_tts`. Do not put user names, home directories, dated workspace paths, or model cache paths in this skill.

Run synthesis through any Python 3 interpreter. Runtime discovery selects the F5 environment:

```bash
python3 scripts/synthesize_f5_speech.py \
  --text "旁白文字" \
  --output <project>/public/audio/scene-01.wav
```

For several scenes, create a UTF-8 JSON manifest and synthesize them in one model session:

```json
[
  {"text": "第一段旁白", "output": "public/audio/scene-01.wav"},
  {"text": "第二段旁白", "output": "public/audio/scene-02.wav"}
]
```

```bash
python3 scripts/synthesize_f5_speech.py --manifest <project>/narration.json
```

If automatic discovery cannot find F5 TTS, pass a portable configuration supplied by the machine owner:

```bash
python3 scripts/synthesize_f5_speech.py \
  --python /path/to/f5-environment/bin/python \
  --manifest <project>/narration.json
```

Alternatively set `VIDEOGEN_F5_PYTHON` in the shell or automation environment. Resolve relative manifest outputs from the manifest directory. Let F5 TTS or Hugging Face manage model downloads and caches in the host environment. Use `--reference-audio` and `--reference-text` only when the user explicitly chooses another authorized voice. If F5 TTS cannot run after the portable checks, fall back to an available system voice and disclose the fallback.

For a custom authorized voice, require both the reference audio and its exact transcript:

```bash
python3 scripts/synthesize_f5_speech.py \
  --reference-audio /path/to/authorized-reference.wav \
  --reference-text "参考音频的准确文字" \
  --manifest <project>/narration.json
```

Keep custom reference files inside the user project unless the user explicitly authorizes bundling them into a shared skill.

Synthesize one complete scene paragraph per clip rather than one sentence per clip. Write natural clause lengths, use punctuation to indicate emphasis and pauses, vary scene level seeds, and avoid beginning every sentence with the same cadence. Use exclamation marks only at genuine peaks. Listen to at least the opening, a middle scene, and the climax before rendering.

Fallback command:

```bash
python3 scripts/synthesize_speech.py --text "旁白文字" --output <project>/public/audio/scene-01.wav
```

Add `narrationText` and `voiceover` to each scene, then synchronize durations and estimated caption timing:

```bash
python3 scripts/sync_captions.py <project>
```

When the user requires an exact total duration, pass it explicitly:

```bash
python3 scripts/sync_captions.py <project> --target-duration 60
```

If narration audio exceeds the target, shorten the script and synthesize again. If it is shorter, let the synchronization script distribute the remaining time as visual holds.

Estimated timing is acceptable for sentence captions. For word highlighting or strict synchronization, use a transcription tool that returns timestamps and replace the estimated captions.

### 6. Validate before rendering

Run:

```bash
python3 scripts/validate_project.py <project>
```

Fix every error. Warnings may be accepted only after visual review.

### 7. Render

Run:

```bash
python3 scripts/render_video.py <project>
```

The script installs dependencies when needed and renders `out/video.mp4` plus a smaller `out/video_preview_720p.mp4`. Use direct scene cuts by default. Never fade a whole scene to transparency or black between adjacent scenes because this creates a visible flash. Use Remotion Studio for iterative layout work:

```bash
cd <project>
npm run start
```

### 8. Inspect and deliver

Run:

```bash
python3 scripts/inspect_video.py <project>/out/video.mp4 --report-dir <project>/out/qa
```

Review the extracted frames, technical report, subtitle safe area, visual hierarchy, factual text, audio balance, and final frame. Do not claim completion when rendering or inspection failed.

Deliver:

1. Lightweight preview MP4 path first so the Codex app can open it without timing out.
2. Final MP4 path.
3. Editable project path.
4. Duration, dimensions, and file size.
5. Any licensing or factual caveats.
6. A short summary of creative choices.

## Included resources

1. `assets/remotion-template` is the reusable React and Remotion project.
2. `scripts/create_project.py` creates an isolated project.
3. `scripts/synthesize_speech.py` creates macOS system voice narration.
4. `scripts/synthesize_f5_speech.py` creates default F5 TTS narration from the bundled authorized female reference.
5. `assets/voice/user-narrator-reference.wav` is the authorized distributable default reference audio.
6. `scripts/sync_captions.py` derives scene durations and captions from narration audio.
7. `scripts/validate_project.py` validates schema and local assets.
8. `scripts/render_video.py` installs dependencies and renders the MP4.
9. `scripts/inspect_video.py` runs FFprobe, black frame detection, and frame extraction.
10. The Remotion template supports direct cuts and the `character`, `drift`, and `static` motion presets.
