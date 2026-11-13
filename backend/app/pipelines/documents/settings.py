"""Configuración del pipeline de documentos (LlamaCloud). Se lee de backend/.env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DocumentsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llama_cloud_api_key: str = ""
    # Región EU: https://api.cloud.eu.llamaindex.ai
    llama_cloud_base_url: str = "https://api.cloud.llamaindex.ai"

    # Parse: tier (fast · cost_effective · agentic · agentic_plus) y versión fija,
    # para que el mismo documento dé el mismo resultado en cada clase.
    parse_tier: str = "agentic"
    parse_version: str = "2026-10-16"
    # Cantidad máxima de páginas que se parsean de un documento.
    parse_max_pages: int = 100

    # Tamaño máximo del archivo que se puede subir, en megas.
    max_upload_mb: int = 50

    # Cantidad máxima de documentos que se pueden subir por IP por día (0 = sin límite).
    documents_daily_limit: int = 0

    # Dice si el pipeline está listo para usarse (o sea, si hay API key).
    @property
    def ready(self) -> bool:
        return bool(self.llama_cloud_api_key)


# Lee la configuración una sola vez y la reutiliza.
@lru_cache
def get_documents_settings() -> DocumentsSettings:
    return DocumentsSettings()
