#!/usr/bin/env python3
"""Inspect supplied videos and images, detect cuts, and create contact sheets."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from common import require_command


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def collect_sources(values: list[Path]) -> list[Path]:
    files: list[Path] = []
    for value in values:
        path = value.expanduser().resolve()
        if path.is_dir():
            files.extend(
                item
                for item in sorted(path.rglob("*"))
                if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS | IMAGE_EXTENSIONS
            )
        elif path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS | IMAGE_EXTENSIONS:
            files.append(path)
        else:
            raise SystemExit(f"Unsupported or missing source: {path}")
    return list(dict.fromkeys(files))


def probe(path: Path, ffprobe: str) -> dict[str, object]:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    duration = video.get("duration") or payload.get("format", {}).get("duration")
    return {
        "durationSeconds": round(float(duration), 3) if duration is not None else None,
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": video.get("avg_frame_rate"),
        "videoCodec": video.get("codec_name"),
        "audioCodec": audio.get("codec_name") if audio else None,
        "hasAudio": audio is not None,
    }


def detect_cuts(path: Path, ffmpeg: str, threshold: float) -> list[float]:
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "info",
            "-i",
            str(path),
            "-vf",
            f"select='gt(scene,{threshold})',showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    return [round(float(value), 3) for value in re.findall(r"pts_time:([0-9.]+)", result.stderr)]


def create_contact_sheet(path: Path, output: Path, ffmpeg: str, interval: float) -> None:
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-vf",
            f"fps=1/{interval},scale=240:-2,tile=4x4:padding=4:margin=4",
            "-frames:v",
            "1",
            str(output),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path, help="Media files or directories")
    parser.add_argument("--output-dir", type=Path, default=Path("media-analysis"))
    parser.add_argument("--sample-interval", type=float, default=2.5)
    parser.add_argument("--scene-threshold", type=float, default=0.18)
    args = parser.parse_args()
    if args.sample_interval <= 0:
        parser.error("--sample-interval must be positive")
    if not 0 < args.scene_threshold < 1:
        parser.error("--scene-threshold must be between 0 and 1")

    ffmpeg = require_command("ffmpeg")
    ffprobe = require_command("ffprobe")
    output_dir = args.output_dir.expanduser().resolve()
    sheets_dir = output_dir / "contact-sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    report: list[dict[str, object]] = []

    for index, source in enumerate(collect_sources(args.sources), start=1):
        metadata = probe(source, ffprobe)
        item: dict[str, object] = {
            "id": f"media-{index:03d}",
            "source": str(source),
            "name": source.name,
            "type": "video" if source.suffix.lower() in VIDEO_EXTENSIONS else "image",
            **metadata,
        }
        if item["type"] == "video":
            sheet = sheets_dir / f"media-{index:03d}.jpg"
            create_contact_sheet(source, sheet, ffmpeg, args.sample_interval)
            item["contactSheet"] = str(sheet)
            item["sceneChangesSeconds"] = detect_cuts(source, ffmpeg, args.scene_threshold)
        report.append(item)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "media-report.json"
    report_path.write_text(json.dumps({"media": report}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Analyzed {len(report)} media file(s): {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
