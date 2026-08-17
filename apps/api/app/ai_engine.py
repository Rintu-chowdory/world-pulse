from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field

from .main_types import Event, EventCategory, EventSeverity

logger = logging.getLogger("world_pulse.ai")


class AIEnrichment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=500)
    category: EventCategory
    severity: EventSeverity
    confidence: float = Field(ge=0, le=1)
    tags: list[str] = Field(max_length=8)
    rationale: str = Field(min_length=1, max_length=500)
    generated_at: datetime
    model: str


AI_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "minLength": 1, "maxLength": 500},
        "category": {"type": "string", "enum": [item.value for item in EventCategory]},
        "severity": {"type": "string", "enum": [item.value for item in EventSeverity]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "rationale": {"type": "string", "minLength": 1, "maxLength": 500},
        "generated_at": {"type": "string"},
        "model": {"type": "string"},
    },
    "required": ["summary", "category", "severity", "confidence", "tags", "rationale", "generated_at", "model"],
    "additionalProperties": False,
}


@dataclass
class AIJob:
    event: Event
    requested_at: datetime


def _fallback(event: Event) -> AIEnrichment:
    severity = event.severity
    if event.category == EventCategory.earthquake and (event.magnitude or 0) >= 6.5:
        severity = EventSeverity.critical
    elif event.category == EventCategory.wildfire and float(event.metadata.get("max_frp") or 0) >= 100:
        severity = EventSeverity.critical
    tag = event.category.value
    summary = f"{event.title} reported near {event.location}. Source: {event.source}."
    return AIEnrichment(
        summary=summary[:500],
        category=event.category,
        severity=severity,
        confidence=0.55,
        tags=[tag, severity.value],
        rationale="Deterministic fallback based on the normalized source category, severity, and event metadata.",
        generated_at=datetime.now(timezone.utc),
        model="fallback",
    )


def _openai_enrichment(event: Event) -> AIEnrichment | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    system = (
        "You are the World Pulse event intelligence classifier. Classify and summarize only the supplied normalized event. "
        "Do not infer casualties, damage, or impact that is not present. Preserve source identity. "
        "Return a short analyst summary, a category, severity, calibrated confidence, tags, and a rationale."
    )
    user = json.dumps(
        {
            "event": event.model_dump(mode="json"),
            "classification_policy": {
                "critical": "Immediate attention or high-impact signal supported by the record",
                "warning": "Material signal requiring monitoring",
                "advisory": "Meaningful but lower urgency signal",
                "normal": "Informational signal",
            },
        },
        default=str,
    )
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_completion_tokens": 450,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "world_pulse_event_enrichment", "strict": True, "schema": AI_SCHEMA},
        },
    }
    req = Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
        parsed = AIEnrichment.model_validate(json.loads(content))
        return parsed.model_copy(update={"model": model, "generated_at": datetime.now(timezone.utc)})
    except (KeyError, IndexError, TypeError, ValueError, HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("OpenAI enrichment failed for %s: %s", event.id, exc)
        return None


class AIEnrichmentEngine:
    def __init__(self, on_enriched: Any | None = None):
        self.enabled = os.getenv("ENABLE_AI_ENRICHMENT", "false").lower() not in {"0", "false", "no"}
        self.worker_count = max(1, min(int(os.getenv("AI_WORKERS", "2")), 8))
        self.queue: asyncio.Queue[AIJob] = asyncio.Queue(maxsize=500)
        self.on_enriched = on_enriched
        self.tasks: list[asyncio.Task] = []
        self.cache: dict[str, AIEnrichment] = {}

    async def start(self) -> None:
        if self.enabled and not self.tasks:
            self.tasks = [asyncio.create_task(self._worker(index), name=f"world-pulse-ai-{index}") for index in range(self.worker_count)]

    async def stop(self) -> None:
        for task in self.tasks:
            task.cancel()
        for task in self.tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.tasks = []

    async def enqueue(self, event: Event) -> None:
        if not self.enabled:
            return
        try:
            self.queue.put_nowait(AIJob(event=event, requested_at=datetime.now(timezone.utc)))
        except asyncio.QueueFull:
            logger.warning("AI queue full; dropping enrichment request for %s", event.id)

    async def enrich_now(self, event: Event) -> tuple[Event, AIEnrichment]:
        enrichment = await asyncio.to_thread(_openai_enrichment, event)
        if enrichment is None:
            enrichment = _fallback(event)
        enriched = event.model_copy(
            update={
                "ai_summary": enrichment.summary,
                "ai_category": enrichment.category,
                "ai_severity": enrichment.severity,
                "ai_confidence": enrichment.confidence,
                "ai_tags": enrichment.tags,
                "ai_rationale": enrichment.rationale,
            }
        )
        self.cache[event.id] = enrichment
        if self.on_enriched:
            await self.on_enriched(enriched, enrichment)
        return enriched, enrichment

    async def _worker(self, index: int) -> None:
        while True:
            job = await self.queue.get()
            try:
                await self.enrich_now(job.event)
            except Exception:
                logger.exception("AI worker %s failed for %s", index, job.event.id)
            finally:
                self.queue.task_done()
