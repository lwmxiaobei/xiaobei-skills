"""Unit tests for :mod:`responses_client`."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Iterable

import pytest
import responses

import http_client
import responses_client as rc


# ---------------------------------------------------------------------------
# Helpers — build an SSE response body.
# ---------------------------------------------------------------------------


def _sse(events: Iterable[tuple[str, dict]]) -> str:
    lines: list[str] = []
    for event_name, payload in events:
        lines.append(f"event: {event_name}")
        lines.append("data: " + json.dumps(payload))
        lines.append("")  # blank line terminates an event
    return "\n".join(lines) + "\n"


def _image_b64() -> str:
    # Minimal valid base64.
    return base64.b64encode(b"\x89PNG\r\n\x1a\n-fake").decode("ascii")


# ---------------------------------------------------------------------------
# Request body shape.
# ---------------------------------------------------------------------------


def test_build_generate_body_matches_codex_default() -> None:
    body = rc._build_generate_body(
        "hello", output_format="png", image_model=None
    )
    assert body == {
        "model": "gpt-5.5",
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": "hello"}],
            }
        ],
        "tools": [{"type": "image_generation", "output_format": "png"}],
        "stream": True,
    }
    # Critical: tools[0] must NOT contain a "model" key by default.
    assert "model" not in body["tools"][0]


def test_build_generate_body_includes_image_model_when_explicit() -> None:
    body = rc._build_generate_body(
        "hi", output_format="png", image_model="gpt-image-2"
    )
    assert body["tools"][0]["model"] == "gpt-image-2"


# ---------------------------------------------------------------------------
# SSE consumption.
# ---------------------------------------------------------------------------


@responses.activate
def test_generate_extracts_image_from_output_item_done() -> None:
    img_b64 = _image_b64()
    body = _sse(
        [
            (
                "response.output_item.done",
                {
                    "item": {
                        "id": "ig_1",
                        "type": "image_generation_call",
                        "result": img_b64,
                        "revised_prompt": "a refined prompt",
                    }
                },
            ),
            ("response.completed", {"response": {"output": []}}),
        ]
    )
    responses.add(
        responses.POST,
        rc.RESPONSES_URL,
        body=body,
        status=200,
        content_type="text/event-stream",
    )

    result = rc.generate("a panda", access_token="tok")
    assert result.image_b64 == img_b64
    assert result.revised_prompt == "a refined prompt"
    assert result.call_id == "ig_1"


@responses.activate
def test_generate_extracts_image_from_response_completed() -> None:
    img_b64 = _image_b64()
    body = _sse(
        [
            (
                "response.completed",
                {
                    "response": {
                        "output": [
                            {
                                "id": "ig_42",
                                "type": "image_generation_call",
                                "result": img_b64,
                            }
                        ]
                    }
                },
            )
        ]
    )
    responses.add(
        responses.POST,
        rc.RESPONSES_URL,
        body=body,
        status=200,
        content_type="text/event-stream",
    )
    result = rc.generate("x", access_token="tok")
    assert result.image_b64 == img_b64
    assert result.call_id == "ig_42"


@responses.activate
def test_generate_raises_on_response_failed() -> None:
    body = _sse(
        [("response.failed", {"response": {"error": {"message": "boom"}}})]
    )
    responses.add(
        responses.POST,
        rc.RESPONSES_URL,
        body=body,
        status=200,
        content_type="text/event-stream",
    )
    with pytest.raises(rc.ApiError):
        rc.generate("p", access_token="tok")


@responses.activate
def test_generate_raises_stream_broken_when_no_image() -> None:
    body = _sse([("response.completed", {"response": {"output": []}})])
    responses.add(
        responses.POST,
        rc.RESPONSES_URL,
        body=body,
        status=200,
        content_type="text/event-stream",
    )
    with pytest.raises(rc.StreamBrokenError):
        rc.generate("p", access_token="tok")


# ---------------------------------------------------------------------------
# HTTP status handling.
# ---------------------------------------------------------------------------


@responses.activate
def test_401_raises_unauthorized() -> None:
    responses.add(
        responses.POST,
        rc.RESPONSES_URL,
        json={"error": "invalid_token"},
        status=401,
    )
    with pytest.raises(rc.UnauthorizedError):
        rc.generate("p", access_token="tok")


@responses.activate
def test_403_raises_forbidden() -> None:
    responses.add(
        responses.POST,
        rc.RESPONSES_URL,
        json={"error": "plan"},
        status=403,
    )
    with pytest.raises(rc.ForbiddenError):
        rc.generate("p", access_token="tok")


@responses.activate
def test_500_then_success_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rc.time, "sleep", lambda *_a, **_kw: None)
    img_b64 = _image_b64()
    responses.add(
        responses.POST, rc.RESPONSES_URL, body="boom", status=500
    )
    responses.add(
        responses.POST,
        rc.RESPONSES_URL,
        body=_sse(
            [
                (
                    "response.output_item.done",
                    {
                        "item": {
                            "id": "ig_2",
                            "type": "image_generation_call",
                            "result": img_b64,
                        }
                    },
                )
            ]
        ),
        status=200,
        content_type="text/event-stream",
    )
    result = rc.generate("p", access_token="tok")
    assert result.image_b64 == img_b64
    assert len(responses.calls) == 2


@responses.activate
def test_500_persistent_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rc.time, "sleep", lambda *_a, **_kw: None)
    for _ in range(4):
        responses.add(
            responses.POST, rc.RESPONSES_URL, body="boom", status=500
        )
    with pytest.raises(rc.ApiError):
        rc.generate("p", access_token="tok")


@responses.activate
def test_429_persistent_raises_rate_limited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rc.time, "sleep", lambda *_a, **_kw: None)
    for _ in range(4):
        responses.add(
            responses.POST,
            rc.RESPONSES_URL,
            json={"error": "rate"},
            status=429,
        )
    with pytest.raises(rc.RateLimitedError):
        rc.generate("p", access_token="tok")


# ---------------------------------------------------------------------------
# Fingerprint headers.
# ---------------------------------------------------------------------------


@responses.activate
def test_request_carries_fingerprint_headers() -> None:
    img_b64 = _image_b64()
    responses.add(
        responses.POST,
        rc.RESPONSES_URL,
        body=_sse(
            [
                (
                    "response.output_item.done",
                    {
                        "item": {
                            "id": "ig_x",
                            "type": "image_generation_call",
                            "result": img_b64,
                        }
                    },
                )
            ]
        ),
        status=200,
        content_type="text/event-stream",
    )
    rc.generate("p", access_token="THE_TOKEN")

    request = responses.calls[0].request
    assert request.headers["Authorization"] == "Bearer THE_TOKEN"
    assert request.headers["originator"] == "codex_cli_rs"
    assert request.headers["Accept"] == "text/event-stream"
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["User-Agent"].startswith("codex_cli_rs/")
    assert "session-id" in request.headers
    assert "x-codex-installation-id" in request.headers
    # Forbidden headers must NOT be present.
    forbidden = [
        "x-codex-turn-state",
        "x-codex-turn-metadata",
        "x-openai-subagent",
        "x-openai-memgen-request",
        "x-responsesapi-include-timing-metrics",
        "thread-id",
        "x-client-request-id",
        "x-openai-internal-codex-residency",
    ]
    for header in forbidden:
        assert header not in request.headers


# ---------------------------------------------------------------------------
# Edit body.
# ---------------------------------------------------------------------------


def test_edit_body_embeds_data_uri(tmp_path: Path) -> None:
    img = tmp_path / "ref.png"
    img.write_bytes(b"hello-png")

    body = rc._build_edit_body(
        "make blue", [img], output_format="png", image_model=None
    )
    content = body["input"][0]["content"]
    assert content[0] == {"type": "input_text", "text": "make blue"}
    assert content[1]["type"] == "input_image"
    assert content[1]["image_url"].startswith("data:image/png;base64,")


# ---------------------------------------------------------------------------
# Header sanity — User-Agent template.
# ---------------------------------------------------------------------------


def test_user_agent_template_uses_codex_pretend_version() -> None:
    ua = http_client.build_user_agent()
    assert ua.startswith(f"codex_cli_rs/{http_client.CODEX_PRETEND_VERSION}")
