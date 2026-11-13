"""Límites simples en memoria por clave (IP). Se reinician al reiniciar el servidor."""
import time
from collections import defaultdict

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, limit: int, window_s: float, message: str):
        self.limit, self.window_s, self.message = limit, window_s, message
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        if self.limit <= 0:
            return
        now = time.monotonic()
        recent = [t for t in self._hits[key] if now - t < self.window_s]
        if len(recent) >= self.limit:
            self._hits[key] = recent
            raise HTTPException(429, self.message)
        recent.append(now)
        self._hits[key] = recent


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
