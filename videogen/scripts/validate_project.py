#!/usr/bin/env python3
"""Validate video.json and every local media reference before rendering."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ALLOWED_ENTRANCES = {"none", "fade", "rise", "left", "right", "pop"}
ALLOWED_ROLES = {"primary", "secondary", "tertiary", "static"}


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Video project directory")
    args = parser.parse_args()

    project = args.project.expanduser().resolve()
    public = project / "public"
    config_path = project / "video.json"
    errors: list[str] = []
    warnings: list[str] = []

    if not config_path.is_file():
        raise SystemExit(f"Missing configuration: {config_path}")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON in {config_path}: {error}") from error

    def error(message: str) -> None:
        errors.append(message)

    def warning(message: str) -> None:
        warnings.append(message)

    def check_asset(relative: Any, label: str) -> None:
        if not isinstance(relative, str) or not relative.strip():
            error(f"{label} must be a nonempty relative path")
            return
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            error(f"{label} must stay inside public: {relative}")
            return
        resolved = (public / path).resolve()
        try:
            resolved.relative_to(public.resolve())
        except ValueError:
            error(f"{label} escapes public: {relative}")
            return
        if not resolved.is_file():
            error(f"{label} does not exist: {resolved}")

    if config.get("schemaVersion") != 1:
        error("schemaVersion must equal 1")
    if not isinstance(config.get("id"), str) or not config["id"].strip():
        error("id must be a nonempty string")
    if not isinstance(config.get("title"), str) or not config["title"].strip():
        error("title must be a nonempty string")

    video = config.get("video")
    if not isinstance(video, dict):
        error("video must be an object")
        video = {}
    for field in ("width", "height", "fps"):
        value = video.get(field)
        if not is_number(value) or value <= 0:
            error(f"video.{field} must be a positive number")
    if is_number(video.get("width")) and is_number(video.get("height")):
        if video["width"] < 480 or video["height"] < 480:
            warning("Video dimensions are unusually small")

    audio = config.get("audio")
    if audio is not None:
        if not isinstance(audio, dict):
            error("audio must be an object when present")
        elif audio.get("music"):
            check_asset(audio["music"], "audio.music")
            volume = audio.get("musicVolume", 0.12)
            if not is_number(volume) or not 0 <= volume <= 1:
                error("audio.musicVolume must be between 0 and 1")

    scenes = config.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        error("scenes must be a nonempty array")
        scenes = []

    scene_ids: set[str] = set()
    total_duration = 0.0
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
        else:
            if not background.get("color") and not background.get("src"):
                warning(f"{prefix}.background has neither color nor src")
            if background.get("src"):
                check_asset(background["src"], f"{prefix}.background.src")

        if scene.get("voiceover"):
            check_asset(scene["voiceover"], f"{prefix}.voiceover")
            if not str(scene.get("narrationText", "")).strip():
                warning(f"{prefix} has voiceover but no narrationText")

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
            if element_type == "image":
                check_asset(element.get("src"), f"{element_prefix}.src")
                if not is_number(element.get("width")) or element["width"] <= 0:
                    error(f"{element_prefix}.width must be positive")
                role = element.get("role", "secondary")
                if role not in ALLOWED_ROLES:
                    error(f"{element_prefix}.role is invalid: {role}")
            elif element_type == "text":
                if not isinstance(element.get("text"), str) or not element["text"].strip():
                    error(f"{element_prefix}.text must be nonempty")
                if not is_number(element.get("width")) or element["width"] <= 0:
                    error(f"{element_prefix}.width must be positive")
            else:
                error(f"{element_prefix}.type must be image or text")

            for field in ("x", "y"):
                if not is_number(element.get(field)):
                    error(f"{element_prefix}.{field} must be a number")
            enter = element.get("enter")
            if enter is not None:
                if not isinstance(enter, dict):
                    error(f"{element_prefix}.enter must be an object")
                elif enter.get("type", "fade") not in ALLOWED_ENTRANCES:
                    error(f"{element_prefix}.enter.type is invalid: {enter.get('type')}")

        captions = scene.get("captions", [])
        if not isinstance(captions, list):
            error(f"{prefix}.captions must be an array")
            captions = []
        for caption_index, caption in enumerate(captions):
            caption_prefix = f"{prefix}.captions[{caption_index}]"
            if not isinstance(caption, dict):
                error(f"{caption_prefix} must be an object")
                continue
            if not isinstance(caption.get("text"), str) or not caption["text"].strip():
                error(f"{caption_prefix}.text must be nonempty")
            start = caption.get("startSeconds")
            end = caption.get("endSeconds")
            if not is_number(start) or not is_number(end) or start < 0 or end <= start:
                error(f"{caption_prefix} has invalid timing")
            elif end > duration + 0.001:
                error(f"{caption_prefix}.endSeconds exceeds scene duration")

    if total_duration > 180:
        warning(f"Video is longer than the normal short video range: {total_duration:.2f}s")

    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}")

    if errors:
        print(f"Validation failed with {len(errors)} error(s) and {len(warnings)} warning(s)")
        return 1

    print(
        f"Validation passed: {len(scenes)} scene(s), "
        f"{total_duration:.2f}s, {int(video.get('width', 0))}x{int(video.get('height', 0))}"
    )
    if warnings:
        print(f"Review {len(warnings)} warning(s) before rendering")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
