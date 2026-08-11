#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, ImageOps

from story_common import SKILL_DIR, ffprobe_json, require_binary


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
TEXT_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".json"}


def safe_name(index: int, path: Path, suffix: str | None = None) -> str:
    extension = suffix or path.suffix.lower() or ".bin"
    return f"{index:03d}-{path.stem[:40]}{extension}"


def collect_inputs(values: list[str]) -> list[str]:
    collected: list[str] = []
    for value in values:
        path = Path(value).expanduser()
        if path.is_dir():
            collected.extend(str(item) for item in sorted(path.rglob("*")) if item.is_file())
        else:
            collected.append(value)
    return collected


def extract_video_frames(source: Path, source_dir: Path, start_index: int) -> tuple[list[dict], int]:
    ffmpeg = require_binary("ffmpeg")
    probe = ffprobe_json(source)
    duration = float(probe.get("format", {}).get("duration") or 0)
    frame_count = min(12, max(5, math.ceil(duration / 1.5))) if duration else 6
    step = duration / (frame_count + 1) if duration else 1.0
    records: list[dict] = []
    for offset in range(frame_count):
        timestamp = max(0.0, step * (offset + 1))
        target = source_dir / safe_name(start_index, source, ".jpg")
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(source),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(target),
            ],
            check=True,
        )
        records.append(
            {
                "type": "video_frame",
                "path": str(target),
                "source": str(source.resolve()),
                "timestamp": round(timestamp, 3),
            }
        )
        start_index += 1
    return records, start_index


def make_contact_sheet(image_paths: list[Path], output: Path) -> None:
    if not image_paths:
        return
    thumb_w, thumb_h = 320, 480
    columns = 3
    rows = math.ceil(len(image_paths) / columns)
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + 38)), "#111111")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 16)
    except OSError:
        font = ImageFont.load_default()
    for index, path in enumerate(image_paths):
        try:
            image = Image.open(path).convert("RGB")
            image = ImageOps.contain(image, (thumb_w, thumb_h), Image.Resampling.LANCZOS)
        except Exception:
            continue
        x = (index % columns) * thumb_w
        y = (index // columns) * (thumb_h + 38)
        sheet.paste(image, (x + (thumb_w - image.width) // 2, y + (thumb_h - image.height) // 2))
        draw.text((x + 8, y + thumb_h + 9), path.name[:42], fill="white", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)


def main() -> None:
    parser = argparse.ArgumentParser(description="分析故事卡片视频的输入素材")
    parser.add_argument("inputs", nargs="+", help="文章、视频、截图、图片、目录或 URL")
    parser.add_argument("--project", required=True, type=Path, help="项目目录")
    args = parser.parse_args()

    project = args.project.expanduser().resolve()
    source_dir = project / "assets" / "source"
    analysis_dir = project / "analysis"
    source_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    image_paths: list[Path] = []
    next_index = 1

    for value in collect_inputs(args.inputs):
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"}:
            records.append({"type": "url", "url": value, "note": "需由 Agent 获取正文、来源信息与页面截图"})
            continue

        source = Path(value).expanduser().resolve()
        if not source.exists():
            records.append({"type": "missing", "path": str(source)})
            continue

        suffix = source.suffix.lower()
        if suffix in VIDEO_EXTENSIONS:
            frames, next_index = extract_video_frames(source, source_dir, next_index)
            records.append({"type": "video", "path": str(source), "probe": ffprobe_json(source), "frames": frames})
            image_paths.extend(Path(frame["path"]) for frame in frames)
        elif suffix in IMAGE_EXTENSIONS:
            target = source_dir / safe_name(next_index, source)
            shutil.copy2(source, target)
            with Image.open(target) as image:
                size = list(image.size)
            records.append({"type": "image", "path": str(target), "source": str(source), "size": size})
            image_paths.append(target)
            next_index += 1
        elif suffix in TEXT_EXTENSIONS:
            target = source_dir / safe_name(next_index, source)
            shutil.copy2(source, target)
            text = target.read_text(encoding="utf-8", errors="replace")
            records.append({"type": "article_text", "path": str(target), "source": str(source), "characters": len(text)})
            next_index += 1
        else:
            target = source_dir / safe_name(next_index, source)
            shutil.copy2(source, target)
            records.append({"type": "other", "path": str(target), "source": str(source)})
            next_index += 1

    report_path = analysis_dir / "input-report.json"
    report_path.write_text(json.dumps({"inputs": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    make_contact_sheet(image_paths, analysis_dir / "contact-sheet.jpg")

    story_path = project / "story.json"
    if not story_path.exists():
        template = json.loads((SKILL_DIR / "assets" / "example-story.json").read_text(encoding="utf-8"))
        template["headline"] = ["待提炼标题"]
        template["conclusion"] = "待提炼结论"
        template["summary"] = ["请根据已核对的素材填写摘要"]
        template["source_label"] = "来源：待填写"
        template["short_title"] = "待命名"
        template["cover_title"] = "待命名"
        template["cover_kicker"] = "来源待核对"
        template["cover_lines"] = ["待提炼事件主体", "待提炼事实边界", "待提炼关键结果"]
        template["cover_evidence"] = []
        template["description"] = "待填写发布简介"
        template["segments"] = [
            {"image": str(path.relative_to(project)), "fit": "contain", "label": "待确认素材"}
            for path in image_paths
        ]
        story_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"project": str(project), "report": str(report_path), "contact_sheet": str(analysis_dir / "contact-sheet.jpg"), "story": str(story_path), "visuals": len(image_paths)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
