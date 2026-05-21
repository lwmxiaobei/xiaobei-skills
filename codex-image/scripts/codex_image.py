"""``codex-image`` command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import auth
import output
import responses_client as rc


# ---------------------------------------------------------------------------
# Exit codes.
# ---------------------------------------------------------------------------


EXIT_OK = 0
EXIT_USER_ERROR = 2
EXIT_FS_ERROR = 3
EXIT_AUTH_ERROR = 4
EXIT_NETWORK_ERROR = 5
EXIT_PARTIAL = 6
EXIT_API_ERROR = 7
EXIT_INTERRUPT = 130


# ---------------------------------------------------------------------------
# Argument parser.
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-image",
        description=(
            "Generate or edit images via OpenAI's Responses API using "
            "ChatGPT-account auth reused from the codex CLI."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser("generate", help="generate a new image")
    _add_common_image_flags(gen)
    gen.add_argument("prompt", help="prompt describing the desired image")

    edit = subparsers.add_parser("edit", help="edit reference image(s)")
    _add_common_image_flags(edit)
    edit.add_argument(
        "--input",
        dest="inputs",
        action="append",
        type=Path,
        required=True,
        help="path to a reference image (repeatable)",
    )
    edit.add_argument("prompt", help="prompt describing the change to apply")

    subparsers.add_parser("login", help="force PKCE OAuth browser flow")
    subparsers.add_parser("logout", help="clear tokens from auth.json")
    subparsers.add_parser("status", help="print current credential metadata")

    return parser


def _add_common_image_flags(sub: argparse.ArgumentParser) -> None:
    sub.add_argument(
        "--output-format",
        choices=("png", "webp", "jpeg"),
        default="png",
    )
    sub.add_argument("--out", type=Path, default=None, help="output path")
    sub.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing file at --out",
    )
    sub.add_argument(
        "--image-model",
        default=None,
        help=(
            "advanced: set tools[0].model. Default unset to match codex "
            "byte-for-byte."
        ),
    )


# ---------------------------------------------------------------------------
# Dispatch.
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "generate":
            return _cmd_generate(args)
        if args.command == "edit":
            return _cmd_edit(args)
        if args.command == "login":
            return _cmd_login()
        if args.command == "logout":
            return _cmd_logout()
        if args.command == "status":
            return _cmd_status()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return EXIT_INTERRUPT

    parser.error(f"unknown command {args.command!r}")
    return EXIT_USER_ERROR


# ---------------------------------------------------------------------------
# Subcommand handlers.
# ---------------------------------------------------------------------------


def _cmd_generate(args: argparse.Namespace) -> int:
    return _run_image_call(
        prompt=args.prompt,
        inputs=None,
        output_format=args.output_format,
        out=args.out,
        force=args.force,
        image_model=args.image_model,
    )


def _cmd_edit(args: argparse.Namespace) -> int:
    inputs: list[Path] = list(args.inputs or [])
    for path in inputs:
        if not path.exists():
            print(f"error: reference image not found: {path}", file=sys.stderr)
            return EXIT_USER_ERROR
    return _run_image_call(
        prompt=args.prompt,
        inputs=inputs,
        output_format=args.output_format,
        out=args.out,
        force=args.force,
        image_model=args.image_model,
    )


def _run_image_call(
    *,
    prompt: str,
    inputs: Iterable[Path] | None,
    output_format: str,
    out: Path | None,
    force: bool,
    image_model: str | None,
) -> int:
    try:
        creds = auth.get_access_credentials()
    except auth.AuthError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return EXIT_AUTH_ERROR

    try:
        result = _call_generate_with_refresh(
            token=creds.access_token,
            account_id=creds.account_id,
            prompt=prompt,
            inputs=inputs,
            output_format=output_format,
            image_model=image_model,
        )
    except rc.UnauthorizedError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return EXIT_AUTH_ERROR
    except rc.ForbiddenError as exc:
        print(f"forbidden: {exc}", file=sys.stderr)
        return EXIT_AUTH_ERROR
    except rc.RateLimitedError as exc:
        print(f"rate limited: {exc}", file=sys.stderr)
        return EXIT_NETWORK_ERROR
    except rc.StreamBrokenError as exc:
        print(f"stream broken: {exc}", file=sys.stderr)
        return EXIT_PARTIAL
    except rc.ApiError as exc:
        print(f"api error: {exc}", file=sys.stderr)
        return EXIT_API_ERROR
    except ValueError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return EXIT_USER_ERROR

    try:
        saved = output.save(
            result.image_b64,
            out,
            force=force,
            slug_source=prompt,
            output_format=output_format,
        )
    except FileNotFoundError as exc:
        print(f"filesystem error: {exc}", file=sys.stderr)
        return EXIT_FS_ERROR
    except (PermissionError, OSError) as exc:
        print(f"filesystem error: {exc}", file=sys.stderr)
        return EXIT_FS_ERROR
    except ValueError as exc:
        print(f"api returned invalid data: {exc}", file=sys.stderr)
        return EXIT_API_ERROR

    print(f"Saved: {saved}")
    if result.revised_prompt:
        print(f"Revised prompt: {result.revised_prompt}")
    return EXIT_OK


def _call_generate_with_refresh(
    *,
    token: str,
    account_id: str | None,
    prompt: str,
    inputs: Iterable[Path] | None,
    output_format: str,
    image_model: str | None,
) -> rc.GenerateResult:
    """Run generate(); on 401 force-refresh once and retry."""

    try:
        return rc.generate(
            prompt,
            access_token=token,
            account_id=account_id,
            input_images=list(inputs) if inputs else None,
            output_format=output_format,
            image_model=image_model,
        )
    except rc.UnauthorizedError:
        refreshed = _force_refresh_credentials()
        return rc.generate(
            prompt,
            access_token=refreshed.access_token,
            account_id=refreshed.account_id,
            input_images=list(inputs) if inputs else None,
            output_format=output_format,
            image_model=image_model,
        )


def _force_refresh_credentials() -> auth.Credentials:
    data = auth._load_auth_json()  # noqa: SLF001 — intentional internal call
    refresh = (data or {}).get("tokens", {}).get("refresh_token") if data else None
    if refresh:
        try:
            return auth.refresh_tokens(refresh, force=True)
        except auth.AuthError:
            pass
    return auth.interactive_login()


def _cmd_login() -> int:
    try:
        creds = auth.interactive_login()
    except auth.AuthError as exc:
        print(f"login failed: {exc}", file=sys.stderr)
        return EXIT_AUTH_ERROR
    print(f"Logged in. Tokens written to {creds.source}.")
    return EXIT_OK


def _cmd_logout() -> int:
    auth.logout()
    print("Logged out (tokens cleared, auth.json shape preserved).")
    return EXIT_OK


def _cmd_status() -> int:
    try:
        info = auth.status()
    except auth.AuthError as exc:
        print(f"status error: {exc}", file=sys.stderr)
        return EXIT_AUTH_ERROR
    print(json.dumps(info, indent=2, sort_keys=True, default=str))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
