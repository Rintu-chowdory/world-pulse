from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
import random

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="World Pulse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # V0.1 only — restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return [
        Event(
            id=r[0], category=r[1], severity=r[2], title=r[3], location=r[4],
            lat=r[5], lon=r[6], magnitude=r[7],
            timestamp=now - timedelta(minutes=r[8]),
            source="Demo Data Source",
        )
        for r in raw
    ]


DEMO_EVENTS = _demo_events()


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc)}


@app.get("/api/v1/events", response_model=list[Event])
def list_events(
    category: Optional[EventCategory] = None,
    severity: Optional[EventSeverity] = None,
    q: Optional[str] = Query(default=None, description="Suche in Titel/Ort"),
):
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
    for e in DEMO_EVENTS:
        if e.id == event_id:
            return e
    return {"error": "not found"}


@app.get("/api/v1/stats")
def stats():
    counts = {}
    for e in DEMO_EVENTS:
        counts[e.category.value] = counts.get(e.category.value, 0) + 1
    return {"total": len(DEMO_EVENTS), "by_category": counts, "live": True}
