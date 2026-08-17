#!/usr/bin/env bash
set -euo pipefail

API_URL="${WORLD_PULSE_API_URL:?WORLD_PULSE_API_URL is required}"
WEB_URL="${WORLD_PULSE_WEB_URL:?WORLD_PULSE_WEB_URL is required}"

check() {
  local label="$1"
  local url="$2"
  if ! curl --fail --silent --show-error --max-time 10 "$url" >/dev/null; then
    echo "FAIL ${label} ${url}" >&2
    return 1
  fi
  echo "PASS ${label} ${url}"
}

check "api-ready" "${API_URL%/}/api/v1/ready"
check "api-health" "${API_URL%/}/api/v1/health"
check "api-events" "${API_URL%/}/api/v1/events"
check "api-metrics" "${API_URL%/}/metrics"
check "web-home" "${WEB_URL%/}/"
