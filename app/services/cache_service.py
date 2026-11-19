import json
import logging
import time
from typing import Any
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory cache if Redis is unreachable
_memory_cache: dict[str, tuple[float, str]] = {}


class CacheService:
    def __init__(self, redis_url: str | None = None):
        self.url = redis_url or settings.REDIS_URL
        self._client: redis.Redis | None = None
        self._redis_available: bool | None = None

    def _get_client(self) -> redis.Redis | None:
        if self._redis_available is False:
            return None

        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.url,
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0,
                )
                self._client.ping()
                self._redis_available = True
                logger.info("Connected to Redis cache at %s", self.url)
            except Exception as e:
                self._redis_available = False
                logger.debug("Redis unavailable (%s); using in-memory cache fallback.", str(e))
                self._client = None

        return self._client

    def get(self, key: str) -> dict[str, Any] | None:
        client = self._get_client()
        if client:
            try:
                val = client.get(key)
                if val:
                    logger.debug("Redis cache HIT: %s", key)
                    return json.loads(val)
                logger.debug("Redis cache MISS: %s", key)
                return None
            except Exception as e:
                logger.warning("Redis read error (%s); falling back to memory.", str(e))

        # Memory cache fallback
        if key in _memory_cache:
            expires_at, raw_json = _memory_cache[key]
            if time.time() < expires_at:
                logger.debug("Memory cache HIT: %s", key)
                return json.loads(raw_json)
            else:
                del _memory_cache[key]

        logger.debug("Cache MISS: %s", key)
        return None

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int = 600) -> None:
        raw_json = json.dumps(value)
        client = self._get_client()
        if client:
            try:
                client.setex(key, ttl_seconds, raw_json)
                return
            except Exception as e:
                logger.warning("Redis write error (%s); saving to memory.", str(e))

        _memory_cache[key] = (time.time() + ttl_seconds, raw_json)

    def delete(self, key: str) -> None:
        client = self._get_client()
        if client:
            try:
                client.delete(key)
            except Exception:
                pass
        _memory_cache.pop(key, None)

    def flush(self) -> None:
        client = self._get_client()
        if client:
            try:
                client.flushdb()
            except Exception:
                pass
        _memory_cache.clear()


cache_service = CacheService()
