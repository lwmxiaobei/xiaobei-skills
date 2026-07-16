#!/usr/bin/env python3
"""Inspect a rendered video and extract representative quality assurance frames."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from common import require_command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Rendered video path")
    parser.add_argument("--report-dir", type=Path, help="Directory for report and frames")
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    if not video.is_file():
        raise SystemExit(f"Video does not exist: {video}")
    report_dir = (args.report_dir or video.parent / "qa").expanduser().resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    ffprobe = require_command("ffprobe")
    ffmpeg = require_command("ffmpeg")
    probe = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(probe.stdout)
    streams = metadata.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if not video_streams:
        raise SystemExit("No video stream found")

    duration = float(metadata.get("format", {}).get("duration") or 0)
    if duration <= 0:
        raise SystemExit("Invalid rendered duration")

    timestamps = [min(0.2, duration / 4), duration / 2, max(0, duration - 0.2)]
    frames: list[str] = []
    for index, timestamp in enumerate(timestamps, start=1):
        frame_path = report_dir / f"frame-{index:02d}.png"
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(video),
                "-frames:v",
                "1",
                str(frame_path),
            ],
            check=True,
        )
        frames.append(str(frame_path))

    black = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(video),
            "-vf",
            "blackdetect=d=0.3:pix_th=0.10",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    black_intervals = [
        {"start": float(start), "end": float(end), "duration": float(length)}
        for start, end, length in re.findall(
            r"black_start:([0-9.]+)\s+black_end:([0-9.]+)\s+black_duration:([0-9.]+)",
            black.stderr,
        )
    ]

    primary = video_streams[0]
    report = {
        "video": str(video),
        "sizeBytes": video.stat().st_size,
        "durationSeconds": duration,
        "width": primary.get("width"),
        "height": primary.get("height"),
        "videoCodec": primary.get("codec_name"),
        "audioStreams": len(audio_streams),
        "blackIntervals": black_intervals,
        "frames": frames,
    }
    report_path = report_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if black_intervals:
        print("WARNING: black intervals were detected and require visual review")
    print(f"Inspection report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
