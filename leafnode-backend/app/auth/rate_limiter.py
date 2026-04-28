import asyncio
import time
from collections import defaultdict


class LoginRateLimiter:
    """In-memory rate limiter. Thread-safe via asyncio lock."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> bool:
        """Returns True if the request is allowed, False if rate-limited."""
        async with self._lock:
            now = time.monotonic()
            cutoff = now - self.window_seconds
            self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
            if len(self._attempts[key]) >= self.max_attempts:
                return False
            self._attempts[key].append(now)
            return True

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._attempts.pop(key, None)


login_limiter = LoginRateLimiter()
