"""Shared HTTP session factory.

Centralises all "fingerprint" headers so :mod:`auth` and
:mod:`responses_client` send byte-identical metadata.

The codex CLI emits a small, deterministic set of headers; this module
constructs the same set and explicitly removes the headers that
``requests`` adds by default but ``codex`` does not.
"""

from __future__ import annotations

import os
import platform
import uuid
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Fingerprint constants — keep in sync with references/fingerprint.md.
# ---------------------------------------------------------------------------

ORIGINATOR = "codex_cli_rs"
CODEX_PRETEND_VERSION = "0.130.0"
# OAuth client_id used by the official codex CLI (codex-rs/login/src/auth/manager.rs).
OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
OAUTH_SCOPE = (
    "openid profile email offline_access "
    "api.connectors.read api.connectors.invoke"
)
USER_AGENT_TEMPLATE = "codex_cli_rs/{version} ({os_type} {os_ver}; {arch}) {terminal}"
# Required by chatgpt.com/backend-api/codex/responses for ChatGPT-account tokens.
OPENAI_BETA_HEADER_VALUE = "responses=experimental"


def _detect_terminal() -> str:
    return os.environ.get("TERM_PROGRAM") or "unknown"


def build_user_agent() -> str:
    return USER_AGENT_TEMPLATE.format(
        version=CODEX_PRETEND_VERSION,
        os_type=platform.system(),
        os_ver=platform.release(),
        arch=platform.machine(),
        terminal=_detect_terminal(),
    )


# ---------------------------------------------------------------------------
# Installation id — UUIDv4 persisted on disk so successive invocations look
# like the same physical client. Stored separately from auth.json so logout
# does not invalidate it.
# ---------------------------------------------------------------------------


def _installation_id_path() -> Path:
    explicit = os.environ.get("CODEX_IMAGE_INSTALLATION_ID_FILE")
    if explicit:
        return Path(explicit).expanduser()
    cache_root = os.environ.get("XDG_CACHE_HOME")
    if cache_root:
        return Path(cache_root).expanduser() / "codex-image" / "installation_id"
    return Path.home() / ".codex-image" / "installation_id"


def get_installation_id() -> str:
    """Return a stable installation UUIDv4, creating it on first use."""

    path = _installation_id_path()
    try:
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass
    except OSError:
        # Disk error reading the file — fall through and try to recreate it.
        pass

    new_id = str(uuid.uuid4())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_id, encoding="utf-8")
    except OSError:
        # Best effort. If the disk is unwritable we still return a UUID for
        # this invocation — the fingerprint then only differs across runs.
        pass
    return new_id


# Session-id is per process, not per disk.
_SESSION_ID = str(uuid.uuid4())


def get_session_id() -> str:
    return _SESSION_ID


# ---------------------------------------------------------------------------
# Session factory.
# ---------------------------------------------------------------------------


def make_session(
    *,
    with_auth_token: str | None = None,
    account_id: str | None = None,
    include_chatgpt_beta: bool = False,
) -> requests.Session:
    """Return a :class:`requests.Session` carrying the codex fingerprint.

    Parameters
    ----------
    with_auth_token:
        Optional bearer token to inject as ``Authorization`` header. The
        OAuth token endpoint must not receive a bearer header, so callers
        for that path pass ``None``.
    account_id:
        Optional ChatGPT account id. When provided, attaches the
        ``chatgpt-account-id`` header expected by
        ``chatgpt.com/backend-api/codex/responses``.
    include_chatgpt_beta:
        When True, attaches ``OpenAI-Beta: responses=experimental`` which
        the ChatGPT-account responses endpoint requires.
    """

    session = requests.Session()

    # Drop requests defaults that codex never sends.
    for header in ("User-Agent", "Accept", "Accept-Encoding"):
        session.headers.pop(header, None)

    session.headers.update(
        {
            "User-Agent": build_user_agent(),
            "originator": ORIGINATOR,
            "session-id": get_session_id(),
            "x-codex-installation-id": get_installation_id(),
        }
    )

    if with_auth_token is not None:
        session.headers["Authorization"] = f"Bearer {with_auth_token}"
    if account_id:
        session.headers["chatgpt-account-id"] = account_id
    if include_chatgpt_beta:
        session.headers["OpenAI-Beta"] = OPENAI_BETA_HEADER_VALUE

    return session
