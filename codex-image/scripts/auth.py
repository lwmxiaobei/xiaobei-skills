"""Authentication layer.

Resolves a ChatGPT access token, with three strategies in order:

1. Read ``$CODEX_HOME/auth.json``.
2. If close to expiry, ``refresh_tokens()``.
3. If still no luck, ``interactive_login()`` via a PKCE OAuth browser flow.

The on-disk file format matches the official ``codex`` CLI so the two
clients share credentials transparently.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import socket
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt as pyjwt
import requests

from http_client import OAUTH_CLIENT_ID, OAUTH_SCOPE, ORIGINATOR, make_session

# ---------------------------------------------------------------------------
# Constants.
# ---------------------------------------------------------------------------

AUTH_HOST = "https://auth.openai.com"
AUTHORIZE_URL = f"{AUTH_HOST}/oauth/authorize"
TOKEN_URL = f"{AUTH_HOST}/oauth/token"

REDIRECT_PORTS = (1455, 1457)
REDIRECT_PATH = "/auth/callback"

REFRESH_LEEWAY_SECONDS = 5 * 60  # refresh when access token has <5min left
OAUTH_TIMEOUT_SECONDS = 90

UNRECOVERABLE_REFRESH_ERRORS = {
    "refresh_token_expired",
    "refresh_token_reused",
    "refresh_token_invalidated",
    "invalid_grant",
}


# ---------------------------------------------------------------------------
# Data types.
# ---------------------------------------------------------------------------


@dataclass
class Credentials:
    access_token: str
    refresh_token: str | None
    id_token: str | None
    account_id: str | None
    last_refresh: str
    source: Path
    extra: dict[str, Any] = field(default_factory=dict)


class AuthError(RuntimeError):
    """Raised when no usable credential can be obtained."""


# ---------------------------------------------------------------------------
# auth.json paths.
# ---------------------------------------------------------------------------


def codex_home() -> Path:
    explicit = os.environ.get("CODEX_HOME")
    if explicit:
        return Path(explicit).expanduser()
    return Path.home() / ".codex"


def auth_path() -> Path:
    return codex_home() / "auth.json"


# ---------------------------------------------------------------------------
# Low-level helpers.
# ---------------------------------------------------------------------------


def _load_auth_json() -> dict | None:
    path = auth_path()
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise AuthError(f"failed to read {path}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        # Don't silently overwrite; back up the bad file so user can inspect.
        backup = path.with_suffix(path.suffix + f".broken-{int(time.time())}")
        try:
            path.rename(backup)
        except OSError:
            pass
        raise AuthError(
            f"{path} contained invalid JSON, backed up to {backup}: {exc}"
        ) from exc


def _write_auth_json(data: dict) -> None:
    path = auth_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _decode_jwt_exp(token: str) -> int | None:
    """Return the ``exp`` claim of *token*, or ``None`` if not a JWT."""

    try:
        claims = pyjwt.decode(token, options={"verify_signature": False})
    except pyjwt.PyJWTError:
        return None
    exp = claims.get("exp")
    return int(exp) if isinstance(exp, (int, float)) else None


def _now() -> int:
    return int(time.time())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _credentials_from_data(data: dict) -> Credentials | None:
    tokens = data.get("tokens")
    if not tokens or not isinstance(tokens, dict):
        return None
    access = tokens.get("access_token")
    if not access:
        return None
    return Credentials(
        access_token=access,
        refresh_token=tokens.get("refresh_token"),
        id_token=tokens.get("id_token"),
        account_id=tokens.get("account_id"),
        last_refresh=data.get("last_refresh") or _now_iso(),
        source=auth_path(),
        extra={k: v for k, v in data.items() if k not in {"tokens", "last_refresh"}},
    )


def _data_from_credentials(creds: Credentials) -> dict:
    data: dict = {"auth_mode": "Chatgpt"}
    data.update(creds.extra)
    data["tokens"] = {
        "id_token": creds.id_token,
        "access_token": creds.access_token,
        "refresh_token": creds.refresh_token,
        "account_id": creds.account_id,
    }
    data["last_refresh"] = creds.last_refresh
    return data


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------


def get_access_token() -> str:
    """Return a usable access token, refreshing or logging in as needed."""

    return get_access_credentials().access_token


def get_access_credentials() -> Credentials:
    """Return usable credentials including ``account_id``.

    Callers that need to attach ``chatgpt-account-id`` to outgoing requests
    (e.g. the ChatGPT-account ``responses`` endpoint) should prefer this
    helper over :func:`get_access_token` so the id stays in sync with the
    token that was actually selected/refreshed.
    """

    return _resolve_credentials()


def _resolve_credentials() -> Credentials:
    try:
        data = _load_auth_json()
    except AuthError:
        # Corrupted file already backed up — go straight to OAuth.
        return interactive_login()

    creds = _credentials_from_data(data) if data else None
    if creds is None:
        return interactive_login()

    exp = _decode_jwt_exp(creds.access_token)
    if exp is not None and exp - _now() > REFRESH_LEEWAY_SECONDS:
        return creds

    if creds.refresh_token:
        try:
            return refresh_tokens(creds.refresh_token, force=False)
        except AuthError:
            return interactive_login()

    return interactive_login()


def refresh_tokens(refresh_token: str, *, force: bool = False) -> Credentials:
    """Exchange *refresh_token* for a fresh access token.

    Parameters
    ----------
    force:
        If True, perform the refresh even when the current token still has
        plenty of validity. Used by the CLI's 401 recovery path.
    """

    payload = {
        "client_id": OAUTH_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    session = make_session()
    last_error: str | None = None
    for attempt in range(3):
        try:
            response = session.post(TOKEN_URL, json=payload, timeout=30)
        except requests.RequestException as exc:
            last_error = str(exc)
            time.sleep(2 ** (attempt + 1))
            continue

        if response.status_code == 200:
            return _store_refreshed_tokens(response.json(), refresh_token)

        # Hard failures — never retry, propagate.
        if response.status_code in (400, 401, 403):
            body: dict[str, Any] = {}
            try:
                body = response.json()
            except ValueError:
                pass
            error_raw = body.get("error") or ""
            error_code = error_raw if isinstance(error_raw, str) else error_raw.get("code", "")
            if error_code in UNRECOVERABLE_REFRESH_ERRORS:
                _clear_tokens_field()
            raise AuthError(
                f"refresh failed ({response.status_code}): {body or response.text!r}"
            )

        # 5xx — back off and retry.
        last_error = f"HTTP {response.status_code}: {response.text!r}"
        time.sleep(2 ** (attempt + 1))

    if force:
        raise AuthError(f"refresh failed after retries: {last_error}")
    raise AuthError(f"refresh failed after retries: {last_error}")


def _store_refreshed_tokens(payload: dict, prior_refresh: str) -> Credentials:
    existing = _load_auth_json() or {}
    extra = {k: v for k, v in existing.items() if k not in {"tokens", "last_refresh"}}
    tokens = existing.get("tokens") or {}

    access = payload.get("access_token") or tokens.get("access_token")
    if not access:
        raise AuthError(f"refresh response missing access_token: {payload!r}")
    refresh = payload.get("refresh_token") or prior_refresh
    id_token = payload.get("id_token") or tokens.get("id_token")
    account_id = payload.get("account_id") or tokens.get("account_id")

    creds = Credentials(
        access_token=access,
        refresh_token=refresh,
        id_token=id_token,
        account_id=account_id,
        last_refresh=_now_iso(),
        source=auth_path(),
        extra=extra if extra else {"auth_mode": "Chatgpt"},
    )
    _write_auth_json(_data_from_credentials(creds))
    return creds


def _clear_tokens_field() -> None:
    """Remove the ``tokens`` field from auth.json without deleting the file."""

    try:
        data = _load_auth_json()
    except AuthError:
        return
    if not data:
        return
    data.pop("tokens", None)
    data["auth_mode"] = data.get("auth_mode", "Chatgpt")
    data.setdefault("last_refresh", _now_iso())
    try:
        _write_auth_json(data)
    except OSError:
        pass


def logout() -> None:
    """Strip tokens from auth.json. File shape and other fields are kept."""

    _clear_tokens_field()


def status() -> dict:
    """Return a non-secret summary of the current credential, or raise."""

    data = _load_auth_json()
    if not data:
        raise AuthError("no credential found")
    creds = _credentials_from_data(data)
    if not creds:
        raise AuthError("auth.json present but no tokens stored")

    info: dict[str, Any] = {
        "source": str(creds.source),
        "account_id": creds.account_id,
        "last_refresh": creds.last_refresh,
    }
    exp = _decode_jwt_exp(creds.access_token)
    if exp is not None:
        info["expires_at"] = datetime.fromtimestamp(exp, timezone.utc).isoformat(
            timespec="seconds"
        )

    if creds.id_token:
        try:
            claims = pyjwt.decode(creds.id_token, options={"verify_signature": False})
        except pyjwt.PyJWTError:
            claims = {}
        info["email"] = claims.get("email")
        ns = claims.get("https://api.openai.com/auth") or {}
        if isinstance(ns, dict):
            info["plan"] = ns.get("chatgpt_plan_type") or ns.get("plan_type")

    return info


# ---------------------------------------------------------------------------
# PKCE OAuth flow.
# ---------------------------------------------------------------------------


def _make_pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(43)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _make_state() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    server_version = "codex-image-callback/1.0"

    def do_GET(self) -> None:  # noqa: N802 — required name
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != REDIRECT_PATH:
            self.send_response(404)
            self.end_headers()
            return
        query = urllib.parse.parse_qs(parsed.query)
        result: dict[str, str | None] = {
            "code": (query.get("code") or [None])[0],
            "state": (query.get("state") or [None])[0],
            "error": (query.get("error") or [None])[0],
            "error_description": (query.get("error_description") or [None])[0],
        }
        # Stash on the server instance so the main thread can pick it up.
        self.server.oauth_result = result  # type: ignore[attr-defined]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if result["error"]:
            body = f"<h1>Login failed</h1><p>{result['error']}</p>"
        else:
            body = "<h1>codex-image login complete</h1><p>You can close this tab.</p>"
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, *_args, **_kwargs) -> None:  # noqa: D401
        # Silence the default stderr logger.
        return


def _bind_callback_server() -> tuple[http.server.HTTPServer, int]:
    last_exc: OSError | None = None
    for port in REDIRECT_PORTS:
        try:
            server = http.server.HTTPServer(("127.0.0.1", port), _CallbackHandler)
        except OSError as exc:
            last_exc = exc
            continue
        server.oauth_result = None  # type: ignore[attr-defined]
        return server, port
    raise AuthError(
        f"could not bind any of {REDIRECT_PORTS!r} for OAuth callback: {last_exc}"
    )


def interactive_login() -> Credentials:
    """Drive the PKCE OAuth flow end-to-end and persist the result."""

    verifier, challenge = _make_pkce_pair()
    state = _make_state()
    server, port = _bind_callback_server()
    redirect_uri = f"http://localhost:{port}{REDIRECT_PATH}"

    params = {
        "response_type": "code",
        "client_id": OAUTH_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": OAUTH_SCOPE,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "id_token_add_organizations": "true",
        "codex_cli_simplified_flow": "true",
        "originator": ORIGINATOR,
    }
    url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print(f"Opening browser for OAuth login...\nIf nothing opens, visit:\n{url}")
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001 — best effort
        pass

    deadline = time.monotonic() + OAUTH_TIMEOUT_SECONDS
    try:
        while time.monotonic() < deadline:
            result = getattr(server, "oauth_result", None)
            if result is not None:
                break
            time.sleep(0.2)
        else:
            raise AuthError("OAuth login timed out waiting for callback")
    finally:
        server.shutdown()
        server.server_close()

    if result["error"]:
        raise AuthError(
            f"OAuth error: {result['error']} {result.get('error_description') or ''}"
        )
    if result["state"] != state:
        raise AuthError("OAuth state mismatch — possible CSRF, aborting")
    if not result["code"]:
        raise AuthError("OAuth callback missing code parameter")

    token_payload = {
        "client_id": OAUTH_CLIENT_ID,
        "grant_type": "authorization_code",
        "code": result["code"],
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }
    session = make_session()
    response = session.post(TOKEN_URL, json=token_payload, timeout=30)
    if response.status_code != 200:
        raise AuthError(
            f"token exchange failed ({response.status_code}): {response.text!r}"
        )
    payload = response.json()

    access = payload.get("access_token")
    if not access:
        raise AuthError(f"token response missing access_token: {payload!r}")

    creds = Credentials(
        access_token=access,
        refresh_token=payload.get("refresh_token"),
        id_token=payload.get("id_token"),
        account_id=payload.get("account_id"),
        last_refresh=_now_iso(),
        source=auth_path(),
        extra={"auth_mode": "Chatgpt"},
    )
    _write_auth_json(_data_from_credentials(creds))
    return creds


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0
