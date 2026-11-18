# Project schema

Store the project plan as UTF 8 JSON in `<project-dir>/story.json`.

```json
{
  "headline": [
    "离谱！",
    "退役女优拍完片偷偷学编程",
    "靠 Claude 接网页开发活命"
  ],
  "conclusion": "AI 救了她的人生",
  "summary": [
    "日本一名退役女优引退后",
    "原有社交大号被工作室收回",
    "她选择自学编程，并借助 Claude",
    "承接网页开发相关工作完成转型"
  ],
  "source_label": "来源：当事人公开账号",
  "short_title": "AI救了她的人生",
  "cover_title": "AI救了她的人生",
  "cover_kicker": "当事人公开转型经历",
  "cover_lines": [
    "退役后失去原有账号",
    "她借助 Claude 学习编程",
    "开始承接网页开发工作"
  ],
  "cover_evidence": [
    "从内容创作转向网页开发"
  ],
  "description": "一段适合发布平台的简介。",
  "hashtags": ["#AI", "#Claude", "#职业转型"],
  "segments": [
    {
      "image": "assets/source/001.jpg",
      "fit": "cover",
      "label": "人物"
    },
    {
      "image": "assets/source/002.png",
      "fit": "contain",
      "crop": [0, 320, 1080, 1280],
      "label": "当事人原帖"
    },
    {
      "text": "从文章中提炼的一条有来源的证据",
      "label": "原文证据"
    }
  ],
  "settings": {
    "main_duration": null,
    "reading_chars_per_second": 5.5,
    "flash_first_n": 2,
    "flash_duration": 0.16,
    "include_outro": true,
    "background_music": null,
    "background_music_volume": 0.82,
    "delivery_dir": "~/Documents/videos",
    "font_path": null
  }
}
```

## Fields

`headline` is one to three yellow lines. `conclusion` is the final white line.

`summary` may be a string or an array of manually wrapped lines. Prefer an array after visual review.

`cover_title` is an optional short fallback and defaults to `short_title`. Keep it no longer than 16 characters.

`cover_lines` is the preferred cover message. Supply two to four centered lines that state the subject or event, the important qualification or contrast, and the concrete result. Add a key number when it materially improves understanding. Keep each line concise enough to remain large at 1080×1920.

`cover_kicker` is an optional centered context label above the main message. Keep it under 24 characters.

`cover_evidence` is an optional array of no more than two centered supporting facts. Keep each line under 26 characters and subordinate to `cover_lines`.

The renderer centers every cover text block. It falls back to the single `cover_title` only for older projects without `cover_lines`.

Each segment requires either `image` or `text`.

`fit` accepts `cover` or `contain`. Use `contain` for screenshots and documents. Use `cover` for portraits and photographs.

`crop` is optional and contains `[left, top, right, bottom]`. Use source pixel coordinates, or four normalized values between zero and one. Apply it when a video frame contains browser chrome, subtitles, an existing card layout, or irrelevant margins. Preserve source identity and qualifications that affect meaning.

`duration` is optional per segment. Either omit duration from every segment and let the renderer distribute the calculated duration, or set it on every segment. Mixed explicit and automatic durations are rejected.

`settings.main_duration` is optional. Omit it or use null for content based duration.

`settings.background_music` is optional. Null uses the bundled default track. A relative path is resolved from the project directory.

Set `settings.delivery_dir` to an empty string only when the user does not want the additional final copy.
