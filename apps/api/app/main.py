from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .ai_engine import AIEnrichmentEngine
from .ingestion import EventStore, IngestionSupervisor, WebSocketHub
from .main_types import AIEnrichRequest, AskRequest, AskResponse, Event, EventCategory, EventSeverity
from .persistence import PostgresEventRepository
from .scaling import RedisEventBus

logger = logging.getLogger("world_pulse.api")


def demo_events() -> list[Event]:
    now = datetime.now(timezone.utc)
    raw = [
        ("eq-1", EventCategory.earthquake, EventSeverity.warning, "Earthquake M6.2", "Japan", 35.68, 139.69, 6.2, 2),
        ("eq-2", EventCategory.earthquake, EventSeverity.advisory, "Earthquake M4.1", "Chile", -33.45, -70.65, 4.1, 45),
        ("fire-1", EventCategory.wildfire, EventSeverity.critical, "Wildfire spreading", "Canada", 51.05, -114.07, None, 5),
        ("fire-2", EventCategory.wildfire, EventSeverity.warning, "Wildfire contained 40%", "Greece", 37.98, 23.73, None, 120),
        ("flood-1", EventCategory.flood, EventSeverity.warning, "River flood warning", "Bangladesh", 23.68, 90.36, None, 8),
        ("storm-1", EventCategory.storm, EventSeverity.critical, "Tropical storm approaching", "Philippines", 14.6, 120.98, None, 15),
        ("volcano-1", EventCategory.volcano, EventSeverity.advisory, "Elevated seismic activity", "Iceland", 63.63, -19.62, None, 300),
    ]
    return [Event(id=r[0], category=r[1], severity=r[2], title=r[3], location=r[4], lat=r[5], lon=r[6], magnitude=r[7], timestamp=now - timedelta(minutes=r[8]), source="Demo Data Source") for r in raw]


def _fallback_answer(question: str, events: list[Event]) -> str:
    if not events:
        return "There are no events in the current view. Try clearing the search or category filters."
    critical = [event for event in events if event.severity == EventSeverity.critical]
    locations = ", ".join(dict.fromkeys(event.location for event in events[:4]))
    categories = sorted({event.category.value for event in events})
    lowered = question.lower()
    if "critical" in lowered or "attention" in lowered or "risk" in lowered:
        if critical:
            items = "; ".join(f"{event.title} in {event.location}" for event in critical)
            return f"The highest-priority signal is {items}. There are {len(critical)} critical event(s) in view; review these before advisory activity."
        return "No critical events are currently visible. The active picture is advisory to warning level."
    if "region" in lowered or "where" in lowered:
        return f"Activity is currently distributed across {locations}. The map contains {len(events)} indexed events across {len(categories)} categories."
    return f"The current view contains {len(events)} events across {len(categories)} categories. The freshest signals are {locations}. Ask about risk, regions, or critical events for a more focused read."


def _ai_answer(question: str, events: list[Event]) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    payload = {"model": os.getenv("OPENAI_MODEL", "gpt-5-mini"), "messages": [{"role": "system", "content": "You are Pulse AI, a concise global event intelligence analyst. Use only the supplied event data. State uncertainty clearly, never invent facts, and answer in 2-4 sentences with the most decision-relevant signal first."}, {"role": "user", "content": json.dumps({"question": question, "events": [event.model_dump(mode="json") for event in events]}, default=str)}], "max_completion_tokens": 300}
    req = urllib_request.Request(f"{base}/chat/completions", data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib_request.urlopen(req, timeout=12) as response:
            result = json.loads(response.read().decode())
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository: PostgresEventRepository | None = None
    candidate_repository = PostgresEventRepository()
    if candidate_repository.enabled:
        try:
            await candidate_repository.start()
            repository = candidate_repository
        except Exception as exc:
            logger.warning("PostGIS unavailable; using in-process event store: %s", exc)
    initial_events = await repository.load_events() if repository else []
    store = EventStore(initial_events or demo_events(), repository=repository)
    hub = WebSocketHub()
    bus = RedisEventBus(hub)

    async def on_ai_enriched(enriched: Event, enrichment: object) -> None:
        await store.upsert_event(enriched)
        await bus.publish({"type": "event.ai_enriched", "event": enriched.model_dump(mode="json"), "enrichment": getattr(enrichment, "model_dump", lambda **_: enrichment)(mode="json"), "sent_at": datetime.now(timezone.utc).isoformat()})

    ai_engine = AIEnrichmentEngine(on_enriched=on_ai_enriched)
    await bus.start()
    await ai_engine.start()
    supervisor = IngestionSupervisor(store, hub, broadcaster=bus, on_event=ai_engine.enqueue)
    app.state.event_store = store
    app.state.websocket_hub = hub
    app.state.ingestion = supervisor
    app.state.repository = repository
    app.state.event_bus = bus
    app.state.ai_engine = ai_engine
    await supervisor.start()
    yield
    await supervisor.stop()
    await ai_engine.stop()
    await bus.stop()
    if repository:
        await repository.stop()


app = FastAPI(title="World Pulse API", version="0.8.0", lifespan=lifespan)
allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])


@app.get("/api/v1/health")
async def health():
    store: EventStore = app.state.event_store
    return {"status": "ok", "time": datetime.now(timezone.utc), "events": len(await store.snapshot()), "live_ingestion": app.state.ingestion.enabled, "postgis": bool(app.state.repository), "redis": app.state.event_bus.distributed, "ai_enrichment": app.state.ai_engine.enabled}


@app.get("/api/v1/events", response_model=list[Event])
async def list_events(category: EventCategory | None = None, severity: EventSeverity | None = None, q: str | None = Query(default=None, description="Search title or location")):
    events = await app.state.event_store.snapshot()
    if category:
        events = [event for event in events if event.category == category]
    if severity:
        events = [event for event in events if event.severity == severity]
    if q:
        needle = q.lower()
        events = [event for event in events if needle in event.title.lower() or needle in event.location.lower()]
    return events


@app.get("/api/v1/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    events = await app.state.event_store.snapshot()
    for event in events:
        if event.id == event_id:
            return event
    return {"error": "not found"}


@app.get("/api/v1/stats")
async def stats():
    events = await app.state.event_store.snapshot()
    counts: dict[str, int] = {}
    for event in events:
        counts[event.category.value] = counts.get(event.category.value, 0) + 1
    return {"total": len(events), "by_category": counts, "live": app.state.ingestion.enabled, "sources": sorted({event.source for event in events}), "postgis": bool(app.state.repository), "redis": app.state.event_bus.distributed}


@app.post("/api/v1/ask", response_model=AskResponse)
async def ask_pulse(payload: AskRequest):
    events = payload.events or await app.state.event_store.snapshot()
    answer = await __import__("asyncio").to_thread(_ai_answer, payload.question, events)
    return AskResponse(answer=answer or _fallback_answer(payload.question, events), mode="ai" if answer else "fallback", sources=sorted({event.source for event in events}))


@app.post("/api/v1/ai/enrich")
async def enrich_event(payload: AIEnrichRequest):
    enriched, enrichment = await app.state.ai_engine.enrich_now(payload.event)
    return {"event": enriched, "enrichment": enrichment}


@app.websocket("/ws/events")
async def events_websocket(websocket: WebSocket):
    hub: WebSocketHub = app.state.websocket_hub
    store: EventStore = app.state.event_store
    await hub.connect(websocket)
    try:
        await websocket.send_json({"type": "snapshot", "events": [event.model_dump(mode="json") for event in await store.snapshot()], "sent_at": datetime.now(timezone.utc).isoformat()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(websocket)
    except Exception:
        await hub.disconnect(websocket)
