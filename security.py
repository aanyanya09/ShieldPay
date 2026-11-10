"""security.py - rate limits and admin password check (B6)."""

import hmac
import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

# Remembers when each visitor made each kind of request
_hits = defaultdict(deque)


def reset_limits() -> None:
    """Forget all counts. Tests call this so one test cannot affect another."""
    _hits.clear()


def rate_limit(name: str, limit: int, window_seconds: int):
    """Allow at most `limit` calls per visitor in `window_seconds`."""
    def checker(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"{name}:{ip}"
        now = time.time()
        calls = _hits[key]
        while calls and now - calls[0] > window_seconds:
            calls.popleft()
        if len(calls) >= limit:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        calls.append(now)
    return checker


def require_admin(request: Request) -> None:
    """Admin routes need the ADMIN_PASSWORD in the X-Admin-Password header."""
    expected = os.getenv("ADMIN_PASSWORD", "")
    if not expected:
        raise HTTPException(status_code=401, detail="Unauthorized.")  # no password set = locked
    given = request.headers.get("X-Admin-Password", "")
    if not hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Unauthorized.")