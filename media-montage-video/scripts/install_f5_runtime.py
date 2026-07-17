#!/usr/bin/env python3
"""Install the shared F5 TTS runtime used by media montage projects."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


F5_TTS_VERSION = "1.1.21"
PACKAGE_SPEC = f"f5-tts=={F5_TTS_VERSION}"
EXTRA_PACKAGES = ("httpx[socks]",)
RUNTIME_ROOT = (
    Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    / "runtimes"
    / "f5-tts"
    / F5_TTS_VERSION
)
VENV_ROOT = RUNTIME_ROOT / ".venv"


def venv_python(venv_root: Path, platform_name: str = os.name) -> Path:
    if platform_name == "nt":
        return venv_root / "Scripts" / "python.exe"
    return venv_root / "bin" / "python"


VENV_PYTHON = venv_python(VENV_ROOT)


@contextmanager
def install_lock(path: Path) -> Iterator[None]:
    with path.open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            while True:
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.25)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            return

        import fcntl

        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def python_has_f5(python: Path) -> bool:
    if not python.is_file():
        return False
    result = subprocess.run(
        [str(python), "-c", "import f5_tts, socksio"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def find_uv() -> Path | None:
    command = shutil.which("uv")
    if command:
        return Path(command)
    executable = "uv.exe" if os.name == "nt" else "uv"
    candidates = [
        Path.home() / ".local" / "bin" / executable,
        Path.home() / ".cargo" / "bin" / executable,
    ]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "uv" / executable)
    return next((path for path in candidates if path.is_file()), None)


def python_command_works(command: list[str]) -> bool:
    result = subprocess.run(
        [*command, "-c", "import sys; assert sys.version_info[:2] in {(3, 10), (3, 11)}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def find_compatible_python() -> list[str] | None:
    candidates: list[list[str]] = []
    for command in ("python3.11", "python3.10"):
        path = shutil.which(command)
        if path:
            candidates.append([path])
    if os.name == "nt":
        launcher = shutil.which("py")
        if launcher:
            candidates.extend(([launcher, "-3.11"], [launcher, "-3.10"]))
    for command in candidates:
        if python_command_works(command):
            return command
    return None


def install_with_uv(uv: Path) -> None:
    if not VENV_PYTHON.is_file():
        subprocess.run(
            [str(uv), "venv", "--python", "3.11", str(VENV_ROOT)],
            check=True,
        )
    subprocess.run(
        [
            str(uv),
            "pip",
            "install",
            "--python",
            str(VENV_PYTHON),
            PACKAGE_SPEC,
            *EXTRA_PACKAGES,
        ],
        check=True,
    )


def install_with_venv(python: list[str]) -> None:
    if not VENV_PYTHON.is_file():
        subprocess.run([*python, "-m", "venv", str(VENV_ROOT)], check=True)
    subprocess.run(
        [
            str(VENV_PYTHON),
            "-m",
            "pip",
            "install",
            "--upgrade",
            PACKAGE_SPEC,
            *EXTRA_PACKAGES,
        ],
        check=True,
    )


def main() -> int:
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    lock_path = RUNTIME_ROOT / ".install.lock"
    with install_lock(lock_path):
        if python_has_f5(VENV_PYTHON):
            print(f"F5 TTS runtime is ready: {VENV_PYTHON}")
            return 0

        uv = find_uv()
        try:
            if uv:
                print(f"Installing {PACKAGE_SPEC} with uv into {VENV_ROOT}")
                install_with_uv(uv)
            else:
                python = find_compatible_python()
                if python is None:
                    raise RuntimeError(
                        "Python 3.11 or 3.10 is required. Install uv or a compatible Python."
                    )
                print(
                    f"Installing {PACKAGE_SPEC} with {' '.join(python)} into {VENV_ROOT}"
                )
                install_with_venv(python)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            print(f"F5 TTS installation failed: {exc}", file=sys.stderr)
            return 1

        if not python_has_f5(VENV_PYTHON):
            print(
                f"Installation finished but f5_tts cannot be imported by {VENV_PYTHON}",
                file=sys.stderr,
            )
            return 1

        print(f"F5 TTS runtime installed: {VENV_PYTHON}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
