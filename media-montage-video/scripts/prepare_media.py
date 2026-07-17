#!/usr/bin/env python3
"""Normalize supplied media and place portable copies in a montage project."""

from __future__ import annotations

import argparse
import json
import shutil
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
        "videoCodec": video.get("codec_name"),
        "hasAudio": audio is not None,
    }


def normalize_video(source: Path, output: Path, ffmpeg: str, fps: int, max_dimension: int) -> None:
    scale = (
        f"scale='if(gt(iw,ih),min(iw,{max_dimension}),-2)':"
        f"'if(gt(iw,ih),-2,min(ih,{max_dimension}))',fps={fps}"
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-vf",
            scale,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Media montage project directory")
    parser.add_argument("sources", nargs="+", type=Path, help="Media files or directories")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--max-dimension", type=int, default=1920)
    args = parser.parse_args()
    if args.fps <= 0 or args.max_dimension <= 0:
        parser.error("--fps and --max-dimension must be positive")

    project = args.project.expanduser().resolve()
    if not (project / "video.json").is_file():
        raise SystemExit(f"Not a media montage project: {project}")
    target = project / "public" / "assets" / "source"
    target.mkdir(parents=True, exist_ok=True)
    ffmpeg = require_command("ffmpeg")
    ffprobe = require_command("ffprobe")
    manifest: list[dict[str, object]] = []

    for index, source in enumerate(collect_sources(args.sources), start=1):
        media_id = f"media-{index:03d}"
        if source.suffix.lower() in VIDEO_EXTENSIONS:
            output = target / f"{media_id}.mp4"
            normalize_video(source, output, ffmpeg, args.fps, args.max_dimension)
            media_type = "video"
        else:
            extension = ".jpg" if source.suffix.lower() == ".jpeg" else source.suffix.lower()
            output = target / f"{media_id}{extension}"
            shutil.copy2(source, output)
            media_type = "image"
        manifest.append(
            {
                "id": media_id,
                "type": media_type,
                "sourceName": source.name,
                "src": output.relative_to(project / "public").as_posix(),
                **probe(output, ffprobe),
            }
        )

    manifest_path = project / "media-manifest.json"
    manifest_path.write_text(json.dumps({"media": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(manifest)} media file(s): {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
