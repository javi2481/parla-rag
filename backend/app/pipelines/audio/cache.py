"""Caché en disco de audios TTS. La clave incluye modelo, voz, ajustes y texto: si algo cambia, se regenera.

Sobrevive a reinicios (y en Docker, a recrear el contenedor si se monta como volumen).
Cuando pasa el tamaño máximo, borra los archivos menos usados.
"""
import hashlib
import json
import os
from pathlib import Path


class AudioCache:
    def __init__(self, directory: str | Path, max_mb: int):
        self.dir = Path(directory)
        self.max_bytes = max_mb * 1024 * 1024

    @staticmethod
    def key(**parts: object) -> str:
        return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def get(self, key: str) -> bytes | None:
        path = self.dir / f"{key}.mp3"
        try:
            data = path.read_bytes()
        except OSError:
            return None
        os.utime(path)  # marca como usado recientemente
        return data

    def put(self, key: str, data: bytes) -> None:
        if self.max_bytes <= 0:
            return
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            tmp = self.dir / f"{key}.tmp"
            tmp.write_bytes(data)
            tmp.replace(self.dir / f"{key}.mp3")
            self._evict()
        except OSError:
            pass  # sin caché no se rompe nada: solo se paga de nuevo

    def _evict(self) -> None:
        files = sorted(self.dir.glob("*.mp3"), key=lambda f: f.stat().st_mtime)
        total = sum(f.stat().st_size for f in files)
        while files and total > self.max_bytes:
            f = files.pop(0)
            total -= f.stat().st_size
            f.unlink(missing_ok=True)
