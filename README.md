# World Pulse

World Pulse is a global event intelligence platform for seeing what is happening around the world with less noise and more context. The project combines a dark geospatial command center, live event filtering, ranked signal summaries, and Pulse AI decision support.

## Current release: V0.4 — Live intelligence foundation

The upgraded experience includes a professional situation-room layout, responsive dark visual system, live world map framing, signal priority panel, metric strip, improved event exploration, an AI assistant with guided questions, real USGS earthquake ingestion, optional NASA FIRMS fire ingestion, normalized event contracts, a lifecycle-managed ingestion supervisor, and WebSocket delivery. The AI endpoint is grounded in the event records supplied by the current map view and returns a deterministic fallback when no model credentials are configured, so the interface remains useful in every environment.

| Layer | Location | Responsibility |
| --- | --- | --- |
| Web | `apps/web` | Next.js interface, MapLibre map, filters, live feed, Pulse AI panel |
| API | `apps/api` | FastAPI event endpoints, stats, health, AI answering route, ingestion adapters, WebSocket hub |
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
ALLOWED_ORIGINS=https://your-cloudflare-domain.example
```

`OPENAI_API_KEY` is read only by FastAPI and is never sent to the browser. If it is absent or the provider is unavailable, `/api/v1/ask` uses the local event-aware fallback response. This makes preview deployments and local demos work without a secret.

On Cloudflare, set `NEXT_PUBLIC_API_BASE` to the public Render URL for the API, for example:

```text
NEXT_PUBLIC_API_BASE=https://your-render-api.example.com
```

After changing a Cloudflare Pages environment variable, trigger a new frontend deployment. After changing Render environment variables, redeploy the API service.

## API routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/events` | Event list with `category`, `severity`, and `q` filters |
| `GET` | `/api/v1/events/{event_id}` | Single event lookup |
| `GET` | `/api/v1/stats` | Current totals by category |
| `POST` | `/api/v1/ask` | Ask Pulse AI about a supplied event view |
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

The compose setup preserves the existing PostGIS and Redis services for the next ingestion phase. The current event catalog remains demo data until the real-source ingestion work is enabled.

## V0.3/V0.4 live data and operations

USGS ingestion polls the official real-time GeoJSON feed and normalizes earthquake IDs, magnitude, place, depth, timestamp, severity, and source URL. NASA FIRMS ingestion is enabled when `FIRMS_MAP_KEY` is configured; it reads a bounded near-real-time CSV window and clusters detections into compact fire events with detection count, maximum FRP, confidence, satellite, and day/night metadata. The ingestion supervisor isolates source failures and broadcasts typed `event.upsert`, `event.remove`, `snapshot.updated`, `source.error`, and `heartbeat` messages over `/ws/events`.

The first live deployment is intentionally single-instance. For horizontal scaling, move the event store to PostGIS, move fan-out to Redis Streams or Pub/Sub, and add replay cursors for reconnecting clients. Keep the browser on HTTP for filtered reads and AI requests, and use WSS only for live event-state changes.

## Roadmap

The next production steps are durable event history, GDACS and weather adapters, replay cursors, alert subscriptions, authentication, observability, and source-quality workflows. Pulse AI is intentionally implemented behind a single backend route so summaries, classification, source citations, and future retrieval can be added without exposing provider credentials to the client.
