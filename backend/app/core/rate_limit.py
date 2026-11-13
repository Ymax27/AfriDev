"""In-process sliding window rate limiting used as a FastAPI dependency."""

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request

from app.core.exceptions import RateLimitError

_buckets: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    _buckets.clear()


class RateLimiter:
    def __init__(self, times: int, seconds: int, *, scope: str = "default") -> None:
        self.times = times
        self.seconds = seconds
        self.scope = scope

    async def __call__(self, request: Request) -> None:
        client = request.client.host if request.client else "anonymous"
        user_id = getattr(request.state, "user_id", None)
        key = f"{self.scope}:{user_id or client}"
        now = time.monotonic()
        bucket = _buckets[key]
        while bucket and now - bucket[0] > self.seconds:
            bucket.popleft()
        if len(bucket) >= self.times:
            raise RateLimitError("Too many requests, please slow down")
        bucket.append(now)


def rate_limit(times: int, seconds: int, *, scope: str) -> Callable[..., Awaitable[None]]:
    return RateLimiter(times, seconds, scope=scope)
