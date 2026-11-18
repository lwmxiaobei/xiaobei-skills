#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from story_common import ffprobe_json, require_binary


def main() -> None:
    parser = argparse.ArgumentParser(description="检查故事卡片成片并生成九宫格")
    parser.add_argument("video", type=Path)
    parser.add_argument("--report-dir", required=True, type=Path)
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    report_dir = args.report_dir.expanduser().resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    probe = ffprobe_json(video)
    (report_dir / "probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")

    duration = float(probe.get("format", {}).get("duration") or 0)
    if duration <= 0:
        raise SystemExit("无法读取视频时长")
    ffmpeg = require_binary("ffmpeg")
    frames: list[tuple[Path, float]] = []
    for index in range(9):
        timestamp = duration * index / 8 if index else min(0.12, duration / 2)
        timestamp = min(timestamp, max(0.0, duration - 0.04))
        target = report_dir / f"frame-{index + 1:02d}.jpg"
        subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{timestamp:.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(target)],
            check=True,
        )
        frames.append((target, timestamp))

    thumb_w, thumb_h = 360, 640
    label_h = 44
    sheet = Image.new("RGB", (thumb_w * 3, (thumb_h + label_h) * 3), "#111111")
    draw = ImageDraw.Draw(sheet)
    face = ImageFont.load_default()
    for index, (path, timestamp) in enumerate(frames):
        image = Image.open(path).convert("RGB")
        image = ImageOps.fit(image, (thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % 3) * thumb_w
        y = (index // 3) * (thumb_h + label_h)
        sheet.paste(image, (x, y))
        draw.text((x + 10, y + thumb_h + 14), f"{timestamp:.2f}s", fill="white", font=face)
    sheet.save(report_dir / "contact-sheet.jpg", quality=92)
    print(json.dumps({"probe": str(report_dir / "probe.json"), "contact_sheet": str(report_dir / "contact-sheet.jpg"), "duration": duration}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

