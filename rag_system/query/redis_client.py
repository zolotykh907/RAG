import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

import redis


logger = logging.getLogger(__name__)


class RedisDB:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0) -> None:
        self.logger = logger
        try:
            self.redis_client: Optional[redis.Redis] = redis.Redis(host=host, port=port, db=db)
            self.redis_client.ping()
            self.logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            self.logger.warning(f"Redis not available at {host}:{port}: {e}")
            self.redis_client = None

    def make_cache_key(self, query: str, namespace: str = "default") -> str:
        cache_input = f"{namespace}\0{query}"
        return f"rag:{hashlib.sha256(cache_input.encode()).hexdigest()}"

    def get_from_cache(self, query: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        if self.redis_client is None:
            return None
        key = self.make_cache_key(query, namespace=namespace)
        value = self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None

    def save_to_cache(self, query: str, answer: Dict[str, Any], namespace: str = "default") -> None:
        if self.redis_client is None:
            return
        key = self.make_cache_key(query, namespace=namespace)
        self.redis_client.setex(key, 60 * 60 * 24, json.dumps(answer))
        self.logger.info("Saved query result to cache")

    def flush_cache(self) -> None:
        """Invalidate all cached query results. Call after index updates."""
        if self.redis_client is None:
            return
        try:
            keys: List[Any] = self.redis_client.keys("rag:*")
            if keys:
                self.redis_client.delete(*keys)
                self.logger.info(f"Flushed {len(keys)} cached query results")
        except Exception as e:
            self.logger.warning(f"Failed to flush cache: {e}")
