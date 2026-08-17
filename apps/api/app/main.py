from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
import json
import os
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="World Pulse API", version="0.2.0")
allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

class EventCategory(str, Enum):
    earthquake = "earthquake"
    wildfire = "wildfire"
    flood = "flood"
    storm = "storm"
    volcano = "volcano"

class EventSeverity(str, Enum):
    critical = "critical"
    warning = "warning"
    advisory = "advisory"
    normal = "normal"

class Event(BaseModel):
    id: str
    category: EventCategory
    severity: EventSeverity
    title: str
    location: str
    lat: float
    lon: float
    magnitude: Optional[float] = None
    timestamp: datetime
    source: str

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    events: list[Event] = Field(default_factory=list, max_length=100)

class AskResponse(BaseModel):
    answer: str
    mode: str
    sources: list[str]

def _demo_events() -> list[Event]:
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

DEMO_EVENTS = _demo_events()

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc)}

@app.get("/api/v1/events", response_model=list[Event])
def list_events(category: Optional[EventCategory] = None, severity: Optional[EventSeverity] = None, q: Optional[str] = Query(default=None, description="Search title or location")):
    events = DEMO_EVENTS
    if category:
        events = [e for e in events if e.category == category]
    if severity:
        events = [e for e in events if e.severity == severity]
    if q:
        needle = q.lower()
        events = [e for e in events if needle in e.title.lower() or needle in e.location.lower()]
    return sorted(events, key=lambda e: e.timestamp, reverse=True)

@app.get("/api/v1/events/{event_id}", response_model=Event)
def get_event(event_id: str):
    for event in DEMO_EVENTS:
        if event.id == event_id:
            return event
    return {"error": "not found"}

@app.get("/api/v1/stats")
def stats():
    counts = {}
    for event in DEMO_EVENTS:
        counts[event.category.value] = counts.get(event.category.value, 0) + 1
    return {"total": len(DEMO_EVENTS), "by_category": counts, "live": True}

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

def _ai_answer(question: str, events: list[Event]) -> Optional[str]:
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

@app.post("/api/v1/ask", response_model=AskResponse)
def ask_pulse(payload: AskRequest):
    events = payload.events or DEMO_EVENTS
    answer = _ai_answer(payload.question, events)
    mode = "ai" if answer else "fallback"
    return AskResponse(answer=answer or _fallback_answer(payload.question, events), mode=mode, sources=sorted({event.source for event in events}))
