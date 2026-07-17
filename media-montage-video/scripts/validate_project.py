#!/usr/bin/env python3
"""Validate a media montage video project before rendering."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath

from common import require_command


ALLOWED_ELEMENT_TYPES = {"image", "video", "text"}
ALLOWED_ENTRANCES = {"none", "fade", "rise", "left", "right", "pop"}
ALLOWED_ROLES = {"primary", "secondary", "tertiary", "static"}


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument(
        "--min-narration-coverage",
        type=float,
        default=0.90,
        help="Minimum voiceover share of narrated scene duration",
    )
    parser.add_argument(
        "--max-scene-tail",
        type=float,
        default=0.60,
        help="Maximum seconds a narrated scene may continue after its voiceover",
    )
    args = parser.parse_args()
    if not 0 < args.min_narration_coverage <= 1:
        parser.error("--min-narration-coverage must be greater than zero and at most one")
    if args.max_scene_tail < 0:
        parser.error("--max-scene-tail must be nonnegative")
    project = args.project.expanduser().resolve()
    config_path = project / "video.json"
    if not config_path.is_file():
        raise SystemExit(f"Missing configuration: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    def error(message: str) -> None:
        errors.append(message)

    def warning(message: str) -> None:
        warnings.append(message)

    def check_asset(value: object, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            error(f"{field} must be a nonempty string")
            return
        posix = PurePosixPath(value)
        if posix.is_absolute() or ".." in posix.parts:
            error(f"{field} must be relative to public and cannot contain ..")
            return
        if not (project / "public" / posix).is_file():
            error(f"Missing asset for {field}: {value}")

    video = config.get("video")
    if not isinstance(video, dict):
        error("video must be an object")
        video = {}
    for field in ("width", "height", "fps"):
        if not is_number(video.get(field)) or video[field] <= 0:
            error(f"video.{field} must be positive")

    theme = config.get("theme")
    if not isinstance(theme, dict):
        error("theme must be an object")
    layout = config.get("layout")
    if layout is not None and not isinstance(layout, dict):
        error("layout must be an object")
    elif isinstance(layout, dict) and layout.get("preset", "full-frame") not in {"full-frame", "tech-explainer"}:
        error("layout.preset must be full-frame or tech-explainer")

    audio = config.get("audio")
    if audio is not None:
        if not isinstance(audio, dict):
            error("audio must be an object")
        else:
            if audio.get("music"):
                check_asset(audio["music"], "audio.music")
            for field in ("musicVolume", "musicDuckingVolume"):
                if field in audio and (not is_number(audio[field]) or not 0 <= audio[field] <= 1):
                    error(f"audio.{field} must be between 0 and 1")

    scenes = config.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        error("scenes must be a nonempty array")
        scenes = []
    total_duration = 0.0
    narration_duration = 0.0
    narrated_scene_duration = 0.0
    scene_ids: set[str] = set()

    for scene_index, scene in enumerate(scenes):
        prefix = f"scenes[{scene_index}]"
        if not isinstance(scene, dict):
            error(f"{prefix} must be an object")
            continue
        scene_id = scene.get("id")
        if not isinstance(scene_id, str) or not scene_id:
            error(f"{prefix}.id must be a nonempty string")
        elif scene_id in scene_ids:
            error(f"Duplicate scene id: {scene_id}")
        else:
            scene_ids.add(scene_id)
        duration = scene.get("durationSeconds")
        if not is_number(duration) or duration <= 0:
            error(f"{prefix}.durationSeconds must be positive")
            duration = 0
        total_duration += float(duration)

        background = scene.get("background", {})
        if not isinstance(background, dict):
            error(f"{prefix}.background must be an object")
        elif background.get("src"):
            check_asset(background["src"], f"{prefix}.background.src")
        if scene.get("voiceover"):
            check_asset(scene["voiceover"], f"{prefix}.voiceover")
            if not str(scene.get("narrationText", "")).strip():
                warning(f"{prefix} has voiceover but no narrationText")
            voiceover_path = project / "public" / str(scene["voiceover"])
            if voiceover_path.is_file() and is_number(duration) and duration > 0:
                try:
                    voiceover_duration = probe_duration(voiceover_path)
                except (subprocess.CalledProcessError, ValueError) as exc:
                    error(f"Could not probe {prefix}.voiceover: {exc}")
                else:
                    narration_duration += voiceover_duration
                    narrated_scene_duration += float(duration)
                    tail = float(duration) - voiceover_duration
                    if tail < -0.05:
                        error(
                            f"{prefix}.durationSeconds cuts off voiceover by {-tail:.3f}s"
                        )
                    elif tail > args.max_scene_tail + 0.001:
                        error(
                            f"{prefix} continues {tail:.3f}s after voiceover; maximum is "
                            f"{args.max_scene_tail:.3f}s"
                        )

        elements = scene.get("elements", [])
        if not isinstance(elements, list):
            error(f"{prefix}.elements must be an array")
            elements = []
        element_ids: set[str] = set()
        for element_index, element in enumerate(elements):
            element_prefix = f"{prefix}.elements[{element_index}]"
            if not isinstance(element, dict):
                error(f"{element_prefix} must be an object")
                continue
            element_id = element.get("id")
            if not isinstance(element_id, str) or not element_id:
                error(f"{element_prefix}.id must be a nonempty string")
            elif element_id in element_ids:
                error(f"Duplicate element id in {prefix}: {element_id}")
            else:
                element_ids.add(element_id)
            element_type = element.get("type")
            if element_type not in ALLOWED_ELEMENT_TYPES:
                error(f"{element_prefix}.type must be image, video, or text")
                continue
            for field in ("x", "y", "width"):
                if not is_number(element.get(field)):
                    error(f"{element_prefix}.{field} must be a number")
            if is_number(element.get("width")) and element["width"] <= 0:
                error(f"{element_prefix}.width must be positive")
            if element_type in {"image", "video"}:
                check_asset(element.get("src"), f"{element_prefix}.src")
            if element_type == "image" and element.get("role", "secondary") not in ALLOWED_ROLES:
                error(f"{element_prefix}.role is invalid")
            if element_type == "video":
                if not is_number(element.get("height")) or element["height"] <= 0:
                    error(f"{element_prefix}.height must be positive")
                playback = element.get("playbackRate", 1)
                if not is_number(playback) or playback <= 0:
                    error(f"{element_prefix}.playbackRate must be positive")
                volume = element.get("volume", 0)
                if not is_number(volume) or not 0 <= volume <= 1:
                    error(f"{element_prefix}.volume must be between 0 and 1")
                before = element.get("trimBeforeSeconds", 0)
                after = element.get("trimAfterSeconds")
                if not is_number(before) or before < 0:
                    error(f"{element_prefix}.trimBeforeSeconds must be nonnegative")
                if after is not None and (not is_number(after) or after <= before):
                    error(f"{element_prefix}.trimAfterSeconds must be greater than trimBeforeSeconds")
                if element.get("loop") and after is None:
                    error(f"{element_prefix}.trimAfterSeconds is required when loop is true")
            if element_type == "text" and not str(element.get("text", "")).strip():
                error(f"{element_prefix}.text must be nonempty")
            enter = element.get("enter")
            if enter is not None:
                if not isinstance(enter, dict):
                    error(f"{element_prefix}.enter must be an object")
                elif enter.get("type", "fade") not in ALLOWED_ENTRANCES:
                    error(f"{element_prefix}.enter.type is invalid")

        captions = scene.get("captions", [])
        if not isinstance(captions, list):
            error(f"{prefix}.captions must be an array")
            captions = []
        for caption_index, caption in enumerate(captions):
            caption_prefix = f"{prefix}.captions[{caption_index}]"
            if not isinstance(caption, dict):
                error(f"{caption_prefix} must be an object")
                continue
            if not str(caption.get("text", "")).strip():
                error(f"{caption_prefix}.text must be nonempty")
            start = caption.get("startSeconds")
            end = caption.get("endSeconds")
            if not is_number(start) or not is_number(end) or start < 0 or end <= start:
                error(f"{caption_prefix} has invalid timing")
            elif end > duration + 0.001:
                error(f"{caption_prefix}.endSeconds exceeds scene duration")

    coverage = (
        narration_duration / narrated_scene_duration
        if narrated_scene_duration > 0
        else 1.0
    )
    if narrated_scene_duration > 0 and coverage + 0.0001 < args.min_narration_coverage:
        error(
            f"Narration covers only {coverage * 100:.1f}% of narrated scene time; "
            f"minimum is {args.min_narration_coverage * 100:.1f}%"
        )

    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}")
    if errors:
        print(f"Validation failed with {len(errors)} error(s) and {len(warnings)} warning(s)")
        return 1
    print(
        f"Validation passed: {len(scenes)} scene(s), {total_duration:.2f}s, "
        f"narration coverage {coverage * 100:.1f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
