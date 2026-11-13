"""Configuración del pipeline de documentos (LlamaCloud). Se lee de backend/.env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DocumentsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llama_cloud_api_key: str = ""
    # Región EU: https://api.cloud.eu.llamaindex.ai
    llama_cloud_base_url: str = "https://api.cloud.llamaindex.ai"

    # Tier de LlamaExtract (créditos por página): cost_effective 8 · agentic 25 · agentic_plus 60 · turbo 35
    extract_tier: str = "agentic"
    # Versión del extractor: "latest" o una fija (ej. "2.5") para resultados reproducibles.
    extract_version: str = "latest"

    # Cantidad máxima de extracciones por IP por día (0 = sin límite).
    documents_daily_limit: int = 50

    # Dice si el pipeline está listo para usarse (o sea, si hay API key).
    @property
    def ready(self) -> bool:
        return bool(self.llama_cloud_api_key)


# Lee la configuración una sola vez y la reutiliza.
@lru_cache
def get_documents_settings() -> DocumentsSettings:
    return DocumentsSettings()
