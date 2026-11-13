"""Caché en disco de los audios de texto a voz.

La clave incluye el texto, el modelo, la voz y los ajustes: si cambia cualquiera, se genera de nuevo.
Sobrevive a los reinicios del servidor. Cuando se pasa del tamaño máximo, borra los audios menos usados.
"""
import hashlib
import json
import os
from pathlib import Path


class AudioCache:
    # Prepara la caché en `directory`, con un tamaño máximo en megas (0 = caché apagada).
    def __init__(self, directory: str | Path, max_mb: int):
        self.dir = Path(directory)
        self.max_bytes = max_mb * 1024 * 1024

    # Arma una clave única a partir de todas las partes que definen el audio.
    @staticmethod
    def key(**parts: object) -> str:
        text = json.dumps(parts, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(text.encode()).hexdigest()

    # Devuelve el audio guardado con esa clave, o None si no está.
    def get(self, key: str) -> bytes | None:
        path = self.dir / f"{key}.mp3"
        try:
            data = path.read_bytes()
        except OSError:
            return None
        os.utime(path)  # lo marca como usado recién, para no borrarlo pronto
        return data

    # Guarda un audio. Si falla (disco lleno, permisos), no pasa nada: la próxima vez se paga de nuevo.
    def put(self, key: str, data: bytes) -> None:
        if self.max_bytes <= 0:
            return
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            # Se escribe primero en un temporal para no dejar nunca un mp3 a medias.
            tmp = self.dir / f"{key}.tmp"
            tmp.write_bytes(data)
            tmp.replace(self.dir / f"{key}.mp3")
            self._remove_oldest()
        except OSError:
            pass

    # Borra los audios menos usados hasta que la caché quede por debajo del máximo.
    def _remove_oldest(self) -> None:
        files = sorted(self.dir.glob("*.mp3"), key=lambda f: f.stat().st_mtime)
        total = sum(f.stat().st_size for f in files)
        while files and total > self.max_bytes:
            oldest = files.pop(0)
            total -= oldest.stat().st_size
            oldest.unlink(missing_ok=True)
