"""Unit tests for :mod:`output`."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

import output


def _payload(data: bytes = b"hello-bytes") -> str:
    return base64.b64encode(data).decode("ascii")


def test_save_explicit_path(tmp_path: Path) -> None:
    target = tmp_path / "out.png"
    written = output.save(_payload(b"abc"), target, output_format="png")
    assert written == target.resolve()
    assert target.read_bytes() == b"abc"


def test_save_collision_appends_version(tmp_path: Path) -> None:
    target = tmp_path / "out.png"
    target.write_bytes(b"old")
    written = output.save(_payload(b"new"), target, output_format="png")
    assert written.name == "out-v2.png"
    assert target.read_bytes() == b"old"
    assert written.read_bytes() == b"new"


def test_save_force_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "out.png"
    target.write_bytes(b"old")
    written = output.save(_payload(b"new"), target, force=True, output_format="png")
    assert written == target.resolve()
    assert target.read_bytes() == b"new"


def test_save_missing_parent_raises(tmp_path: Path) -> None:
    target = tmp_path / "nope" / "out.png"
    with pytest.raises(FileNotFoundError):
        output.save(_payload(), target, output_format="png")


def test_save_default_path_uses_codex_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    written = output.save(_payload(b"x"), None, output_format="png", slug_source="A panda!")
    assert written.parent == (tmp_path / "generated_images" / "codex-image").resolve()
    assert written.suffix == ".png"
    assert "a-panda" in written.name


def test_save_rejects_unsupported_format(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        output.default_path("x", "gif")


def test_save_bad_base64_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        output.save("###not-base64###", tmp_path / "out.png", output_format="png")


def test_default_path_supports_webp_and_jpeg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    assert output.default_path("foo", "webp").suffix == ".webp"
    assert output.default_path("foo", "jpeg").suffix == ".jpg"
