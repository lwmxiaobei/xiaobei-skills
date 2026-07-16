# Video configuration schema

The root file is `video.json`. Keep all paths relative to the project `public` directory. Durations are seconds and positions are pixels in composition coordinates.

## Root fields

```json
{
  "schemaVersion": 1,
  "id": "sample-video",
  "title": "Sample video",
  "description": "Optional production note",
  "video": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "backgroundColor": "#16110f"
  },
  "theme": {
    "fontFamily": "PingFang SC, sans-serif",
    "textColor": "#f8efd9",
    "accentColor": "#d33b2f",
    "captionColor": "#ffffff",
    "captionBackground": "rgba(20, 15, 12, 0.72)"
  },
  "audio": {
    "music": "audio/music.mp3",
    "musicVolume": 0.12
  },
  "scenes": []
}
```

`audio` is optional. Omit `music` when no licensed background track is available.

## Scene fields

```json
{
  "id": "scene-01",
  "durationSeconds": 5.5,
  "narrationText": "The narration for this scene.",
  "voiceover": "audio/scene-01.wav",
  "background": {
    "color": "#8d1f1f",
    "src": "assets/scene-01-bg.png",
    "fit": "cover",
    "startScale": 1,
    "endScale": 1.04
  },
  "elements": [],
  "captions": []
}
```

`voiceover`, `narrationText`, `background.src`, and `captions` are optional. A background must have at least `color` or `src`.

## Image element

```json
{
  "id": "main-character",
  "type": "image",
  "src": "assets/main-character.png",
  "x": 540,
  "y": 980,
  "width": 720,
  "height": 960,
  "anchorX": 0.5,
  "anchorY": 0.5,
  "zIndex": 10,
  "opacity": 1,
  "role": "primary",
  "motionPreset": "character",
  "enter": {
    "type": "rise",
    "atSeconds": 0.2,
    "durationSeconds": 0.8,
    "distance": 90
  },
  "drift": {
    "x": 6,
    "y": 10,
    "scale": 0.015,
    "periodSeconds": 3.6
  },
  "style": {
    "filter": "drop-shadow(0 18px 12px rgba(20,15,12,0.34))"
  }
}
```

Allowed image roles are `primary`, `secondary`, `tertiary`, and `static`. Allowed entrance types are `none`, `fade`, `rise`, `left`, `right`, and `pop`.

Allowed motion presets are `character`, `drift`, and `static`. Use `character` only for isolated people. It adds subtle breathing, weight shift, sway, and perspective motion after the entrance. Use `drift` for ordinary image layers. Use `static` for maps, labels, and props that must remain locked.

`anchorX` and `anchorY` range from 0 to 1. Position refers to the anchor point. Omit `height` to preserve intrinsic aspect ratio.

## Text element

```json
{
  "id": "headline",
  "type": "text",
  "text": "A clear headline",
  "x": 540,
  "y": 260,
  "width": 900,
  "zIndex": 30,
  "fontSize": 96,
  "fontWeight": 800,
  "lineHeight": 1.12,
  "align": "center",
  "color": "#f8efd9",
  "backgroundColor": "transparent",
  "padding": 0,
  "enter": {
    "type": "pop",
    "atSeconds": 0.1,
    "durationSeconds": 0.6
  }
}
```

Allowed alignment values are `left`, `center`, and `right`.

## Caption

```json
{
  "text": "One short caption page",
  "startSeconds": 0.2,
  "endSeconds": 1.8,
  "emphasis": "optional emphasized phrase"
}
```

Keep each page concise. For Chinese, prefer 8 to 18 characters. Keep captions inside the lower safe area and avoid covering important faces or products.

## Timing rules

1. Scene duration must be positive.
2. Caption time is local to its scene.
3. Caption start must be nonnegative and less than its end.
4. Caption end must not exceed scene duration.
5. Entrance start should be inside scene duration.
6. Total video duration is the sum of scene durations.
7. When a user gives an exact target duration, make the rounded scene total match it before rendering.

## Path rules

1. Never use an absolute media path in `video.json`.
2. Never use `..` in a media path.
3. Use files under `public/assets`, `public/audio`, or `public/fonts`.
4. Prefer PNG or WebP for transparent layers and JPEG or WebP for opaque backgrounds.
