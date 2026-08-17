# World Pulse

World Pulse is a global event intelligence platform for seeing what is happening around the world with less noise and more context. The project combines a dark geospatial command center, live event filtering, ranked signal summaries, and Pulse AI decision support.

## Current release: V1.0 — production delivery and observability foundation

The upgraded experience includes a professional situation-room layout, responsive dark visual system, live world map framing, signal priority panel, metric strip, improved event exploration, an AI assistant with guided questions, real USGS earthquake ingestion, optional NASA FIRMS fire ingestion, normalized event contracts, a lifecycle-managed ingestion supervisor, WebSocket delivery, optional PostGIS persistence, Redis pub/sub fan-out, a V0.8 OpenAI-backed summarization/classification worker, V1.0 CI/CD automation, readiness probes, structured logs, and Prometheus-compatible metrics. The AI endpoints use deterministic fallbacks when no model credentials are configured, so the interface remains useful in every environment.

| Layer | Location | Responsibility |
| --- | --- | --- |
| Web | `apps/web` | Next.js interface, MapLibre map, filters, live feed, Pulse AI panel |
| API | `apps/api` | FastAPI routes, ingestion adapters, AI enrichment workers, PostGIS repository, Redis event bus, WebSocket hub |
| Local services | `docker-compose.yml` | Web, API, PostGIS, and Redis development services |

## Run locally without Docker

Start the API:

```bash
cd apps/api
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn app.main:app --reload --port 8000
```

In a second terminal, start the web application:

```bash
cd apps/web
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The frontend reads `NEXT_PUBLIC_API_BASE` and defaults to `http://127.0.0.1:8000`.

## Pulse AI configuration

The backend supports any OpenAI-compatible chat completion endpoint. To enable model-backed answers on Render, configure these environment variables on the API service:

```text
OPENAI_API_KEY=your-server-side-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-5-mini
ENABLE_AI_ENRICHMENT=true
AI_WORKERS=2
ALLOWED_ORIGINS=https://your-cloudflare-domain.example
DATABASE_URL=postgresql://user:password@host:5432/worldpulse
REDIS_URL=redis://:password@host:6379/0
DB_POOL_MAX=10
```

`OPENAI_API_KEY` is read only by FastAPI and is never sent to the browser. If it is absent or the provider is unavailable, `/api/v1/ask` uses the local event-aware fallback response and `/api/v1/ai/enrich` uses deterministic event classification. The background V0.8 worker is opt-in through `ENABLE_AI_ENRICHMENT=true`; keep it disabled while calibrating cost, latency, and evaluation thresholds.

On Cloudflare, set `NEXT_PUBLIC_API_BASE` to the public Render URL for the API, for example:

```text
NEXT_PUBLIC_API_BASE=https://your-render-api.example.com
```

After changing a Cloudflare Pages environment variable, trigger a new frontend deployment. After changing Render environment variables, redeploy the API service.

## API routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Liveness and dependency status |
| `GET` | `/api/v1/ready` | Deployment readiness probe; optionally enforces PostGIS and Redis |
| `GET` | `/metrics` | Prometheus-compatible request, ingestion, AI, and runtime metrics |
| `GET` | `/api/v1/events` | Event list with `category`, `severity`, and `q` filters |
| `GET` | `/api/v1/events/{event_id}` | Single event lookup |
| `GET` | `/api/v1/stats` | Current totals by category |
| `POST` | `/api/v1/ask` | Ask Pulse AI about a supplied event view |
| `POST` | `/api/v1/ai/enrich` | Summarize and classify one normalized event |
| `WS` | `/ws/events` | Receive an initial snapshot and live event changes |

Example AI request:

```bash
curl -X POST https://your-render-api.example.com/api/v1/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What needs attention right now?","events":[]}'
```

## Run with Docker

```bash
docker compose up --build
```

The compose setup now initializes the PostGIS schema from `migrations/001_pulse_events.sql`, persists the Redis append-only log for local recovery, waits on healthchecks, and exposes production-like environment flags. Run `docker compose down -v` once when you need to recreate the database from the migration after schema changes.

## V0.3/V0.4 live data and operations

USGS ingestion polls the official real-time GeoJSON feed and normalizes earthquake IDs, magnitude, place, depth, timestamp, severity, and source URL. NASA FIRMS ingestion is enabled when `FIRMS_MAP_KEY` is configured; it reads a bounded near-real-time CSV window and clusters detections into compact fire events with detection count, maximum FRP, confidence, satellite, and day/night metadata. The ingestion supervisor isolates source failures and broadcasts typed `event.upsert`, `event.remove`, `snapshot.updated`, `source.error`, and `heartbeat` messages over `/ws/events`.

The first live deployment is intentionally single-instance. For horizontal scaling, move the event store to PostGIS, move fan-out to Redis Streams or Pub/Sub, and add replay cursors for reconnecting clients. Keep the browser on HTTP for filtered reads and AI requests, and use WSS only for live event-state changes.

## V0.8 AI summarization and classification

The V0.8 engine is deliberately split into synchronous and asynchronous paths. `/api/v1/ai/enrich` processes one normalized event immediately. When `ENABLE_AI_ENRICHMENT=true`, the background worker consumes a bounded queue and enriches new source events asynchronously. OpenAI-compatible calls request strict JSON Schema output containing `summary`, `category`, `severity`, `confidence`, `tags`, `rationale`, `generated_at`, and `model`. Every response is validated by Pydantic before it is persisted or broadcast. The model sees only the normalized event record and must not infer casualties, damage, or impact that are absent from the source.

Use `gpt-5-mini` as the default high-volume classifier/summarizer. For offline backfills, nightly evaluations, and large historical reclassification jobs, use OpenAI Batch API rather than synchronous calls. Keep a programmatic quality gate around schema validation, confidence bounds, summary length, and category/severity agreement with deterministic rules; route failures to retry or human review rather than silently accepting them. Structured Outputs are preferred over JSON mode because the API enforces the supplied schema.[1] Batch processing is designed for asynchronous classification and offers a separate rate-limit pool and lower cost than synchronous processing.[2]

## PostGIS and Redis production scaling

Set `DATABASE_URL` to a managed Postgres/PostGIS instance and apply `migrations/001_pulse_events.sql` once with a migration runner or `psql`. The `pulse_events.geom` column uses SRID 4326 and a GiST index for spatial queries; timestamps, source, category, severity, and metadata also have indexes for the event feed and AI context. Set `DB_POOL_MAX` conservatively per Render instance so the total connection count stays below the database plan limit.

Set `REDIS_URL` to a managed Redis instance. The API publishes typed event messages to `world-pulse:events`; every API instance subscribes and fans the messages to its own WebSocket clients. Without `REDIS_URL`, the app automatically falls back to the existing in-process hub, which is useful for local development but is not sufficient for multi-instance production. Keep Redis credentials server-side and use TLS URLs when the provider requires them.

For Render, deploy the API as a long-running web service with WebSocket support, configure the environment variables above, run the migration before enabling multiple instances, and verify `/api/v1/health` reports `postgis: true` and `redis: true`. The frontend continues to use HTTP for reads and AI requests and WSS for live event-state changes.

## V1.0 CI/CD and monitoring

The repository now includes `.github/workflows/ci-cd.yml`. Pull requests run Python compilation, API smoke tests, the Next.js production build, and a static-export check. Successful pushes to `main` can deploy the Cloudflare Pages artifact with Wrangler and trigger the Render API deploy hook. Both deployment steps are conditional, so the workflow remains safe until the production environment secrets and variables are configured. Render can also be configured to deploy “After CI Checks Pass,” which provides an additional deployment gate.[3]

Configure the `production-cloudflare` GitHub Environment with `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` secrets and `CLOUDFLARE_PAGES_PROJECT`, `CLOUDFLARE_PAGES_URL`, and `NEXT_PUBLIC_API_BASE` variables. Configure the `production-render` environment with the `RENDER_DEPLOY_HOOK_URL` secret and `RENDER_API_URL` variable. Cloudflare’s token should be scoped to Account / Cloudflare Pages / Edit, and Render deploy-hook URLs must be treated as secrets.[4] [5]

The repository includes `render.yaml` with `healthCheckPath: /api/v1/ready`. Set `REQUIRE_POSTGIS=true` and `REQUIRE_REDIS=true` in the production API only after managed PostGIS and Redis are connected; otherwise the service can start in compatibility mode while infrastructure is being provisioned. Render’s HTTP health checks accept a 2xx or 3xx response within five seconds and use the result during deploy cutover and instance recovery.[6]

`.github/workflows/monitoring.yml` runs every 15 minutes and checks `/api/v1/ready`, `/api/v1/health`, `/api/v1/events`, `/metrics`, and the Cloudflare homepage. If `MONITOR_ALERT_WEBHOOK_URL` is configured, failures send a generic JSON alert payload to the configured incident channel. The service also emits JSON logs and counters through `/metrics`, making it straightforward to scrape with a managed monitoring provider or a Prometheus-compatible collector. The monitoring workflow is a useful baseline; for stronger SLOs, add an external probe provider so checks continue even if GitHub Actions is unavailable.

## Roadmap

The next production steps are GDACS and weather adapters, replay cursors, alert subscriptions, authentication, observability, source-quality workflows, and a formal AI evaluation dashboard. Pulse AI remains behind server-side routes so provider credentials never reach the browser.

## References

[1] [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

[2] [OpenAI Batch API](https://developers.openai.com/api/docs/guides/batch)

[3] [Render Deploys and CI Checks](https://render.com/docs/deploys)

[4] [Cloudflare Pages Direct Upload with CI](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)

[5] [Render Deploy Hooks](https://render.com/docs/deploy-hooks)

[6] [Render Health Checks](https://render.com/docs/health-checks)
