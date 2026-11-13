"""Cliente del SDK oficial de LlamaCloud (paquete `llama-cloud`).

El SDK ya reintenta solo cuando LlamaCloud responde 429 (muchos pedidos) o 5xx (error del servidor).
"""
from llama_cloud import AsyncLlamaCloud

from .settings import DocumentsSettings


# Crea el cliente de LlamaCloud con la API key y la región configuradas.
def make_client(settings: DocumentsSettings) -> AsyncLlamaCloud:
    return AsyncLlamaCloud(
        api_key=settings.llama_cloud_api_key,
        base_url=settings.llama_cloud_base_url.rstrip("/"),
        timeout=60,
        max_retries=3,
    )
