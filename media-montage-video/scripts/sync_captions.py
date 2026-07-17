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
    parser.add_argument(
        "--tail-padding",
        type=float,
        default=0.12,
        help="Brief cadence pause after each narration",
    )
    parser.add_argument(
        "--target-duration",
        type=float,
        help="Exact total video duration in seconds; fails when narration is too short instead of padding silence",
    )
    parser.add_argument(
        "--overrun-tolerance",
        type=float,
        default=0.15,
        help="Allowed target overrun before failing",
    )
    parser.add_argument(
        "--max-silence-ratio",
        type=float,
        default=0.10,
        help="Maximum unvoiced share of the narrated timeline when an exact target is used",
    )
    parser.add_argument(
        "--max-scene-tail",
        type=float,
        default=0.60,
        help="Maximum seconds a narrated scene may continue after its voiceover",
    )
    args = parser.parse_args()

    if args.target_duration is not None and args.target_duration <= 0:
        parser.error("--target-duration must be greater than zero")
    if args.overrun_tolerance < 0:
        parser.error("--overrun-tolerance must be nonnegative")
    if not 0 <= args.max_silence_ratio < 1:
        parser.error("--max-silence-ratio must be between zero and one")
    if args.max_scene_tail < 0:
        parser.error("--max-scene-tail must be nonnegative")
    if args.tail_padding > args.max_scene_tail:
        parser.error("--tail-padding cannot exceed --max-scene-tail")

    project = args.project.expanduser().resolve()
    config_path = project / "video.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    updated = 0
    narrated: list[tuple[dict[str, object], float]] = []

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
        narrated.append((scene, duration))
        if narration:
            scene["captions"] = make_captions(narration, duration, args.max_chars)
        updated += 1

    scenes = config.get("scenes", [])
    if args.target_duration is not None and narrated:
        fixed_total = sum(
            float(scene.get("durationSeconds", 0))
            for scene in scenes
            if not scene.get("voiceover")
        )
        narration_window = args.target_duration - fixed_total
        if narration_window <= 0:
            raise SystemExit(
                f"Non-narrated scenes already use {fixed_total:.3f}s of the "
                f"{args.target_duration:.3f}s target. Shorten those scenes first."
            )

        audio_total = sum(duration for _, duration in narrated)
        required_hold = narration_window - audio_total
        if required_hold < 0:
            overrun = -required_hold
            qualifier = (
                f"more than the {args.overrun_tolerance:.3f}s tolerance"
                if overrun > args.overrun_tolerance
                else "even though the difference is small"
            )
            raise SystemExit(
                f"Narration audio plus fixed scenes exceeds the {args.target_duration:.3f}s "
                f"target by {overrun:.3f}s, {qualifier}. Shorten the narration and "
                "synthesize it again; audio will not be trimmed."
            )

        max_hold = narration_window * args.max_silence_ratio
        if required_hold > max_hold + 0.001:
            minimum_audio = narration_window - max_hold
            missing_audio = max(0.0, minimum_audio - audio_total)
            coverage = audio_total / narration_window * 100
            raise SystemExit(
                f"Narration covers only {coverage:.1f}% of the narrated "
                f"{narration_window:.3f}s timeline. Add about {missing_audio:.3f}s of "
                "spoken copy and synthesize it again. The script will not distribute "
                f"the {required_hold:.3f}s gap as silent scene holds."
            )

        weight_total = max(0.001, audio_total)
        allocated: list[float] = []
        for scene, duration in narrated:
            tail = required_hold * duration / weight_total
            if tail > args.max_scene_tail + 0.001:
                raise SystemExit(
                    f"Scene {scene.get('id', '<unknown>')} would need a {tail:.3f}s "
                    f"silent tail, above the {args.max_scene_tail:.3f}s limit. Revise "
                    "the narration and synthesize it again."
                )
            allocated.append(tail)
            scene["durationSeconds"] = round(duration + tail, 3)

        rounded_total = sum(float(scene.get("durationSeconds", 0)) for scene in scenes)
        correction = round(args.target_duration - rounded_total, 3)
        last_scene, last_audio_duration = narrated[-1]
        corrected_duration = round(float(last_scene["durationSeconds"]) + correction, 3)
        corrected_tail = corrected_duration - last_audio_duration
        if corrected_tail > args.max_scene_tail + 0.001:
            raise SystemExit("Rounding correction would exceed the per-scene tail limit")
        last_scene["durationSeconds"] = corrected_duration
    elif args.target_duration is not None and scenes:
        current_total = sum(float(scene.get("durationSeconds", 0)) for scene in scenes)
        difference = abs(current_total - args.target_duration)
        if difference > args.overrun_tolerance:
            raise SystemExit(
                f"Project has no generated narration and totals {current_total:.3f}s, "
                f"not the {args.target_duration:.3f}s target."
            )

    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(float(scene.get("durationSeconds", 0)) for scene in config.get("scenes", []))
    audio_total = sum(duration for _, duration in narrated)
    narrated_total = sum(float(scene.get("durationSeconds", 0)) for scene, _ in narrated)
    coverage = audio_total / narrated_total * 100 if narrated_total > 0 else 100.0
    largest_tail = max(
        (float(scene.get("durationSeconds", 0)) - duration for scene, duration in narrated),
        default=0.0,
    )
    print(
        f"Updated {updated} scene(s), total {total:.3f}s, narration {audio_total:.3f}s, "
        f"coverage {coverage:.1f}%, largest scene tail {largest_tail:.3f}s: {config_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
