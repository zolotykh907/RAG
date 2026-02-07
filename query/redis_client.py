import hashlib
import json
import logging

import redis


logger = logging.getLogger(__name__)


class RedisDB:
    def __init__(self, host='localhost', port=6379, db=0):
        self.logger = logger
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db)
            self.redis_client.ping()
            self.logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            self.logger.warning(f"Redis not available at {host}:{port}: {e}")
            self.redis_client = None

    def make_cache_key(self, query: str) -> str:
        """Generate a cache key based on the query.

        Args:
            query (str): The query string.

        Returns:
            str: A unique cache key for the query.
        """
        return f"rag:{hashlib.sha256(query.encode()).hexdigest()}"

    def get_from_cache(self, query: str):
        """Retrieve the cached answer for a given query.

        Args:
            query (str): The query string.

        Returns:
            dict: The cached answer containing 'answer' and 'texts', or None if not found
        """
        if self.redis_client is None:
            return None
        key = self.make_cache_key(query)
        value = self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None

    def save_to_cache(self, query: str, answer: dict):
        """Save the answer to the cache with a TTL of 24 hours.

        Args:
            query (str): The query string.
            answer (dict): The answer containing 'answer' and 'texts'.
        """
        if self.redis_client is None:
            return
        key = self.make_cache_key(query)
        self.redis_client.setex(key, 60 * 60 * 24, json.dumps(answer))
        self.logger.info(f"Saved to cache: {query[:25]}...")
