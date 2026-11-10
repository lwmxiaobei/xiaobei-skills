#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import ImageFont

from story_common import StoryError, calculate_timing, load_story, nonspace_count, require_binary, resolve_font, resolve_project_path


PLACEHOLDERS = {
    "待提炼标题",
    "待提炼结论",
    "待填写",
    "待命名",
    "请根据已核对的素材填写摘要",
    "来源待核对",
    "待提炼事件主体",
    "待提炼事实边界",
    "待提炼关键结果",
}


def validate(project: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    story = load_story(project)

    headline = story.get("headline")
    if not isinstance(headline, list) or not 1 <= len(headline) <= 3:
        errors.append("headline 必须是一至三行字符串数组")
    else:
        for line in headline:
            if not str(line).strip() or str(line).strip() in PLACEHOLDERS:
                errors.append("headline 仍包含空值或占位内容")
            if nonspace_count(line) > 22:
                warnings.append(f"标题行偏长，可能需要缩小字号：{line}")

    conclusion = str(story.get("conclusion") or "").strip()
    if not conclusion or conclusion in PLACEHOLDERS:
        errors.append("conclusion 不能为空或保留占位内容")

    summary_chars = nonspace_count(story.get("summary"))
    if summary_chars < 20:
        errors.append("summary 少于 20 个字符，无法构成完整故事")
    elif summary_chars < 45:
        warnings.append("summary 少于建议的 45 个字符")
    if summary_chars > 220:
        errors.append("summary 超过 220 个字符，请提炼后再渲染")
    elif summary_chars > 180:
        warnings.append("summary 超过建议的 180 个字符")

    short_title = str(story.get("short_title") or "").strip()
    if not short_title or short_title in PLACEHOLDERS:
        errors.append("short_title 不能为空或保留占位内容")
    elif len(short_title) > 16:
        errors.append("short_title 必须不超过 16 个字符")

    cover_title = str(story.get("cover_title") or short_title).strip()
    if len(cover_title) > 16:
        errors.append("cover_title 必须不超过 16 个字符")

    cover_kicker = str(story.get("cover_kicker") or "").strip()
    if cover_kicker in PLACEHOLDERS:
        errors.append("cover_kicker 仍包含占位内容")
    elif nonspace_count(cover_kicker) > 24:
        warnings.append("cover_kicker 超过 24 个字符，可能需要缩小字号")

    cover_lines = story.get("cover_lines")
    if cover_lines is None:
        warnings.append("建议填写 cover_lines，以生成信息完整的居中封面")
        cover_line_values: list[str] = []
    elif not isinstance(cover_lines, list) or not 2 <= len(cover_lines) <= 4:
        errors.append("cover_lines 必须是二至四行字符串数组")
        cover_line_values = []
    else:
        cover_line_values = [str(line).strip() for line in cover_lines]
        for line in cover_line_values:
            if not line or line in PLACEHOLDERS:
                errors.append("cover_lines 仍包含空值或占位内容")
            if nonspace_count(line) > 22:
                warnings.append(f"封面主信息行偏长，可能需要缩小字号：{line}")

    cover_evidence = story.get("cover_evidence") or []
    if not isinstance(cover_evidence, list) or len(cover_evidence) > 2:
        errors.append("cover_evidence 必须是最多两行的字符串数组")
        cover_evidence_values: list[str] = []
    else:
        cover_evidence_values = [str(line).strip() for line in cover_evidence]
        for line in cover_evidence_values:
            if not line or line in PLACEHOLDERS:
                errors.append("cover_evidence 仍包含空值或占位内容")
            if nonspace_count(line) > 28:
                warnings.append(f"封面证据行偏长，可能需要缩小字号：{line}")

    cover_information_chars = nonspace_count(cover_line_values) + nonspace_count(cover_evidence_values)
    if cover_line_values and cover_information_chars < 20:
        warnings.append("封面信息偏少，建议补充事实边界、具体结果或关键数字")

    segments = story.get("segments") or []
    if not segments:
        errors.append("segments 至少需要一个证据画面")
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            errors.append(f"第 {index} 个 segment 不是对象")
            continue
        image_value = segment.get("image")
        text_value = str(segment.get("text") or "").strip()
        if not image_value and not text_value:
            errors.append(f"第 {index} 个 segment 必须包含 image 或 text")
        if image_value:
            image_path = resolve_project_path(project, str(image_value))
            if not image_path or not image_path.exists():
                errors.append(f"第 {index} 个 segment 图片不存在：{image_value}")
        if segment.get("fit", "contain") not in {"contain", "cover"}:
            errors.append(f"第 {index} 个 segment.fit 只能是 contain 或 cover")
        crop = segment.get("crop")
        if crop is not None:
            if not isinstance(crop, list) or len(crop) != 4 or not all(isinstance(value, (int, float)) for value in crop):
                errors.append(f"第 {index} 个 segment.crop 必须是四个数字")
            elif crop[2] <= crop[0] or crop[3] <= crop[1]:
                errors.append(f"第 {index} 个 segment.crop 边界无效")

    try:
        timing = calculate_timing(story)
        if timing["max_hold"] > 4.0:
            warnings.append(f"最长证据停留 {timing['max_hold']:.2f} 秒，建议增加真实素材或证据卡")
    except StoryError as exc:
        errors.append(str(exc))
        timing = None

    try:
        font = resolve_font(project, story)
        ImageFont.truetype(str(font), 40)
    except Exception as exc:
        errors.append(f"中文字体不可用：{exc}")

    for binary in ("ffmpeg", "ffprobe"):
        try:
            require_binary(binary)
        except StoryError as exc:
            errors.append(str(exc))

    music_value = story.get("settings", {}).get("background_music")
    if music_value:
        music_path = resolve_project_path(project, music_value)
        if not music_path or not music_path.exists():
            errors.append(f"背景音乐不存在：{music_value}")

    result = {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary_characters": summary_chars,
        "cover_information_characters": cover_information_chars,
        "timing": timing,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="校验故事卡片视频项目")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    try:
        result = validate(project)
    except StoryError as exc:
        result = {"valid": False, "errors": [str(exc)], "warnings": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
