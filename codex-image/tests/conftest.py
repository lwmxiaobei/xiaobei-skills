"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

# Make ``scripts/`` importable as top-level modules.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
