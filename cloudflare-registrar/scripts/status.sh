#!/usr/bin/env bash
# Poll the registration workflow status for a domain.
# Usage: status.sh <domain>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <domain>" >&2
  exit 2
fi

DOMAIN="$1"
case "$DOMAIN" in
  */*|*[\"\\\ ]*|"")
    echo "Error: invalid domain '$DOMAIN'" >&2
    exit 2
    ;;
esac

cf_curl GET "/registrations/${DOMAIN}/registration-status"
