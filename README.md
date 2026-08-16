# World Pulse

Global event intelligence platform — "see what's happening around the world."

## Status: V0.1 — Foundation

- 🌍 Global map (MapLibre, dark theme)
- 📍 Demo event markers (earthquakes, wildfires, floods, storms, volcanoes)
- 🔎 Event search
- 🎛️ Category filters
- 📡 FastAPI backend

## Structure

```
world-pulse/
├── apps/
│   ├── web/     # Next.js frontend
│   └── api/     # FastAPI backend
├── docker-compose.yml
```

## Run locally (without Docker)

Backend:

```bash
cd apps/api
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000 — the frontend expects the API on http://127.0.0.1:8000 (see `apps/web/.env.local`).

## Run with Docker

```bash
docker compose up --build
```

## Roadmap

- V0.2 World map: clusters, popups, layer toggles
- V0.3 Disaster Tracker: real data sources (USGS, NASA FIRMS, GDACS)
- V0.4 Live Event Engine: ingestion, normalization, WebSockets
- V0.5 Flights, V0.6 Vessels, V0.7 Weather + Alerts
- V0.8 AI: summaries, classification, deduplication
- V0.9 User system: accounts, saved locations, alerts
- V1.0 Production: CI/CD, monitoring, security
