#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from story_common import (
    DEFAULT_BGM,
    DEFAULT_OUTRO,
    StoryError,
    calculate_timing,
    load_story,
    require_binary,
    resolve_font,
    resolve_project_path,
)
from validate_project import validate


WIDTH = 1080
HEIGHT = 1920
TOP_END = 500
MEDIA_END = 1210
BOTTOM_START = 1210
SAFE_X = 74
YELLOW = "#F4E84A"
WHITE = "#F7F7F5"
MUTED = "#B7BCB9"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def text_width(draw: ImageDraw.ImageDraw, value: str, face: ImageFont.FreeTypeFont) -> int:
    left, _, right, _ = draw.textbbox((0, 0), value, font=face)
    return right - left


def wrap_text(draw: ImageDraw.ImageDraw, value: str, face: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in str(value).splitlines() or [""]:
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and text_width(draw, candidate, face) > max_width:
                lines.append(current.rstrip())
                current = char.lstrip()
            else:
                current = candidate
        if current:
            lines.append(current.rstrip())
        elif not paragraph:
            lines.append("")
    return lines


def find_title_font(draw: ImageDraw.ImageDraw, path: Path, values: list[str]) -> ImageFont.FreeTypeFont:
    for size in range(72, 39, -2):
        face = font(path, size)
        if all(text_width(draw, value, face) <= WIDTH - SAFE_X * 2 for value in values):
            return face
    return font(path, 40)


def open_rgb(path: Path) -> Image.Image:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    return image.convert("RGB")


def apply_crop(image: Image.Image, crop: Any) -> Image.Image:
    if crop is None:
        return image
    values = [float(value) for value in crop]
    if all(0.0 <= value <= 1.0 for value in values):
        left = round(values[0] * image.width)
        top = round(values[1] * image.height)
        right = round(values[2] * image.width)
        bottom = round(values[3] * image.height)
    else:
        left, top, right, bottom = [round(value) for value in values]
    left = max(0, min(left, image.width - 1))
    top = max(0, min(top, image.height - 1))
    right = max(left + 1, min(right, image.width))
    bottom = max(top + 1, min(bottom, image.height))
    return image.crop((left, top, right, bottom))


def gradient_background() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#0C1110")
    pixels = image.load()
    for y in range(HEIGHT):
        factor = y / HEIGHT
        red = int(10 + 8 * math.sin(factor * math.pi))
        green = int(15 + 14 * factor)
        blue = int(14 + 8 * factor)
        for x in range(WIDTH):
            pixels[x, y] = (red, green, blue)
    return image


def make_background(source: Image.Image | None) -> Image.Image:
    if source is None:
        return gradient_background()
    background = ImageOps.fit(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    background = background.filter(ImageFilter.GaussianBlur(58))
    background = ImageEnhance.Contrast(background).enhance(0.82)
    background = ImageEnhance.Brightness(background).enhance(0.52)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (2, 8, 7, 132))
    return Image.alpha_composite(background.convert("RGBA"), overlay).convert("RGB")


def draw_title(draw: ImageDraw.ImageDraw, story: dict[str, Any], font_path: Path) -> None:
    headline = [str(item).strip() for item in story.get("headline", [])]
    conclusion = str(story.get("conclusion") or "").strip()
    values = headline + [conclusion]
    face = find_title_font(draw, font_path, values)
    line_height = int(face.size * 1.34)
    total_height = line_height * len(values)
    y = max(34, (TOP_END - total_height) // 2)
    for index, value in enumerate(values):
        color = WHITE if index == len(values) - 1 else YELLOW
        draw.text(
            (WIDTH // 2, y + line_height // 2),
            value,
            font=face,
            fill=color,
            anchor="mm",
            stroke_width=1,
            stroke_fill=(0, 0, 0),
        )
        y += line_height


def summary_lines(draw: ImageDraw.ImageDraw, story: dict[str, Any], font_path: Path) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    summary = story.get("summary") or ""
    source_lines = summary if isinstance(summary, list) else [summary]
    available_height = HEIGHT - BOTTOM_START - 105
    for size in range(48, 31, -2):
        face = font(font_path, size)
        lines: list[str] = []
        for value in source_lines:
            lines.extend(wrap_text(draw, str(value), face, WIDTH - SAFE_X * 2))
        line_height = int(size * 1.38)
        if len(lines) * line_height <= available_height:
            return face, lines, line_height
    face = font(font_path, 32)
    lines = []
    for value in source_lines:
        lines.extend(wrap_text(draw, str(value), face, WIDTH - SAFE_X * 2))
    return face, lines, int(32 * 1.34)


def draw_summary(draw: ImageDraw.ImageDraw, story: dict[str, Any], font_path: Path) -> None:
    source_label = str(story.get("source_label") or "").strip()
    label_face = font(font_path, 30)
    if source_label:
        draw.text((WIDTH // 2, BOTTOM_START + 40), source_label, font=label_face, fill=MUTED, anchor="ma")
    face, lines, line_height = summary_lines(draw, story, font_path)
    start_y = BOTTOM_START + 96
    available = HEIGHT - 72 - start_y
    total = line_height * len(lines)
    y = start_y + max(0, (available - total) // 2)
    for line in lines:
        draw.text((WIDTH // 2, y + line_height // 2), line, font=face, fill=WHITE, anchor="mm")
        y += line_height


def draw_media_image(canvas: Image.Image, source: Image.Image, fit: str) -> None:
    media_size = (WIDTH, MEDIA_END - TOP_END)
    if fit == "cover":
        media = ImageOps.fit(source, media_size, Image.Resampling.LANCZOS)
        canvas.paste(media, (0, TOP_END))
        return
    panel = Image.new("RGB", media_size, "#111514")
    media = ImageOps.contain(source, (WIDTH - 36, media_size[1] - 36), Image.Resampling.LANCZOS)
    panel.paste(media, ((media_size[0] - media.width) // 2, (media_size[1] - media.height) // 2))
    canvas.paste(panel, (0, TOP_END))


def draw_quote_card(canvas: Image.Image, segment: dict[str, Any], font_path: Path) -> None:
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = 70, TOP_END + 48, WIDTH - 70, MEDIA_END - 48
    draw.rounded_rectangle((x0, y0, x1, y1), radius=34, fill="#F6F2E9")
    label = str(segment.get("label") or "原文证据")
    label_face = font(font_path, 32)
    draw.text((x0 + 48, y0 + 45), label, font=label_face, fill="#777067", anchor="la")
    quote = str(segment.get("text") or "").strip()
    for size in range(56, 31, -2):
        quote_face = font(font_path, size)
        lines = wrap_text(draw, quote, quote_face, x1 - x0 - 96)
        line_height = int(size * 1.42)
        if len(lines) * line_height <= y1 - y0 - 160:
            break
    y = y0 + 130 + max(0, (y1 - y0 - 160 - len(lines) * line_height) // 2)
    for line in lines:
        draw.text((x0 + 48, y), line, font=quote_face, fill="#171716", anchor="la")
        y += line_height


def draw_label(draw: ImageDraw.ImageDraw, value: str, font_path: Path) -> None:
    if not value:
        return
    face = font(font_path, 29)
    width = text_width(draw, value, face) + 44
    x0, y0 = 38, TOP_END + 30
    draw.rounded_rectangle((x0, y0, x0 + width, y0 + 54), radius=27, fill=(0, 0, 0, 190))
    draw.text((x0 + 22, y0 + 27), value, font=face, fill="white", anchor="lm")


def render_card(project: Path, story: dict[str, Any], segment: dict[str, Any], font_path: Path, flash: bool = False) -> Image.Image:
    source: Image.Image | None = None
    image_value = segment.get("image")
    if image_value:
        source_path = resolve_project_path(project, str(image_value))
        if source_path:
            source = apply_crop(open_rgb(source_path), segment.get("crop"))
    canvas = make_background(source)
    overlays = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlays, "RGBA")
    overlay_draw.rectangle((0, 0, WIDTH, TOP_END), fill=(0, 0, 0, 205))
    overlay_draw.rectangle((0, BOTTOM_START, WIDTH, HEIGHT), fill=(0, 0, 0, 210))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlays).convert("RGB")

    if flash:
        ImageDraw.Draw(canvas).rectangle((0, TOP_END, WIDTH, MEDIA_END), fill="white")
    elif source is not None:
        draw_media_image(canvas, source, str(segment.get("fit") or "contain"))
    else:
        draw_quote_card(canvas, segment, font_path)

    draw = ImageDraw.Draw(canvas, "RGBA")
    if not flash:
        draw_label(draw, str(segment.get("label") or ""), font_path)
    draw_title(draw, story, font_path)
    draw_summary(draw, story, font_path)
    return canvas


def cover_face(
    draw: ImageDraw.ImageDraw,
    font_path: Path,
    value: str,
    maximum: int,
    minimum: int,
    max_width: int,
) -> ImageFont.FreeTypeFont:
    for size in range(maximum, minimum - 1, -2):
        face = font(font_path, size)
        if text_width(draw, value, face) <= max_width:
            return face
    return font(font_path, minimum)


def draw_centered_cover_text(
    draw: ImageDraw.ImageDraw,
    font_path: Path,
    value: str,
    y: int,
    maximum: int,
    minimum: int,
    fill: str,
    max_width: int = WIDTH - 150,
    stroke_width: int = 3,
) -> None:
    face = cover_face(draw, font_path, value, maximum, minimum, max_width)
    draw.text(
        (WIDTH // 2, y),
        value,
        font=face,
        fill=fill,
        anchor="mm",
        stroke_width=stroke_width,
        stroke_fill="#050505",
    )


def render_cover(project: Path, story: dict[str, Any], first_segment: dict[str, Any], font_path: Path, output: Path) -> None:
    source = None
    if first_segment.get("image"):
        path = resolve_project_path(project, str(first_segment["image"]))
        if path:
            source = apply_crop(open_rgb(path), first_segment.get("crop"))
    if source is not None:
        canvas = ImageOps.fit(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        canvas = canvas.filter(ImageFilter.GaussianBlur(12))
        canvas = ImageEnhance.Brightness(canvas).enhance(0.62)
    else:
        canvas = gradient_background()
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 132))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas, "RGBA")

    kicker = str(story.get("cover_kicker") or "").strip()
    if kicker:
        kicker_face = cover_face(draw, font_path, kicker, 38, 28, WIDTH - 220)
        kicker_width = text_width(draw, kicker, kicker_face)
        draw.rounded_rectangle(
            (WIDTH // 2 - kicker_width // 2 - 34, 350, WIDTH // 2 + kicker_width // 2 + 34, 430),
            radius=40,
            fill=(8, 11, 10, 205),
            outline=(244, 232, 74, 125),
            width=2,
        )
        draw.text((WIDTH // 2, 390), kicker, font=kicker_face, fill=WHITE, anchor="mm")

    raw_cover_lines = story.get("cover_lines")
    if isinstance(raw_cover_lines, list) and raw_cover_lines:
        cover_lines = [str(value).strip() for value in raw_cover_lines if str(value).strip()]
    else:
        fallback = str(story.get("cover_title") or story.get("short_title") or story.get("conclusion") or "").strip()
        cover_lines = [fallback]

    evidence_values = story.get("cover_evidence") or []
    cover_evidence = [str(value).strip() for value in evidence_values if str(value).strip()][:2]
    main_center = 825 if cover_evidence else 920
    gap = 130 if len(cover_lines) <= 3 else 124
    start_y = round(main_center - gap * (len(cover_lines) - 1) / 2)
    for index, value in enumerate(cover_lines):
        if len(cover_lines) == 1 or index == 0 or index == len(cover_lines) - 1:
            color = YELLOW
        else:
            color = WHITE
        draw_centered_cover_text(
            draw,
            font_path,
            value,
            start_y + index * gap,
            maximum=90 if len(cover_lines) <= 3 else 84,
            minimum=48,
            fill=color,
        )

    if cover_evidence:
        evidence_top = 1215
        evidence_height = 78 * len(cover_evidence) + 72
        evidence_bottom = evidence_top + evidence_height
        draw.rounded_rectangle(
            (120, evidence_top, WIDTH - 120, evidence_bottom),
            radius=30,
            fill=(4, 7, 6, 180),
            outline=(255, 255, 255, 60),
            width=2,
        )
        for index, value in enumerate(cover_evidence):
            draw_centered_cover_text(
                draw,
                font_path,
                value,
                evidence_top + 72 + index * 76,
                maximum=40,
                minimum=28,
                fill=WHITE,
                max_width=WIDTH - 290,
                stroke_width=1,
            )

    source_label = str(story.get("source_label") or "").strip()
    if source_label:
        source_face = cover_face(draw, font_path, source_label, 34, 26, WIDTH - 180)
        draw.text((WIDTH // 2, HEIGHT - 180), source_label, font=source_face, fill="#D6D9D7", anchor="mm")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, quality=95)


def ffmpeg_concat_stills(ffmpeg: str, list_path: Path, output: Path) -> None:
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )


def append_audio(ffmpeg: str, silent_video: Path, music: Path, duration: float, volume: float, output: Path) -> None:
    fade_out_start = max(0.0, duration - 0.55)
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-stream_loop",
            "-1",
            "-i",
            str(music),
            "-i",
            str(silent_video),
            "-map",
            "1:v:0",
            "-map",
            "0:a:0",
            "-af",
            f"volume={volume:.3f},afade=t=in:st=0:d=0.20,afade=t=out:st={fade_out_start:.3f}:d=0.55,aresample=48000",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )


def append_outro(ffmpeg: str, main_video: Path, outro: Path, output: Path) -> None:
    filter_graph = (
        "[0:v]fps=30,scale=1080:1920,setsar=1,settb=AVTB,setpts=PTS-STARTPTS[v0];"
        "[1:v]fps=30,scale=1080:1920,setsar=1,settb=AVTB,setpts=PTS-STARTPTS[v1];"
        "[0:a]aresample=48000,asetpts=PTS-STARTPTS[a0];"
        "[1:a]aresample=48000,asetpts=PTS-STARTPTS[a1];"
        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(main_video),
            "-i",
            str(outro),
            "-filter_complex",
            filter_graph,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )


def safe_output_name(value: str) -> str:
    clean = re.sub(r"[\\/:*?\"<>|]", "", value).strip()
    return clean or "故事卡片视频"


def main() -> None:
    parser = argparse.ArgumentParser(description="渲染故事卡片视频")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    project = args.project.expanduser().resolve()

    validation = validate(project)
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    if not validation["valid"]:
        raise SystemExit(1)

    ffmpeg = require_binary("ffmpeg")
    story = load_story(project)
    timing = calculate_timing(story)
    font_path = resolve_font(project, story)
    settings = story.get("settings") or {}
    segments = story["segments"]

    music = resolve_project_path(project, settings.get("background_music")) or DEFAULT_BGM
    if not music.exists():
        raise StoryError(f"默认背景音乐不存在：{music}")
    outro = DEFAULT_OUTRO
    include_outro = bool(settings.get("include_outro", True))
    if include_outro and not outro.exists():
        raise StoryError(f"固定片尾不存在：{outro}")

    out_dir = project / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    final_video = out_dir / "video.mp4"

    with tempfile.TemporaryDirectory(prefix="story-card-render-") as temporary:
        work = Path(temporary)
        timeline: list[tuple[Path, float]] = []
        for index, (segment, duration) in enumerate(zip(segments, timing["segment_durations"]), start=1):
            card_path = work / f"card-{index:03d}.png"
            render_card(project, story, segment, font_path).save(card_path)
            timeline.append((card_path, duration))
            if index <= timing["flash_count"]:
                flash_path = work / f"flash-{index:03d}.png"
                render_card(project, story, segment, font_path, flash=True).save(flash_path)
                timeline.append((flash_path, timing["flash_duration"]))

        concat_path = work / "timeline.txt"
        lines: list[str] = []
        for image_path, duration in timeline:
            escaped = str(image_path).replace("'", "'\\''")
            lines.append(f"file '{escaped}'")
            lines.append(f"duration {duration:.3f}")
        last_escaped = str(timeline[-1][0]).replace("'", "'\\''")
        lines.append(f"file '{last_escaped}'")
        concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        silent_video = work / "story-silent.mp4"
        main_video = work / "story-with-music.mp4"
        ffmpeg_concat_stills(ffmpeg, concat_path, silent_video)
        append_audio(
            ffmpeg,
            silent_video,
            music,
            timing["main_duration"],
            float(settings.get("background_music_volume", 0.82)),
            main_video,
        )
        if include_outro:
            append_outro(ffmpeg, main_video, outro, final_video)
        else:
            shutil.copy2(main_video, final_video)

    render_cover(project, story, segments[0], font_path, out_dir / "cover.png")
    hashtags = story.get("hashtags") or []
    publish = "\n\n".join(
        part
        for part in [
            str(story.get("short_title") or "").strip(),
            str(story.get("description") or "").strip(),
            " ".join(str(tag) for tag in hashtags),
        ]
        if part
    )
    (out_dir / "publish.txt").write_text(publish + "\n", encoding="utf-8")

    preview = out_dir / "video_preview_720p.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(final_video),
            "-vf",
            "scale=720:1280",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "26",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-movflags",
            "+faststart",
            str(preview),
        ],
        check=True,
    )

    delivery_value = settings.get("delivery_dir", "~/Documents/videos")
    delivered = None
    if delivery_value:
        delivery_dir = Path(str(delivery_value)).expanduser().resolve()
        delivery_dir.mkdir(parents=True, exist_ok=True)
        delivered = delivery_dir / f"{safe_output_name(str(story['short_title']))}.mp4"
        shutil.copy2(final_video, delivered)

    result = {
        "video": str(final_video),
        "preview": str(preview),
        "cover": str(out_dir / "cover.png"),
        "publish_copy": str(out_dir / "publish.txt"),
        "delivered_copy": str(delivered) if delivered else None,
        "main_duration": timing["main_duration"],
        "outro_included": include_outro,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
