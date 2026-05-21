"""Streaming client for the ChatGPT-account ``responses`` endpoint.

Speaks Server-Sent Events, mirrors the codex CLI's request shape exactly,
and extracts the final base64 image from the ``image_generation_call``
output item.

ChatGPT-account tokens (issued by the official ``codex`` CLI's OAuth flow)
can only reach the ``/v1/responses`` surface via
``https://chatgpt.com/backend-api/codex/responses``. The traditional
``api.openai.com/v1/responses`` endpoint rejects them with HTTP 401
``Missing scopes: api.responses.write`` because the token's ``scp`` only
contains ``api.connectors.*``.
"""

from __future__ import annotations

import base64
import io
import json
import mimetypes
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import httpx

from http_client import (
    ORIGINATOR,
    OPENAI_BETA_HEADER_VALUE,
    build_user_agent,
    get_installation_id,
    get_session_id,
)

# ChatGPT-account responses endpoint (codex-rs/model-provider-info/src/lib.rs
# CHATGPT_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex").
RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"
# Default model accepted by Codex-with-ChatGPT-account; gpt-5.4 and gpt-5.2
# pass model gating, others return "model is not supported".
TOP_LEVEL_MODEL = "gpt-5.4"
DEFAULT_INSTRUCTIONS = (
    "You are an image-generation assistant. When the user asks for an image, "
    "immediately call the image_generation tool with the user's full "
    "description as the prompt. Do not ask follow-up questions and do not "
    "emit any text output beyond what the tool returns."
)

MAX_INPUT_BYTES_BEFORE_RESIZE = 5 * 1024 * 1024
MAX_INPUT_BYTES_HARD = 10 * 1024 * 1024
MAX_INPUT_LONG_EDGE = 2048

RETRY_BACKOFF_SECONDS = (2.0, 4.0, 8.0)
# How many times to retry when the SSE stream is cut mid-generation (e.g.,
# Cloudflare / local proxy idle-killing the connection before the image is
# emitted). Each attempt re-POSTs from scratch since ``store=false`` means
# the previous response cannot be resumed by id.
MAX_STREAM_RESTARTS = 3


class ResponsesError(Exception):
    """Base error for the Responses API client."""


class UnauthorizedError(ResponsesError):
    """HTTP 401 — caller should refresh the token and retry once."""


class ForbiddenError(ResponsesError):
    """HTTP 403 — usually a plan/permission issue."""


class RateLimitedError(ResponsesError):
    """HTTP 429 retries exhausted."""


class ApiError(ResponsesError):
    """Other HTTP / business error returned by the backend."""


class StreamBrokenError(ResponsesError):
    """SSE stream ended before ``response.completed``."""


# ---------------------------------------------------------------------------
# Result type.
# ---------------------------------------------------------------------------


@dataclass
class GenerateResult:
    image_b64: str
    revised_prompt: str | None
    call_id: str
    model: str
    raw_events: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Request body builders.
# ---------------------------------------------------------------------------


def _tool_spec(output_format: str, image_model: str | None) -> dict:
    spec: dict[str, Any] = {"type": "image_generation", "output_format": output_format}
    if image_model:
        spec["model"] = image_model
    return spec


def _build_generate_body(
    prompt: str, *, output_format: str, image_model: str | None
) -> dict:
    return {
        "model": TOP_LEVEL_MODEL,
        "store": False,
        "stream": True,
        "instructions": DEFAULT_INSTRUCTIONS,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
        "tools": [_tool_spec(output_format, image_model)],
    }


def _build_edit_body(
    prompt: str,
    input_images: Iterable[Path],
    *,
    output_format: str,
    image_model: str | None,
) -> dict:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    for path in input_images:
        content.append(
            {"type": "input_image", "image_url": _image_to_data_uri(path)}
        )
    return {
        "model": TOP_LEVEL_MODEL,
        "store": False,
        "stream": True,
        "instructions": DEFAULT_INSTRUCTIONS,
        "input": [{"role": "user", "content": content}],
        "tools": [_tool_spec(output_format, image_model)],
    }


def _image_to_data_uri(path: Path) -> str:
    raw = path.read_bytes()
    mime, _ = mimetypes.guess_type(path.name)
    if mime is None or not mime.startswith("image/"):
        mime = "image/png"

    if len(raw) > MAX_INPUT_BYTES_BEFORE_RESIZE:
        raw, mime = _downscale(raw, mime)

    if len(raw) > MAX_INPUT_BYTES_HARD:
        raise ValueError(
            f"reference image {path} is {len(raw)} bytes after downscaling, "
            f"exceeds hard limit of {MAX_INPUT_BYTES_HARD} bytes"
        )

    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _downscale(raw: bytes, mime: str) -> tuple[bytes, str]:
    from PIL import Image  # imported lazily so tests without Pillow still work

    img = Image.open(io.BytesIO(raw))
    img.load()
    longest = max(img.size)
    if longest <= MAX_INPUT_LONG_EDGE:
        return raw, mime

    scale = MAX_INPUT_LONG_EDGE / float(longest)
    new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
    img = img.resize(new_size, Image.LANCZOS)

    buf = io.BytesIO()
    fmt = "PNG" if mime == "image/png" else "JPEG"
    if fmt == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(buf, format=fmt)
    new_mime = "image/png" if fmt == "PNG" else "image/jpeg"
    return buf.getvalue(), new_mime


# ---------------------------------------------------------------------------
# Public entrypoints.
# ---------------------------------------------------------------------------


def generate(
    prompt: str,
    *,
    access_token: str,
    account_id: str | None,
    input_images: Iterable[Path] | None = None,
    output_format: str = "png",
    image_model: str | None = None,
) -> GenerateResult:
    """Call the ChatGPT-account ``responses`` endpoint and return the image.

    Parameters
    ----------
    prompt:
        Natural-language description of the image to generate, or — when
        editing — the change to apply to the reference image(s).
    access_token:
        Bearer token resolved by :mod:`auth`.
    account_id:
        ChatGPT account id (``tokens.account_id`` in ``auth.json``). The
        endpoint requires it as the ``chatgpt-account-id`` header; missing
        or stale ids surface as HTTP 401.
    input_images:
        Optional iterable of reference image paths. When non-empty the call
        is treated as an *edit*.
    output_format:
        ``png`` / ``webp`` / ``jpeg``.
    image_model:
        Advanced override of the ``image_generation`` tool's ``model``
        field. ``None`` (default) lets the server pick.
    """

    if input_images:
        body = _build_edit_body(
            prompt,
            list(input_images),
            output_format=output_format,
            image_model=image_model,
        )
    else:
        body = _build_generate_body(
            prompt, output_format=output_format, image_model=image_model
        )

    headers = _build_headers(access_token, account_id)
    return _stream_with_restarts(body, headers)


def _build_headers(access_token: str, account_id: str | None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": build_user_agent(),
        "originator": ORIGINATOR,
        "session-id": get_session_id(),
        "x-codex-installation-id": get_installation_id(),
        "OpenAI-Beta": OPENAI_BETA_HEADER_VALUE,
    }
    if account_id:
        headers["chatgpt-account-id"] = account_id
    return headers


def _stream_with_restarts(body: dict, headers: dict[str, str]) -> GenerateResult:
    """POST + consume SSE, restarting from scratch when the stream is cut.

    ``store=false`` means a broken stream cannot be resumed by response id,
    so the only recovery is to re-POST. We do this up to
    ``MAX_STREAM_RESTARTS`` times before giving up.
    """

    timeout = httpx.Timeout(connect=30.0, read=900.0, write=60.0, pool=30.0)
    last_partial_error: Exception | None = None

    with httpx.Client(
        http2=True,
        timeout=timeout,
        trust_env=True,
        follow_redirects=False,
    ) as client:
        for restart in range(MAX_STREAM_RESTARTS + 1):
            try:
                return _post_once(client, body, headers)
            except StreamBrokenError as exc:
                last_partial_error = exc
                if restart >= MAX_STREAM_RESTARTS:
                    raise
                delay = RETRY_BACKOFF_SECONDS[
                    min(restart, len(RETRY_BACKOFF_SECONDS) - 1)
                ]
                time.sleep(delay)
                continue

    # Loop only exits via return or raise; this is defensive.
    raise ApiError(f"stream restarts exhausted: {last_partial_error}")


def _post_once(
    client: httpx.Client, body: dict, headers: dict[str, str]
) -> GenerateResult:
    """Single POST attempt with HTTP-status retries (excluding mid-stream cuts)."""

    last_error: Exception | None = None
    for attempt in range(len(RETRY_BACKOFF_SECONDS) + 1):
        try:
            with client.stream(
                "POST", RESPONSES_URL, json=body, headers=headers
            ) as response:
                status = response.status_code

                if status == 200:
                    return _consume_sse(response)

                if status == 401:
                    raise UnauthorizedError(
                        f"access token rejected: {_safe_read(response)}"
                    )
                if status == 403:
                    raise ForbiddenError(f"forbidden: {_safe_read(response)}")

                if status == 429:
                    if attempt >= len(RETRY_BACKOFF_SECONDS):
                        raise RateLimitedError("rate-limit retries exhausted")
                    delay = _retry_after(response, attempt)
                    time.sleep(delay)
                    continue

                if 500 <= status < 600:
                    text = _safe_read(response)
                    if attempt >= len(RETRY_BACKOFF_SECONDS):
                        raise ApiError(f"server error {status}: {text}")
                    time.sleep(RETRY_BACKOFF_SECONDS[attempt])
                    continue

                raise ApiError(f"unexpected status {status}: {_safe_read(response)}")

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
            last_error = exc
            if attempt < len(RETRY_BACKOFF_SECONDS):
                time.sleep(RETRY_BACKOFF_SECONDS[attempt])
                continue
            raise ApiError(f"network error: {exc}") from exc

    raise ApiError(f"retries exhausted: {last_error}")


def _retry_after(response: httpx.Response, attempt: int) -> float:
    raw = response.headers.get("Retry-After")
    if not raw:
        return RETRY_BACKOFF_SECONDS[attempt]
    try:
        return float(raw)
    except ValueError:
        return RETRY_BACKOFF_SECONDS[attempt]


def _safe_read(response: httpx.Response) -> str:
    try:
        return response.read().decode("utf-8", errors="replace")[:500]
    except Exception:  # noqa: BLE001
        return "<unreadable body>"


# ---------------------------------------------------------------------------
# SSE consumer.
# ---------------------------------------------------------------------------


def _iter_sse_events(response: httpx.Response) -> Iterable[dict]:
    """Yield decoded JSON payloads from an SSE response.

    Re-raises transport-level errors as :class:`StreamBrokenError` so the
    caller can decide whether to restart the request.
    """

    event_name: str | None = None
    data_chunks: list[str] = []

    line_source = response.iter_lines()
    while True:
        try:
            line = next(line_source)
        except StopIteration:
            break
        except (
            httpx.RemoteProtocolError,
            httpx.ReadError,
            httpx.ReadTimeout,
            httpx.ProtocolError,
        ) as exc:
            raise StreamBrokenError(f"transport error mid-stream: {exc}") from exc

        if line is None:
            continue
        if line == "":
            if data_chunks:
                raw = "\n".join(data_chunks)
                data_chunks.clear()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    payload = {"_raw": raw}
                if event_name and "type" not in payload:
                    payload["type"] = event_name
                event_name = None
                yield payload
            else:
                event_name = None
            continue
        if line.startswith(":"):
            # Comment / keepalive — ignore but the heartbeat keeps the
            # HTTP/2 stream open.
            continue
        if line.startswith("event:"):
            event_name = line[len("event:") :].strip()
            continue
        if line.startswith("data:"):
            data_chunks.append(line[len("data:") :].lstrip())
            continue


def _consume_sse(response: httpx.Response) -> GenerateResult:
    raw_events: list[dict] = []
    final_image: str | None = None
    revised_prompt: str | None = None
    call_id: str | None = None
    failure: dict | None = None

    for event in _iter_sse_events(response):
        raw_events.append(event)
        etype = event.get("type")

        if etype == "response.output_item.done":
            item = event.get("item") or {}
            if item.get("type") == "image_generation_call":
                final_image = item.get("result") or final_image
                revised_prompt = item.get("revised_prompt") or revised_prompt
                call_id = item.get("id") or call_id

        elif etype == "response.completed":
            response_obj = event.get("response") or {}
            for item in response_obj.get("output") or []:
                if item.get("type") == "image_generation_call":
                    final_image = item.get("result") or final_image
                    revised_prompt = item.get("revised_prompt") or revised_prompt
                    call_id = item.get("id") or call_id

        elif etype == "response.failed":
            failure = event.get("response") or event

        elif etype == "error":
            failure = event

    if failure:
        raise ApiError(f"response failed: {failure}")

    if not final_image:
        raise StreamBrokenError("stream ended without producing an image")

    return GenerateResult(
        image_b64=final_image,
        revised_prompt=revised_prompt,
        call_id=call_id or "",
        model=TOP_LEVEL_MODEL,
        raw_events=raw_events,
    )
