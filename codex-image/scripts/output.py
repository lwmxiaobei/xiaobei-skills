"""Filesystem output helpers."""

from __future__ import annotations

import base64
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from auth import codex_home

EXTENSION_BY_FORMAT = {
    "png": ".png",
    "webp": ".webp",
    "jpeg": ".jpg",
    "jpg": ".jpg",
}


def default_output_dir() -> Path:
    return codex_home() / "generated_images" / "codex-image"


def _slugify(text: str, *, max_length: int = 48) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text.strip().lower()).strip("-")
    if not cleaned:
        cleaned = "image"
    return cleaned[:max_length].rstrip("-") or "image"


def default_path(slug_source: str, output_format: str) -> Path:
    ext = EXTENSION_BY_FORMAT.get(output_format.lower())
    if ext is None:
        raise ValueError(f"unsupported output format {output_format!r}")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slugify(slug_source)
    return default_output_dir() / f"{timestamp}-{slug}{ext}"


def _avoid_collision(path: Path) -> Path:
    if not path.exists():
        return path
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    n = 2
    while True:
        candidate = parent / f"{stem}-v{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def save(
    image_b64: str,
    out_path: Path | None,
    *,
    force: bool = False,
    slug_source: str | None = None,
    output_format: str = "png",
) -> Path:
    """Decode *image_b64* and write it to disk. Returns the absolute path."""

    try:
        data = base64.b64decode(image_b64, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid base64 payload: {exc}") from exc

    if out_path is None:
        target = default_path(slug_source or "image", output_format)
        target.parent.mkdir(parents=True, exist_ok=True)
    else:
        target = out_path.expanduser().resolve()
        if not target.parent.exists():
            raise FileNotFoundError(
                f"output directory does not exist: {target.parent}"
            )
        if target.exists() and not force:
            target = _avoid_collision(target)

    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, target)
    return target.resolve()
