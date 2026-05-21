#!/usr/bin/env bash
# Register a domain. BILLABLE and NON-REFUNDABLE once it succeeds.
# Usage: register.sh <domain> [--async]
#
# --async adds the "Prefer: respond-async" header so the API returns immediately
# with 202 instead of waiting ~10s. Use when you prefer to poll status.sh yourself.
#
# This script intentionally uses account defaults:
#   - default registrant contact
#   - default payment method
#   - auto_renew: false
#   - privacy_mode: registry default
# If you need to override any of those, call the Registrar API directly with curl.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <domain> [--async]" >&2
  exit 2
fi

DOMAIN="$1"
shift

case "$DOMAIN" in
  *[\"\\]*|"")
    echo "Error: invalid domain '$DOMAIN'" >&2
    exit 2
    ;;
esac

ASYNC=0
for arg in "$@"; do
  case "$arg" in
    --async) ASYNC=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

HEADERS=(--header "Content-Type: application/json")
if (( ASYNC )); then
  HEADERS+=(--header "Prefer: respond-async")
fi

payload="{\"domain_name\":\"${DOMAIN}\"}"

cf_curl POST "/registrations" \
  "${HEADERS[@]}" \
  --data "$payload"
