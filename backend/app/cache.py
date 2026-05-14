from datetime import datetime, timedelta
from typing import Any


class InMemoryCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[datetime, Any]] = {}

    def get(self, key: str) -> Any | None:
        cached = self._items.get(key)
        if cached is None:
            return None

        expires_at, value = cached
        if expires_at <= datetime.now(expires_at.tzinfo):
            self._items.pop(key, None)
            return None

        return value

    def set(self, key: str, value: Any, expires_at: datetime) -> None:
        self._items[key] = (expires_at, value)


cache = InMemoryCache()


def meal_cache_expires_at(now: datetime) -> datetime:
    next_day = now.date() + timedelta(days=1)
    return datetime(
        next_day.year,
        next_day.month,
        next_day.day,
        0,
        10,
        tzinfo=now.tzinfo,
    )
