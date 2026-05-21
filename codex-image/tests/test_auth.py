"""Unit tests for :mod:`auth`."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import jwt as pyjwt
import pytest
import responses

import auth


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _make_jwt(exp_offset_seconds: int, extra: dict | None = None) -> str:
    claims = {"exp": int(time.time()) + exp_offset_seconds}
    if extra:
        claims.update(extra)
    return pyjwt.encode(claims, "secret", algorithm="HS256")


@pytest.fixture
def codex_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "codex"
    monkeypatch.setenv("CODEX_HOME", str(home))
    return home


def _write_auth(codex_dir: Path, payload: dict) -> Path:
    codex_dir.mkdir(parents=True, exist_ok=True)
    path = codex_dir / "auth.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# _load_auth_json
# ---------------------------------------------------------------------------


def test_load_auth_json_missing(codex_dir: Path) -> None:
    assert auth._load_auth_json() is None


def test_load_auth_json_corrupt_backs_up(codex_dir: Path) -> None:
    codex_dir.mkdir(parents=True, exist_ok=True)
    bad = codex_dir / "auth.json"
    bad.write_text("not json{", encoding="utf-8")
    with pytest.raises(auth.AuthError):
        auth._load_auth_json()
    # Original should have been renamed.
    assert not bad.exists()
    backups = list(codex_dir.glob("auth.json.broken-*"))
    assert backups, "broken file should be backed up"


# ---------------------------------------------------------------------------
# _decode_jwt_exp
# ---------------------------------------------------------------------------


def test_decode_jwt_exp_returns_int() -> None:
    token = _make_jwt(60)
    assert auth._decode_jwt_exp(token) is not None


def test_decode_jwt_exp_invalid_returns_none() -> None:
    assert auth._decode_jwt_exp("not-a-jwt") is None


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------


def test_logout_strips_tokens_but_keeps_file(codex_dir: Path) -> None:
    _write_auth(
        codex_dir,
        {
            "auth_mode": "Chatgpt",
            "tokens": {"access_token": "x", "refresh_token": "y"},
            "last_refresh": "2025-01-01T00:00:00+00:00",
        },
    )
    auth.logout()
    data = json.loads((codex_dir / "auth.json").read_text())
    assert "tokens" not in data
    assert data["auth_mode"] == "Chatgpt"
    assert data["last_refresh"] == "2025-01-01T00:00:00+00:00"


def test_logout_when_no_file_is_noop(codex_dir: Path) -> None:
    auth.logout()  # should not raise
    assert not (codex_dir / "auth.json").exists()


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


def test_status_missing_raises(codex_dir: Path) -> None:
    with pytest.raises(auth.AuthError):
        auth.status()


def test_status_reports_email_plan_and_expiry(codex_dir: Path) -> None:
    id_token = _make_jwt(
        3600,
        {
            "email": "user@example.com",
            "https://api.openai.com/auth": {"chatgpt_plan_type": "plus"},
        },
    )
    access_token = _make_jwt(3600)
    _write_auth(
        codex_dir,
        {
            "auth_mode": "Chatgpt",
            "tokens": {
                "id_token": id_token,
                "access_token": access_token,
                "refresh_token": "r",
                "account_id": "acct_1",
            },
            "last_refresh": "2025-01-01T00:00:00+00:00",
        },
    )
    info = auth.status()
    assert info["email"] == "user@example.com"
    assert info["plan"] == "plus"
    assert info["account_id"] == "acct_1"
    assert info["expires_at"].startswith("20")


# ---------------------------------------------------------------------------
# refresh_tokens — happy path
# ---------------------------------------------------------------------------


@responses.activate
def test_refresh_tokens_success_persists(codex_dir: Path) -> None:
    _write_auth(
        codex_dir,
        {
            "auth_mode": "Chatgpt",
            "tokens": {
                "id_token": _make_jwt(60),
                "access_token": _make_jwt(60),
                "refresh_token": "old-refresh",
                "account_id": "acct_1",
            },
            "last_refresh": "2025-01-01T00:00:00+00:00",
        },
    )

    new_access = _make_jwt(3600)
    responses.add(
        responses.POST,
        auth.TOKEN_URL,
        json={
            "access_token": new_access,
            "refresh_token": "new-refresh",
            "id_token": _make_jwt(3600),
        },
        status=200,
    )

    creds = auth.refresh_tokens("old-refresh", force=True)
    assert creds.access_token == new_access
    assert creds.refresh_token == "new-refresh"

    on_disk = json.loads((codex_dir / "auth.json").read_text())
    assert on_disk["tokens"]["access_token"] == new_access
    assert on_disk["tokens"]["refresh_token"] == "new-refresh"


@responses.activate
def test_refresh_tokens_expired_clears_tokens(codex_dir: Path) -> None:
    _write_auth(
        codex_dir,
        {
            "auth_mode": "Chatgpt",
            "tokens": {
                "id_token": "x",
                "access_token": "y",
                "refresh_token": "old",
                "account_id": "z",
            },
            "last_refresh": "2025-01-01T00:00:00+00:00",
        },
    )

    responses.add(
        responses.POST,
        auth.TOKEN_URL,
        json={"error": "refresh_token_expired"},
        status=400,
    )

    with pytest.raises(auth.AuthError):
        auth.refresh_tokens("old", force=True)

    on_disk = json.loads((codex_dir / "auth.json").read_text())
    assert "tokens" not in on_disk
    assert on_disk["auth_mode"] == "Chatgpt"


# ---------------------------------------------------------------------------
# _resolve_credentials — token still fresh
# ---------------------------------------------------------------------------


def test_resolve_credentials_returns_fresh_token(
    codex_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fresh = _make_jwt(3600)
    _write_auth(
        codex_dir,
        {
            "auth_mode": "Chatgpt",
            "tokens": {
                "id_token": _make_jwt(3600),
                "access_token": fresh,
                "refresh_token": "r",
                "account_id": "acct",
            },
            "last_refresh": "2025-01-01T00:00:00+00:00",
        },
    )

    def _boom(*_args, **_kwargs):
        raise AssertionError("should not refresh when token is fresh")

    monkeypatch.setattr(auth, "refresh_tokens", _boom)
    monkeypatch.setattr(auth, "interactive_login", _boom)

    assert auth.get_access_token() == fresh


# ---------------------------------------------------------------------------
# _resolve_credentials — token near expiry triggers refresh
# ---------------------------------------------------------------------------


def test_resolve_credentials_triggers_refresh_when_near_expiry(
    codex_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    soon = _make_jwt(60)  # within 5min leeway → refresh
    _write_auth(
        codex_dir,
        {
            "auth_mode": "Chatgpt",
            "tokens": {
                "id_token": _make_jwt(60),
                "access_token": soon,
                "refresh_token": "rrr",
                "account_id": "acct",
            },
            "last_refresh": "2025-01-01T00:00:00+00:00",
        },
    )

    refreshed_creds = auth.Credentials(
        access_token="REFRESHED",
        refresh_token="rrr2",
        id_token=None,
        account_id="acct",
        last_refresh=auth._now_iso(),
        source=codex_dir / "auth.json",
    )

    called = {"n": 0}

    def fake_refresh(refresh_token: str, *, force: bool = False):
        called["n"] += 1
        assert refresh_token == "rrr"
        return refreshed_creds

    monkeypatch.setattr(auth, "refresh_tokens", fake_refresh)
    monkeypatch.setattr(
        auth,
        "interactive_login",
        lambda: pytest.fail("should not fall back to OAuth"),
    )

    assert auth.get_access_token() == "REFRESHED"
    assert called["n"] == 1


# ---------------------------------------------------------------------------
# PKCE helpers — light sanity check
# ---------------------------------------------------------------------------


def test_pkce_pair_uses_s256() -> None:
    import hashlib

    verifier, challenge = auth._make_pkce_pair()
    digest = hashlib.sha256(verifier.encode()).digest()
    expected = (
        base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    )
    assert challenge == expected
