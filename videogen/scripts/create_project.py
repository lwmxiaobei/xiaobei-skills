#!/usr/bin/env python3
"""Create an isolated video project from the bundled Remotion template."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "remotion-template"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Target project directory")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Merge the template into an existing directory and replace matching files",
    )
    args = parser.parse_args()

    output = args.output.expanduser().resolve()
    if not TEMPLATE_ROOT.is_dir():
        raise SystemExit(f"Template not found: {TEMPLATE_ROOT}")

    if output.exists() and any(output.iterdir()) and not args.force:
        raise SystemExit(
            f"Target is not empty: {output}\n"
            "Choose a new directory or pass --force to replace matching template files."
        )

    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE_ROOT, output, dirs_exist_ok=True)
    (output / "out").mkdir(exist_ok=True)

    print(f"Created video project: {output}")
    print(f"Edit configuration: {output / 'video.json'}")
    print(f"Validate with: python3 {SKILL_ROOT / 'scripts' / 'validate_project.py'} {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
