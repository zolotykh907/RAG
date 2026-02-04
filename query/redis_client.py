import hashlib
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared'))
from logs import setup_logging

import redis


class RedisDB:
    def __init__(self, host='localhost', port=6379, db=0):
        self.logger = setup_logging('logs', 'Redis')
        self.redis_client = redis.Redis(host=host, port=port, db=db)

    def make_cache_key(self, query: str) -> str:
        """Generate a cache key based on the query.

        Args:
            query (str): The query string.

        Returns:
            str: A unique cache key for the query."""
        return f"rag:{hashlib.md5(query.encode()).hexdigest()}"


    def get_from_cache(self, query: str):
        """Retrieve the cached answer for a given query.

        Args:
            query (str): The query string.

        Returns:
            dict: The cached answer containing 'answer' and 'texts', or None if not found
        """
        key = self.make_cache_key(query)
        value = self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None


    def save_to_cache(self, query: str, answer: str):
        """Save the answer to the cache with a TTL of 24 hours.

        Args:
            query (str): The query string.
            answer (dict): The answer containing 'answer' and 'texts'.
        """
        key = self.make_cache_key(query)
        self.redis_client.setex(key, 60 * 60 * 24, json.dumps(answer))  # TTL: 24 часа
        self.logger.info(f"Saved to cache: {query[:25]}...")
