"""Configuración general de la app (lo que no pertenece a ningún pipeline en particular).

Cada pipeline tiene su propio settings.py con sus API keys y opciones.
Todos leen el mismo archivo backend/.env.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Orígenes permitidos para CORS, separados por coma.
    cors_origins: str = "http://localhost:5173"

    # Carpeta donde se guardan los datos (simula una base de datos).
    data_dir: str = "data"

    # Devuelve la lista de orígenes CORS, sin espacios ni elementos vacíos.
    def cors_origin_list(self) -> list[str]:
        origins = []
        for origin in self.cors_origins.split(","):
            origin = origin.strip()
            if origin:
                origins.append(origin)
        return origins


# Lee la configuración una sola vez y la reutiliza en toda la app.
@lru_cache
def get_core_settings() -> CoreSettings:
    return CoreSettings()
