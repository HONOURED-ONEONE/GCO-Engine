import time
from typing import Dict, Any, Optional

class TTLCache:
    def __init__(self, ttl_sec: int):
        self.ttl_sec = ttl_sec
        self.cache: Dict[str, Any] = {}
        self.expire_at: Dict[str, float] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache and time.time() < self.expire_at[key]:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = value
        self.expire_at[key] = time.time() + self.ttl_sec

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
        if key in self.expire_at:
            del self.expire_at[key]

    def clear(self):
        self.cache = {}
        self.expire_at = {}
