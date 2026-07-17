#!/usr/bin/env python3
"""Validate, install dependencies when needed, and render a media montage project."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent


def find_command(name: str) -> Path | None:
    direct = shutil.which(name)
    if direct:
        return Path(direct)
    candidates: list[Path] = [Path.home() / ".volta" / "bin" / name]
    nvm_root = Path.home() / ".nvm" / "versions" / "node"
    if nvm_root.is_dir():
        candidates.extend(sorted(nvm_root.glob(f"*/bin/{name}"), reverse=True))
    candidates.extend(
        [
            Path.home() / ".bun" / "bin" / name,
            Path("/opt/homebrew/bin") / name,
            Path("/usr/local/bin") / name,
        ]
    )
    return next((path for path in candidates if path.is_file()), None)


def project_command(project: Path, name: str, platform_name: str = os.name) -> Path:
    bin_dir = project / "node_modules" / ".bin"
    names = [f"{name}.cmd", f"{name}.exe", name] if platform_name == "nt" else [name]
    found = next((bin_dir / candidate for candidate in names if (bin_dir / candidate).is_file()), None)
    return found or (bin_dir / names[0])


def platform_command(
    executable: Path,
    arguments: list[str],
    platform_name: str = os.name,
    command_processor: str | None = None,
) -> list[str]:
    if platform_name == "nt" and executable.suffix.lower() in {".cmd", ".bat"}:
        processor = command_processor or os.environ.get("COMSPEC", "cmd.exe")
        command_line = subprocess.list2cmdline([str(executable), *arguments])
        return [processor, "/d", "/s", "/c", command_line]
    return [str(executable), *arguments]


def run(command: list[str], cwd: Path, env: dict[str, str]) -> None:
    print("Running:", " ".join(command))
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Video project directory")
    parser.add_argument("--output", type=Path, help="Output MP4 path")
    parser.add_argument("--skip-install", action="store_true", help="Fail instead of installing dependencies")
    parser.add_argument("--no-preview", action="store_true", help="Do not create a lightweight preview MP4")
    parser.add_argument("--preview-width", type=int, default=720, help="Preview width in pixels")
    parser.add_argument("--preview-crf", type=int, default=27, help="Preview H.264 CRF")
    args = parser.parse_args()

    if args.preview_width <= 0:
        parser.error("--preview-width must be greater than zero")
    if not 0 <= args.preview_crf <= 51:
        parser.error("--preview-crf must be between 0 and 51")

    project = args.project.expanduser().resolve()
    if not (project / "package.json").is_file():
        raise SystemExit(f"Not a media montage project: {project}")

    subprocess.run(
        [sys.executable, str(SKILL_ROOT / "scripts" / "validate_project.py"), str(project)],
        check=True,
    )

    env = os.environ.copy()
    npm = find_command("npm")
    if npm is None:
        raise SystemExit("npm was not found. Install Node.js or make npm available in PATH.")
    env["PATH"] = str(npm.parent) + os.pathsep + env.get("PATH", "")

    remotion = project_command(project, "remotion")
    if not remotion.is_file():
        if args.skip_install:
            raise SystemExit(f"Dependencies are missing: {project / 'node_modules'}")
        run(
            platform_command(npm, ["install", "--no-audit", "--no-fund"]),
            project,
            env,
        )
    if not remotion.is_file():
        raise SystemExit(f"Remotion CLI was not installed: {remotion}")

    output = (args.output or (project / "out" / "video.mp4")).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        platform_command(
            remotion,
            [
                "render",
                "src/index.ts",
                "MainVideo",
                str(output),
                "--codec=h264",
                "--overwrite",
            ],
        ),
        project,
        env,
    )
    print(f"Rendered video: {output}")

    if not args.no_preview:
        ffmpeg = find_command("ffmpeg") or (Path(shutil.which("ffmpeg")) if shutil.which("ffmpeg") else None)
        if ffmpeg is None:
            raise SystemExit("ffmpeg was not found, so the lightweight preview could not be created.")
        preview = output.with_name(f"{output.stem}_preview_720p.mp4")
        run(
            [
                str(ffmpeg),
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(output),
                "-vf",
                f"scale={args.preview_width}:-2:flags=lanczos",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                str(args.preview_crf),
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "96k",
                "-movflags",
                "+faststart",
                str(preview),
            ],
            project,
            env,
        )
        print(f"Rendered preview: {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
