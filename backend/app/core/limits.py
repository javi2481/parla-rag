"""Límite simple de pedidos por IP, guardado en memoria.

Se reinicia cuando se reinicia el servidor. Alcanza para una herramienta interna o una demo.
"""
import time
from collections import defaultdict

from fastapi import HTTPException, Request


class RateLimiter:
    # Crea el limitador: como máximo `limit` pedidos cada `window_s` segundos.
    # Si limit es 0 (o menos), no limita nada.
    def __init__(self, limit: int, window_s: float, message: str):
        self.limit = limit
        self.window_s = window_s
        self.message = message
        self._hits: dict[str, list[float]] = defaultdict(list)

    # Registra un pedido de `key` (la IP). Si ya pasó el límite, corta con un error 429.
    def check(self, key: str) -> None:
        if self.limit <= 0:
            return
        now = time.monotonic()

        # Nos quedamos solo con los pedidos que están dentro de la ventana de tiempo.
        recent = []
        for moment in self._hits[key]:
            if now - moment < self.window_s:
                recent.append(moment)

        if len(recent) >= self.limit:
            self._hits[key] = recent
            raise HTTPException(429, self.message)

        recent.append(now)
        self._hits[key] = recent


# Devuelve la IP de quien hace el pedido (o "unknown" si no se conoce).
def client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"
