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
    # No hay máximo de páginas a propósito: un parse limitado (max_pages) no se puede usar
    # después en Split (ver docs/bitacora.md, 13/11). El límite real es el tamaño del archivo.

    # Tamaño máximo del archivo que se puede subir, en megas.
    max_upload_mb: int = 50

    # Bibliotecas: "local" (LlamaIndex + Voyage AI, en nuestro servidor) o "llamacloud" (necesita un plan pago).
    library_engine: str = "local"
    # Voyage AI: embeddings y reranker de las bibliotecas locales.
    voyage_api_key: str = ""
    library_embed_model: str = "voyage-4"
    library_rerank_model: str = "rerank-2.5"
    # Cómo se cortan las páginas en chunks antes de los embeddings (los dos son nativos de LlamaIndex):
    # "pagina" (no corta: cada página es un chunk; es el que mejor dio en los evals de búsqueda y respuestas),
    # "oraciones" (SentenceSplitter, el de por defecto de LlamaIndex) o "markdown" (MarkdownNodeParser: corta por títulos).
    library_splitter: str = "pagina"
    # OpenAI: el modelo de lenguaje que escribe las respuestas del chat de las bibliotecas locales.
    # gpt-5-nano es el más barato de OpenAI. Es un modelo de razonamiento: "minimal" casi no razona,
    # así responde rápido y gasta menos tokens (alcanza para redactar con las páginas que trae la búsqueda).
    openai_api_key: str = ""
    library_chat_model: str = "gpt-5-nano"
    library_reasoning_effort: str = "minimal"
    # Cuántas páginas (las mejores según el reranker) se le pasan al modelo en cada pregunta.
    library_chat_top_k: int = 6

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
