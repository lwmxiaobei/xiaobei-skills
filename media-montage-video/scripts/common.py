"""Shared command discovery helpers for media montage scripts."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional


def find_command(name: str) -> Optional[str]:
    direct = shutil.which(name)
    if direct:
        return direct
    candidates = [
        Path("/opt/homebrew/bin") / name,
        Path("/usr/local/bin") / name,
        Path.home() / ".volta" / "bin" / name,
        Path.home() / ".bun" / "bin" / name,
    ]
    nvm_root = Path.home() / ".nvm" / "versions" / "node"
    if nvm_root.is_dir():
        candidates.extend(sorted(nvm_root.glob(f"*/bin/{name}"), reverse=True))
    found = next((path for path in candidates if path.is_file()), None)
    return str(found) if found else None


def require_command(name: str) -> str:
    command = find_command(name)
    if command is None:
        raise SystemExit(f"Required command not found: {name}")
    return command
