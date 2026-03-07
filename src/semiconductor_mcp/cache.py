"""In-memory TTL cache for source adapters.

Each source that benefits from caching creates its own TTLCache instance at
module level. Cache entries expire after ttl_seconds and are evicted lazily
on next access.

Cache is NOT persisted across restarts — intentional, to avoid serving stale
data after deployments or config changes.
"""

import time
from typing import Any


class TTLCache:
    """Simple time-to-live in-memory cache safe for use within a single asyncio
    event loop (no cross-thread locking needed).
    """

    def __init__(self, ttl_seconds: int, name: str = ""):
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl_seconds
        self.name = name

    def get(self, key: str) -> Any:
        """Return the cached value if still within TTL, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts >= self._ttl:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value, resetting its TTL."""
        self._store[key] = (time.monotonic(), value)

    def invalidate(self, key: str) -> None:
        """Remove a specific key."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
