#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BGM = SKILL_DIR / "assets" / "default-bgm.m4a"
DEFAULT_OUTRO = SKILL_DIR / "assets" / "logo-outro.mp4"
DEFAULT_FONT_CANDIDATES = [
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
]


class StoryError(RuntimeError):
    pass


def run(command: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def require_binary(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise StoryError(f"缺少必需命令：{name}")
    return found


def load_story(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "story.json"
    if not path.exists():
        raise StoryError(f"未找到项目配置：{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StoryError(f"story.json 不是有效 JSON：{exc}") from exc


def nonspace_count(value: Any) -> int:
    if isinstance(value, list):
        text = "".join(str(item) for item in value)
    else:
        text = str(value or "")
    return sum(1 for char in text if not char.isspace())


def resolve_project_path(project_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = project_dir / candidate
    return candidate.resolve()


def resolve_font(project_dir: Path, story: dict[str, Any]) -> Path:
    configured = resolve_project_path(project_dir, story.get("settings", {}).get("font_path"))
    if configured:
        if not configured.exists():
            raise StoryError(f"指定字体不存在：{configured}")
        return configured
    for candidate in DEFAULT_FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise StoryError("未找到可用的中文字体，请在 settings.font_path 中指定字体")


def calculate_timing(story: dict[str, Any]) -> dict[str, Any]:
    segments = story.get("segments") or []
    settings = story.get("settings") or {}
    if not segments:
        raise StoryError("segments 至少需要一个证据画面")

    explicit = [segment.get("duration") for segment in segments]
    if any(value is not None for value in explicit) and not all(value is not None for value in explicit):
        raise StoryError("segment.duration 必须全部填写或全部省略")

    flash_first_n = max(0, int(settings.get("flash_first_n", 2)))
    flash_count = min(flash_first_n, max(0, len(segments) - 1))
    flash_duration = max(0.0, float(settings.get("flash_duration", 0.16)))
    flash_total = flash_count * flash_duration

    requested = settings.get("main_duration")
    if all(value is not None for value in explicit):
        segment_durations = [float(value) for value in explicit]
        if any(value <= 0 for value in segment_durations):
            raise StoryError("segment.duration 必须大于零")
        computed = sum(segment_durations) + flash_total
        if requested is not None and abs(float(requested) - computed) > 0.12:
            raise StoryError(
                f"main_duration 为 {float(requested):.2f} 秒，但分镜与闪屏合计 {computed:.2f} 秒"
            )
        main_duration = computed
    else:
        reading_speed = float(settings.get("reading_chars_per_second", 5.5))
        if reading_speed <= 0:
            raise StoryError("reading_chars_per_second 必须大于零")
        summary_chars = nonspace_count(story.get("summary"))
        content_duration = max(
            8.0,
            summary_chars / reading_speed + 2.0,
            len(segments) * 2.2,
        )
        main_duration = float(requested) if requested is not None else content_duration
        if main_duration <= flash_total + len(segments) * 0.8:
            raise StoryError("main_duration 太短，无法容纳证据画面和转场")
        each = (main_duration - flash_total) / len(segments)
        segment_durations = [each for _ in segments]

    return {
        "main_duration": round(main_duration, 3),
        "segment_durations": [round(value, 3) for value in segment_durations],
        "flash_count": flash_count,
        "flash_duration": flash_duration,
        "max_hold": max(segment_durations),
    }


def ffprobe_json(path: Path) -> dict[str, Any]:
    ffprobe = require_binary("ffprobe")
    result = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(result.stdout)

