#!/usr/bin/env python3
"""Synthesize one or more narration clips with F5 TTS."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE_AUDIO = SKILL_ROOT / "assets" / "voice" / "user-narrator-reference.wav"
DEFAULT_REFERENCE_TEXT = (
    "六百多年前，明朝把一支巨大的船队，派向了从未真正看清的远方。"
    "第一件事，不是出发，而是集结。南京港口把国书、瓷器和丝绸，一件件装上宝船。"
)


def python_has_f5(python: Path) -> bool:
    if not python.is_file():
        return False
    try:
        result = subprocess.run(
            [str(python), "-c", "import f5_tts"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def nearby_python_candidates(path: Path) -> list[Path]:
    base = path if path.is_dir() else path.parent
    roots = [base, *list(base.parents)[:5]]
    return [
        root / environment / "bin" / "python"
        for root in roots
        for environment in (".venv", "venv", "env")
    ]


def discover_f5_python(args: argparse.Namespace) -> tuple[Path | None, list[Path]]:
    candidates: list[Path] = []

    def add(value: str | Path | None) -> None:
        if not value:
            return
        path = Path(value).expanduser()
        try:
            absolute = Path(os.path.abspath(path))
        except OSError:
            return
        if absolute not in candidates:
            candidates.append(absolute)

    add(args.python)
    add(os.environ.get("VIDEOGEN_F5_PYTHON"))
    add(os.environ.get("F5_TTS_PYTHON"))
    add(sys.executable)

    for environment_name in ("VIRTUAL_ENV", "CONDA_PREFIX"):
        environment = os.environ.get(environment_name)
        if environment:
            add(Path(environment) / "bin" / "python")

    hints = [Path.cwd(), SKILL_ROOT]
    for value in (args.manifest, args.output, args.reference_audio):
        if value:
            hints.append(Path(value).expanduser())
    for hint in hints:
        for candidate in nearby_python_candidates(hint):
            add(candidate)

    add(shutil.which("python3"))
    add(shutil.which("python"))

    for candidate in candidates:
        if python_has_f5(candidate):
            return candidate, candidates
    return None, candidates


def ensure_f5_runtime(args: argparse.Namespace) -> None:
    candidate, checked = discover_f5_python(args)
    if candidate is None:
        checked_text = "\n".join(f"  {path}" for path in checked)
        raise SystemExit(
            "No Python environment with f5_tts was found. Install F5 TTS, activate its "
            "environment, pass --python /path/to/.venv/bin/python, or set "
            "VIDEOGEN_F5_PYTHON. Checked:\n"
            f"{checked_text}"
        )

    current = Path(os.path.abspath(sys.executable))
    if candidate != current:
        print(f"Using F5 TTS Python: {candidate}", file=sys.stderr)
        os.execv(str(candidate), [str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]])


def load_jobs(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.manifest:
        manifest = args.manifest.expanduser().resolve()
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(payload, list) or not payload:
            raise SystemExit("Manifest must be a non-empty JSON array")
        jobs: list[dict[str, Any]] = []
        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                raise SystemExit(f"Manifest item {index} must be an object")
            text = str(item.get("text", "")).strip()
            output_value = str(item.get("output", "")).strip()
            if not text or not output_value:
                raise SystemExit(f"Manifest item {index} needs text and output")
            output = Path(output_value).expanduser()
            if not output.is_absolute():
                output = manifest.parent / output
            jobs.append(
                {
                    "text": text,
                    "output": output.resolve(),
                    "seed": int(item.get("seed", args.seed + index)),
                }
            )
        return jobs

    text = (args.text or "").strip()
    if not text:
        raise SystemExit("Narration text is empty")
    return [{"text": text, "output": args.output.expanduser().resolve(), "seed": args.seed}]


def normalize_audio(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar",
            "24000",
            "-ac",
            "1",
            str(destination),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="Narration text")
    source.add_argument("--manifest", type=Path, help="JSON array with text and output fields")
    parser.add_argument("--output", type=Path, help="Output WAV path when using --text")
    parser.add_argument("--python", type=Path, help="Python interpreter containing f5_tts")
    parser.add_argument(
        "--check-runtime",
        action="store_true",
        help="Locate an F5 TTS Python environment and exit without loading a model",
    )
    parser.add_argument("--reference-audio", type=Path, default=DEFAULT_REFERENCE_AUDIO)
    parser.add_argument("--reference-text", default=DEFAULT_REFERENCE_TEXT)
    parser.add_argument("--model", default="F5TTS_v1_Base")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=2026071510)
    parser.add_argument("--device", help="Optional F5 TTS device override")
    parser.add_argument("--no-normalize", action="store_true")
    args = parser.parse_args()

    if not args.check_runtime and not args.text and not args.manifest:
        parser.error("one of --text or --manifest is required")
    if args.text and args.output is None:
        parser.error("--output is required with --text")
    if args.speed <= 0:
        parser.error("--speed must be greater than zero")

    ensure_f5_runtime(args)

    try:
        import f5_tts
        from f5_tts.api import F5TTS
    except ImportError as exc:
        raise SystemExit("The selected Python environment could not import f5_tts.") from exc

    if args.check_runtime:
        cli = Path(sys.executable).with_name("f5-tts_infer-cli")
        print(f"F5 TTS Python: {Path(os.path.abspath(sys.executable))}")
        print(f"F5 TTS package: {Path(f5_tts.__path__[0]).resolve()}")
        print(f"F5 TTS CLI: {cli if cli.is_file() else 'not installed beside Python'}")
        return 0

    reference_audio = args.reference_audio.expanduser().resolve()
    if not reference_audio.is_file():
        raise SystemExit(f"Reference audio not found: {reference_audio}")
    if not args.reference_text.strip():
        raise SystemExit("Reference transcript is empty")

    jobs = load_jobs(args)
    init_args: dict[str, Any] = {"model": args.model}
    if args.device:
        init_args["device"] = args.device
    tts = F5TTS(**init_args)
    print(f"F5 TTS device: {tts.device}")

    with tempfile.TemporaryDirectory(prefix="videogen-f5-") as temp_dir:
        temp = Path(temp_dir)
        for index, job in enumerate(jobs, start=1):
            output: Path = job["output"]
            output.parent.mkdir(parents=True, exist_ok=True)
            raw_output = output if args.no_normalize else temp / f"scene-{index:03d}.wav"
            tts.infer(
                ref_file=str(reference_audio),
                ref_text=args.reference_text,
                gen_text=job["text"],
                speed=args.speed,
                nfe_step=32,
                cfg_strength=2,
                sway_sampling_coef=-1,
                remove_silence=False,
                file_wave=str(raw_output),
                seed=job["seed"],
            )
            if not args.no_normalize:
                normalize_audio(raw_output, output)
            print(f"Created narration: {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
