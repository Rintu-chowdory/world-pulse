from __future__ import annotations

import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(os_level())
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            handler.setFormatter(JsonFormatter())


def os_level() -> int:
    import os

    return getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)


class Metrics:
    def __init__(self) -> None:
        self.requests = Counter()
        self.duration_seconds = Counter()
        self.events_ingested = Counter()
        self.ai_enrichments = Counter()

    def request(self, method: str, path: str, status: int, duration: float) -> None:
        key = (method, path, str(status))
        self.requests[key] += 1
        self.duration_seconds[(method, path)] += duration

    def render(self, extra: dict[str, Any] | None = None) -> str:
        lines = [
            "# HELP world_pulse_http_requests_total Total HTTP requests handled by route and status.",
            "# TYPE world_pulse_http_requests_total counter",
        ]
        for (method, path, status), value in sorted(self.requests.items()):
            lines.append(f'world_pulse_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {value}')
        lines.extend([
            "# HELP world_pulse_http_request_duration_seconds_sum Total request duration in seconds.",
            "# TYPE world_pulse_http_request_duration_seconds_sum counter",
        ])
        for (method, path), value in sorted(self.duration_seconds.items()):
            lines.append(f'world_pulse_http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {value:.6f}')
        lines.extend([
            "# HELP world_pulse_events_ingested_total Events accepted from source adapters.",
            "# TYPE world_pulse_events_ingested_total counter",
        ])
        for source, value in sorted(self.events_ingested.items()):
            lines.append(f'world_pulse_events_ingested_total{{source="{source}"}} {value}')
        lines.extend([
            "# HELP world_pulse_ai_enrichments_total AI enrichment attempts by outcome.",
            "# TYPE world_pulse_ai_enrichments_total counter",
        ])
        for outcome, value in sorted(self.ai_enrichments.items()):
            lines.append(f'world_pulse_ai_enrichments_total{{outcome="{outcome}"}} {value}')
        if extra:
            lines.extend([
                "# HELP world_pulse_runtime_info Runtime state labels.",
                "# TYPE world_pulse_runtime_info gauge",
            ])
            labels = ",".join(f'{key}="{str(value).lower() if isinstance(value, bool) else value}"' for key, value in sorted(extra.items()))
            lines.append(f"world_pulse_runtime_info{{{labels}}} 1")
        return "\n".join(lines) + "\n"


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, metrics: Metrics):
        super().__init__(app)
        self.metrics = metrics

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        path = request.url.path
        self.metrics.request(request.method, path, response.status_code, time.perf_counter() - started)
        response.headers["X-Request-ID"] = request.headers.get("x-request-id", "world-pulse")
        return response
