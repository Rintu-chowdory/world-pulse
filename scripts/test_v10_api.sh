#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../apps/api"
PYTHONPATH=. ENABLE_LIVE_INGESTION=false ENABLE_AI_ENRICHMENT=false uvicorn app.main:app --host 127.0.0.1 --port 8010 >/tmp/world-pulse-v10-api.log 2>&1 &
pid=$!
cleanup() { kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; }
trap cleanup EXIT

for _ in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8010/api/v1/ready >/tmp/world-pulse-v10-ready.json 2>/dev/null; then break; fi
  sleep 0.5
done
curl -fsS http://127.0.0.1:8010/api/v1/health >/tmp/world-pulse-v10-health.json
curl -fsS http://127.0.0.1:8010/metrics >/tmp/world-pulse-v10-metrics.txt
curl -fsS http://127.0.0.1:8010/api/v1/events >/tmp/world-pulse-v10-events.json

grep -q '"status":"ready"' /tmp/world-pulse-v10-ready.json
grep -q 'world_pulse_http_requests_total' /tmp/world-pulse-v10-metrics.txt
grep -q 'Demo Data Source' /tmp/world-pulse-v10-events.json
printf '%s\n' 'V1.0 API smoke test passed'
