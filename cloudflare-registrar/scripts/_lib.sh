#!/usr/bin/env bash
# Shared helpers. Source this from each script.
set -euo pipefail

: "${ACCOUNT_ID:?ACCOUNT_ID env var is required. Export it before running.}"
: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN env var is required. Export it before running.}"

CF_BASE="https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/registrar"
CF_AUTH_HEADER="Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"

cf_curl() {
  # Usage: cf_curl <method> <path> [curl args...]
  local method="$1" path="$2"
  shift 2
  curl --fail-with-body --silent --show-error \
    --request "$method" \
    --url "${CF_BASE}${path}" \
    --header "$CF_AUTH_HEADER" \
    "$@"
}
