# Media montage configuration

Keep all media paths relative to the project `public` directory. Store normalized user media under `public/assets/source`.

## Root configuration

```json
{
  "schemaVersion": 1,
  "id": "product-story",
  "title": "Product story",
  "video": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "backgroundColor": "#050a08"
  },
  "theme": {
    "fontFamily": "PingFang SC, sans-serif",
    "textColor": "#f3fff7",
    "accentColor": "#ffd92f",
    "captionColor": "#10130f",
    "captionBackground": "#ffd92f",
    "captionFontSize": 42,
    "captionBottom": 420,
    "captionMaxWidth": 820
  },
  "layout": {
    "preset": "tech-explainer",
    "brandLabel": "MEDIA LAB",
    "headline": "Persistent headline",
    "subheadline": "Persistent supporting copy",
    "contentTop": 440,
    "contentHeight": 760,
    "gridColor": "rgba(67,255,139,0.10)"
  },
  "audio": {
    "music": "audio/music.mp3",
    "musicVolume": 0.12,
    "musicDuckingVolume": 0.05
  },
  "scenes": []
}
```

Allowed layout presets are `tech-explainer` and `full-frame`. The persistent frame is visual chrome. Scene media still uses composition coordinates.

`theme.captionMaxWidth` is the maximum wrapping width. Caption backgrounds must use content sized width and horizontal padding, so short captions produce short pills while long captions wrap before this limit.

## Scene

```json
{
  "id": "scene-01",
  "durationSeconds": 4.2,
  "narrationText": "A complete spoken paragraph for this scene.",
  "voiceover": "audio/scene-01.wav",
  "background": {"color": "#050a08"},
  "elements": [],
  "captions": []
}
```

Scene durations are seconds. Caption timing is local to the scene. For narrated scenes, set duration only after probing the voiceover. Keep the scene close to voiceover duration, normally adding 0.08 to 0.20 seconds and never more than 0.60 seconds without a deliberate, reviewed reason.

## Video element

```json
{
  "id": "demo-clip",
  "type": "video",
  "src": "assets/source/media-001.mp4",
  "x": 540,
  "y": 820,
  "width": 1080,
  "height": 760,
  "anchorX": 0.5,
  "anchorY": 0.5,
  "fit": "cover",
  "objectPosition": "center",
  "trimBeforeSeconds": 3.2,
  "trimAfterSeconds": 7.4,
  "playbackRate": 1,
  "volume": 0,
  "muted": true,
  "loop": false,
  "borderRadius": 0,
  "zIndex": 10,
  "enter": {"type": "none"}
}
```

Use `trimAfterSeconds` as an absolute source timestamp. The usable source duration is `trimAfterSeconds` minus `trimBeforeSeconds`, divided by `playbackRate`. Enable `loop` only for ambient footage. Never use looping to hide a missing proof shot.

## Image element

```json
{
  "id": "product-photo",
  "type": "image",
  "src": "assets/source/media-002.jpg",
  "x": 540,
  "y": 820,
  "width": 940,
  "height": 680,
  "fit": "contain",
  "role": "static",
  "motionPreset": "static",
  "zIndex": 10
}
```

Use subtle `drift` only when a still image needs motion. Keep UI screenshots and text heavy images static.

## Text element

```json
{
  "id": "price-label",
  "type": "text",
  "text": "售价 230 美元",
  "x": 540,
  "y": 1180,
  "width": 760,
  "fontSize": 54,
  "fontWeight": 800,
  "color": "#ffd92f",
  "backgroundColor": "rgba(0,0,0,0.72)",
  "padding": 20,
  "borderRadius": 18,
  "zIndex": 30,
  "enter": {"type": "pop", "durationSeconds": 0.45}
}
```

## Caption

```json
{
  "text": "让键盘成为 Agent 入口",
  "startSeconds": 0.2,
  "endSeconds": 1.8,
  "emphasis": "Agent 入口"
}
```

For Chinese captions, prefer 6 to 18 characters. Do not repeat the full persistent headline in every caption.
