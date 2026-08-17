from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class _Entry(Generic[T]):
    expires_at: float
    value: T


class AsyncTtlCache(Generic[T]):
    """Small process-local cache; it never persists user queries or results."""

    def __init__(self, ttl_seconds: float, max_entries: int):
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._items: OrderedDict[str, _Entry[T]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> T | None:
        if self._ttl_seconds <= 0 or self._max_entries <= 0:
            return None
        now = time.monotonic()
        async with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return entry.value

    async def put(self, key: str, value: T) -> None:
        if self._ttl_seconds <= 0 or self._max_entries <= 0:
            return
        async with self._lock:
            self._items[key] = _Entry(
                expires_at=time.monotonic() + self._ttl_seconds,
                value=value,
            )
            self._items.move_to_end(key)
            while len(self._items) > self._max_entries:
                self._items.popitem(last=False)
