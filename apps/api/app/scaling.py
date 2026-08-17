from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from typing import Any, Awaitable, Callable

logger = logging.getLogger("world_pulse.scaling")


class RedisEventBus:
    def __init__(self, local_hub: Any, channel: str = "world-pulse:events"):
        self.local_hub = local_hub
        self.url = __import__("os").getenv("REDIS_URL")
        self.channel = channel
        self.redis: Any | None = None
        self.pubsub: Any | None = None
        self.task: asyncio.Task | None = None
        self.distributed = False

    async def start(self) -> None:
        if not self.url:
            logger.info("REDIS_URL not configured; using in-process WebSocket fan-out")
            return
        try:
            import redis.asyncio as redis

            self.redis = redis.from_url(self.url, decode_responses=True)
            await self.redis.ping()
            self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
            await self.pubsub.subscribe(self.channel)
            self.task = asyncio.create_task(self._listen(), name="world-pulse-redis-subscriber")
            self.distributed = True
            logger.info("Redis event bus connected on %s", self.channel)
        except Exception as exc:
            logger.warning("Redis unavailable; using local WebSocket fan-out: %s", exc)
            await self.stop()

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
            self.task = None
        if self.pubsub:
            with suppress(Exception):
                await self.pubsub.close()
            self.pubsub = None
        if self.redis:
            with suppress(Exception):
                await self.redis.close()
            self.redis = None
        self.distributed = False

    async def publish(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message, default=str)
        if self.redis and self.distributed:
            await self.redis.publish(self.channel, payload)
            return
        await self.local_hub.broadcast(message)

    async def _listen(self) -> None:
        assert self.pubsub is not None
        async for message in self.pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                await self.local_hub.broadcast(json.loads(message["data"]))
            except Exception:
                logger.exception("Redis event payload could not be delivered")
