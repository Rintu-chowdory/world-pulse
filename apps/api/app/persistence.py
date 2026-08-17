from __future__ import annotations

import json
import logging
import os
from typing import Any

from .main_types import Event

logger = logging.getLogger("world_pulse.persistence")


class PostgresEventRepository:
    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DATABASE_URL")
        self.pool: Any | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.url)

    async def start(self) -> None:
        if not self.url:
            return
        import asyncpg

        self.pool = await asyncpg.create_pool(self.url, min_size=1, max_size=int(os.getenv("DB_POOL_MAX", "10")), command_timeout=15)
        async with self.pool.acquire() as conn:
            table = await conn.fetchval("SELECT to_regclass('pulse_events')")
            if table is None:
                raise RuntimeError("pulse_events table is missing; apply migrations/001_pulse_events.sql before starting multiple API instances")
        logger.info("PostGIS repository connected")

    async def stop(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def load_events(self) -> list[Event]:
        if not self.pool:
            return []
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, category, severity, title, location, lat, lon, magnitude, timestamp,
                       source, source_url, metadata, ai_summary, ai_category, ai_severity,
                       ai_confidence, ai_tags, ai_rationale
                FROM pulse_events
                ORDER BY timestamp DESC
                """
            )
        return [
            Event(
                id=row["id"], category=row["category"], severity=row["severity"], title=row["title"], location=row["location"],
                lat=row["lat"], lon=row["lon"], magnitude=row["magnitude"], timestamp=row["timestamp"], source=row["source"],
                source_url=row["source_url"],                 metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {}), ai_summary=row["ai_summary"],

                ai_category=row["ai_category"], ai_severity=row["ai_severity"], ai_confidence=row["ai_confidence"],
                ai_tags=list(row["ai_tags"] or []), ai_rationale=row["ai_rationale"],
            )
            for row in rows
        ]

    async def upsert(self, event: Event) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pulse_events (
                  id, category, severity, title, location, lat, lon, magnitude, timestamp,
                  source, source_url, metadata, geom, ai_summary, ai_category, ai_severity,
                  ai_confidence, ai_tags, ai_rationale, updated_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,ST_SetSRID(ST_MakePoint($7,$6),4326),$13,$14,$15,$16,$17,$18,NOW())
                ON CONFLICT (id) DO UPDATE SET
                  category=EXCLUDED.category, severity=EXCLUDED.severity, title=EXCLUDED.title,
                  location=EXCLUDED.location, lat=EXCLUDED.lat, lon=EXCLUDED.lon, magnitude=EXCLUDED.magnitude,
                  timestamp=EXCLUDED.timestamp, source=EXCLUDED.source, source_url=EXCLUDED.source_url,
                  metadata=EXCLUDED.metadata, geom=EXCLUDED.geom, ai_summary=EXCLUDED.ai_summary,
                  ai_category=EXCLUDED.ai_category, ai_severity=EXCLUDED.ai_severity,
                  ai_confidence=EXCLUDED.ai_confidence, ai_tags=EXCLUDED.ai_tags,
                  ai_rationale=EXCLUDED.ai_rationale, updated_at=NOW()
                """,
                event.id, event.category.value, event.severity.value, event.title, event.location, event.lat, event.lon,
                event.magnitude, event.timestamp, event.source, event.source_url, json.dumps(event.metadata), event.ai_summary,
                event.ai_category.value if event.ai_category else None, event.ai_severity.value if event.ai_severity else None,
                event.ai_confidence, event.ai_tags, event.ai_rationale,
            )

    async def delete(self, event_id: str) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM pulse_events WHERE id=$1", event_id)

    async def replace_source(self, source: str, incoming_ids: set[str]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM pulse_events WHERE source=$1 AND NOT (id = ANY($2::text[]))", source, list(incoming_ids) or ["__none__"])
