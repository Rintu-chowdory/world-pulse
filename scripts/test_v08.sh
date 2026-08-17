#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../apps/api"
PYTHONPATH=. ENABLE_LIVE_INGESTION=false ENABLE_AI_ENRICHMENT=false uvicorn app.main:app --host 127.0.0.1 --port 8004 >/tmp/world-pulse-v08-api.log 2>&1 &
pid=$!
cleanup() { kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8004/api/v1/health >/tmp/world-pulse-health.json 2>/dev/null; then break; fi
  sleep 0.5
done
printf '%s\n' '--- health ---'
cat /tmp/world-pulse-health.json
printf '\n%s\n' '--- ai enrich ---'
curl -fsS -X POST http://127.0.0.1:8004/api/v1/ai/enrich \
  -H 'Content-Type: application/json' \
  -d '{"event":{"id":"test:1","category":"earthquake","severity":"warning","title":"Earthquake M5.6","location":"Test Region","lat":1.0,"lon":2.0,"magnitude":5.6,"timestamp":"2026-08-17T20:00:00Z","source":"Test Source","metadata":{}}}'
printf '\n%s\n' '--- stats ---'
curl -fsS http://127.0.0.1:8004/api/v1/stats
printf '\n%s\n' '--- log ---'
tail -n 12 /tmp/world-pulse-v08-api.log
