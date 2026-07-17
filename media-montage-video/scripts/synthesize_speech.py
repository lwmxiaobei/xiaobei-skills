#!/usr/bin/env python3
"""Synthesize narration with the macOS system voice and convert it to WAV."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from common import require_command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Narration text")
    source.add_argument("--text-file", type=Path, help="UTF-8 text file")
    parser.add_argument("--output", required=True, type=Path, help="Output WAV path")
    parser.add_argument("--voice", help="macOS voice name, for example Tingting")
    parser.add_argument("--rate", type=int, default=185, help="Speaking rate in words per minute")
    args = parser.parse_args()

    say = require_command("say")
    ffmpeg = require_command("ffmpeg")

    if args.text_file:
        text = args.text_file.expanduser().read_text(encoding="utf-8").strip()
    else:
        text = (args.text or "").strip()
    if not text:
        raise SystemExit("Narration text is empty")

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="videogen-tts-") as temp_dir:
        temp = Path(temp_dir)
        text_path = temp / "narration.txt"
        aiff_path = temp / "narration.aiff"
        text_path.write_text(text, encoding="utf-8")

        command = [say, "-r", str(args.rate), "-f", str(text_path), "-o", str(aiff_path)]
        if args.voice:
            command[1:1] = ["-v", args.voice]
        subprocess.run(command, check=True)
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(aiff_path),
                "-ar",
                "48000",
                "-ac",
                "1",
                str(output),
            ],
            check=True,
        )

    print(f"Created narration: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
