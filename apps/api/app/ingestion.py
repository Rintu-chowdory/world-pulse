from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import os
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .main_types import Event, EventCategory, EventSeverity

logger = logging.getLogger("world_pulse.ingestion")

USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/{source}/world/{days}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_json(url: str, timeout: int = 15) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": "WorldPulse/0.4 (+global-event-intelligence)"})
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_text(url: str, timeout: int = 30) -> str:
    req = Request(url, headers={"User-Agent": "WorldPulse/0.4 (+global-event-intelligence)"})
    with urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _severity_from_magnitude(magnitude: float | None) -> EventSeverity:
    if magnitude is None:
        return EventSeverity.normal
    if magnitude >= 6.5:
        return EventSeverity.critical
    if magnitude >= 5.0:
        return EventSeverity.warning
    if magnitude >= 3.5:
        return EventSeverity.advisory
    return EventSeverity.normal


def _parse_iso_millis(value: int | None) -> datetime:
    if not value:
        return utc_now()
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def fetch_usgs_events() -> list[Event]:
    payload = _get_json(USGS_FEED_URL)
    events: list[Event] = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        coordinates = feature.get("geometry", {}).get("coordinates") or []
        if len(coordinates) < 2:
            continue
        event_id = str(feature.get("id") or properties.get("code") or f"usgs-{properties.get('time')}")
        title = str(properties.get("title") or "Earthquake")
        events.append(Event(id=f"usgs:{event_id}", category=EventCategory.earthquake, severity=_severity_from_magnitude(properties.get("mag")), title=title, location=title.rsplit(", ", 1)[-1], lat=float(coordinates[1]), lon=float(coordinates[0]), magnitude=properties.get("mag"), timestamp=_parse_iso_millis(properties.get("time")), source="USGS Earthquake Hazards Program", source_url=properties.get("url"), metadata={"depth_km": coordinates[2] if len(coordinates) > 2 else None, "usgs_id": event_id}))
    return events


def _fire_severity(confidence: str, frp: float) -> EventSeverity:
    if frp >= 100 or confidence.lower() == "h":
        return EventSeverity.critical
    if frp >= 30 or confidence.lower() in {"n", "nominal"}:
        return EventSeverity.warning
    return EventSeverity.advisory


def fetch_firms_events() -> list[Event]:
    map_key = os.getenv("FIRMS_MAP_KEY")
    if not map_key:
        return []
    source = os.getenv("FIRMS_SOURCE", "VIIRS_NOAA20_NRT")
    days = max(1, min(int(os.getenv("FIRMS_DAY_RANGE", "1")), 3))
    csv_text = _get_text(FIRMS_AREA_URL.format(map_key=map_key, source=source, days=days), timeout=45)
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    clusters: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
            clusters[(round(lat * 2), round(lon * 2))].append(row)
        except (KeyError, TypeError, ValueError):
            continue
    events: list[Event] = []
    for (lat_cell, lon_cell), cluster in clusters.items():
        first = cluster[0]
        lat = sum(float(row["latitude"]) for row in cluster) / len(cluster)
        lon = sum(float(row["longitude"]) for row in cluster) / len(cluster)
        frps = [float(row.get("frp") or 0) for row in cluster]
        max_frp = max(frps, default=0)
        confidence = max((str(row.get("confidence") or "n") for row in cluster), key=lambda value: {"h": 3, "n": 2, "l": 1}.get(value.lower(), 0))
        acquisition = f"{first.get('acq_date', '')} {first.get('acq_time', '0000')}"
        try:
            timestamp = datetime.strptime(acquisition, "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
        except ValueError:
            timestamp = utc_now()
        event_id = f"firms:{source}:{lat_cell}:{lon_cell}:{timestamp.strftime('%Y%m%d%H')}"
        events.append(Event(id=event_id, category=EventCategory.wildfire, severity=_fire_severity(confidence, max_frp), title=f"Active fire cluster · {len(cluster)} detections", location=f"{lat:.2f}°, {lon:.2f}°", lat=lat, lon=lon, magnitude=None, timestamp=timestamp, source="NASA FIRMS", source_url="https://firms.modaps.eosdis.nasa.gov/active_fire/", metadata={"detections": len(cluster), "max_frp": max_frp, "confidence": confidence, "satellite": first.get("satellite"), "instrument": first.get("instrument"), "daynight": first.get("daynight"), "source_dataset": source}))
    return events


@dataclass
class EventChange:
    kind: str
    event: Event | None = None
    event_id: str | None = None


class EventStore:
    def __init__(self, initial_events: list[Event] | None = None, repository: Any | None = None):
        self._events: dict[str, Event] = {event.id: event for event in (initial_events or [])}
        self._lock = asyncio.Lock()
        self.repository = repository

    async def snapshot(self) -> list[Event]:
        async with self._lock:
            return sorted(self._events.values(), key=lambda event: event.timestamp, reverse=True)

    async def upsert_event(self, event: Event) -> None:
        async with self._lock:
            self._events[event.id] = event
        if self.repository:
            await self.repository.upsert(event)

    async def replace_source(self, source: str, incoming: list[Event]) -> list[EventChange]:
        async with self._lock:
            changes: list[EventChange] = []
            incoming_ids = {event.id for event in incoming}
            old_source_ids = {event_id for event_id, event in self._events.items() if event.source == source}
            for event in incoming:
                previous = self._events.get(event.id)
                self._events[event.id] = event
                if previous != event:
                    changes.append(EventChange(kind="event.upsert", event=event))
            removed_ids = old_source_ids - incoming_ids
            for event_id in removed_ids:
                del self._events[event_id]
                changes.append(EventChange(kind="event.remove", event_id=event_id))
        if self.repository:
            for event in incoming:
                await self.repository.upsert(event)
            for event_id in removed_ids:
                await self.repository.delete(event_id)
            await self.repository.replace_source(source, incoming_ids)
        return changes


class WebSocketHub:
    def __init__(self):
        self._clients: set[Any] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(self, websocket: Any) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        async with self._lock:
            clients = list(self._clients)
        dead = []
        for client in clients:
            try:
                await client.send_json(message)
            except Exception:
                dead.append(client)
        for client in dead:
            await self.disconnect(client)


class IngestionSupervisor:
    def __init__(self, store: EventStore, hub: WebSocketHub, broadcaster: Any | None = None, on_event: Any | None = None):
        self.store = store
        self.hub = hub
        self.broadcaster = broadcaster or hub
        self.on_event = on_event
        self.task: asyncio.Task | None = None
        self.enabled = os.getenv("ENABLE_LIVE_INGESTION", "true").lower() not in {"0", "false", "no"}
        self.interval = max(30, int(os.getenv("INGESTION_INTERVAL_SECONDS", "60")))

    async def start(self) -> None:
        if self.enabled and self.task is None:
            self.task = asyncio.create_task(self._run(), name="world-pulse-ingestion")

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
            self.task = None

    async def _poll_source(self, name: str, fetcher: Any) -> None:
        try:
            events = await asyncio.to_thread(fetcher)
            changes = await self.store.replace_source(name, events)
            for change in changes:
                payload = {"type": change.kind, "event": change.event.model_dump(mode="json") if change.event else None, "event_id": change.event_id, "source": name, "sent_at": utc_now().isoformat()}
                await self.broadcaster.publish(payload)
                if change.event and self.on_event:
                    await self.on_event(change.event)
            if changes:
                await self.broadcaster.publish({"type": "snapshot.updated", "count": len(await self.store.snapshot()), "source": name, "sent_at": utc_now().isoformat()})
            logger.info("ingested %s events from %s", len(events), name)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            logger.warning("source %s unavailable: %s", name, exc)
            await self.broadcaster.publish({"type": "source.error", "source": name, "message": str(exc), "sent_at": utc_now().isoformat()})

    async def _run(self) -> None:
        while True:
            await asyncio.gather(self._poll_source("USGS", fetch_usgs_events), self._poll_source("NASA FIRMS", fetch_firms_events))
            await self.broadcaster.publish({"type": "heartbeat", "sent_at": utc_now().isoformat()})
            await asyncio.sleep(self.interval)
