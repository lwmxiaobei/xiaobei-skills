#!/usr/bin/env python3
"""Synchronize scene duration and estimated caption pages from narration audio."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from common import require_command


def probe_duration(path: Path) -> float:
    ffprobe = require_command("ffprobe")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def split_long_text(text: str, max_chars: int) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    sentences = [part.strip() for part in re.findall(r".*?(?:[。！？!?；;，,]|$)", text) if part.strip()]
    chunks: list[str] = []
    for sentence in sentences:
        while len(sentence) > max_chars:
            cut = max_chars
            for marker in ("，", ",", "、", " "):
                candidate = sentence.rfind(marker, 0, max_chars + 1)
                if candidate >= max_chars // 2:
                    cut = candidate + 1
                    break
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if sentence:
            chunks.append(sentence)
    return chunks or [text]


def make_captions(text: str, audio_duration: float, max_chars: int) -> list[dict[str, object]]:
    chunks = split_long_text(text, max_chars)
    if not chunks:
        return []
    start_padding = min(0.18, audio_duration * 0.03)
    end_padding = min(0.15, audio_duration * 0.03)
    usable = max(0.1, audio_duration - start_padding - end_padding)
    weights = [max(1, len(re.sub(r"\s", "", chunk))) for chunk in chunks]
    total_weight = sum(weights)
    cursor = start_padding
    captions: list[dict[str, object]] = []
    for index, (chunk, weight) in enumerate(zip(chunks, weights)):
        segment = usable * weight / total_weight
        end = audio_duration - end_padding if index == len(chunks) - 1 else cursor + segment
        captions.append(
            {
                "text": chunk,
                "startSeconds": round(cursor, 3),
                "endSeconds": round(max(cursor + 0.08, end), 3),
            }
        )
        cursor = end
    return captions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Video project directory")
    parser.add_argument("--max-chars", type=int, default=16, help="Maximum characters per caption page")
    parser.add_argument("--tail-padding", type=float, default=0.35, help="Silence after each narration")
    parser.add_argument(
        "--target-duration",
        type=float,
        help="Exact total video duration in seconds; distributes unused time as scene holds",
    )
    parser.add_argument(
        "--overrun-tolerance",
        type=float,
        default=0.15,
        help="Allowed target overrun before failing",
    )
    args = parser.parse_args()

    if args.target_duration is not None and args.target_duration <= 0:
        parser.error("--target-duration must be greater than zero")
    if args.overrun_tolerance < 0:
        parser.error("--overrun-tolerance must be nonnegative")

    project = args.project.expanduser().resolve()
    config_path = project / "video.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    updated = 0

    for scene in config.get("scenes", []):
        voiceover = scene.get("voiceover")
        narration = str(scene.get("narrationText", "")).strip()
        if not voiceover:
            continue
        audio_path = project / "public" / voiceover
        if not audio_path.is_file():
            raise SystemExit(f"Missing scene voiceover: {audio_path}")
        duration = probe_duration(audio_path)
        scene["durationSeconds"] = round(duration + args.tail_padding, 3)
        if narration:
            scene["captions"] = make_captions(narration, duration, args.max_chars)
        updated += 1

    scenes = config.get("scenes", [])
    if args.target_duration is not None and scenes:
        current_total = sum(float(scene.get("durationSeconds", 0)) for scene in scenes)
        overrun = current_total - args.target_duration
        if overrun > args.overrun_tolerance:
            raise SystemExit(
                f"Narration and scene holds total {current_total:.3f}s, exceeding the "
                f"{args.target_duration:.3f}s target by {overrun:.3f}s. "
                "Shorten the narration and synthesize it again."
            )

        remaining = args.target_duration - current_total
        if remaining > 0:
            positive_durations = [max(0.001, float(scene.get("durationSeconds", 0))) for scene in scenes]
            weight_total = sum(positive_durations)
            for scene, weight in zip(scenes, positive_durations):
                scene["durationSeconds"] = round(
                    float(scene.get("durationSeconds", 0)) + remaining * weight / weight_total,
                    3,
                )

        rounded_total = sum(float(scene.get("durationSeconds", 0)) for scene in scenes)
        correction = round(args.target_duration - rounded_total, 3)
        scenes[-1]["durationSeconds"] = round(
            float(scenes[-1].get("durationSeconds", 0)) + correction,
            3,
        )

    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(float(scene.get("durationSeconds", 0)) for scene in config.get("scenes", []))
    print(f"Updated {updated} scene(s), total {total:.3f}s: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
