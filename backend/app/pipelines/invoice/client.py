"""Cliente del SDK oficial de LlamaCloud (paquete `llama-cloud`). Reintenta 429/5xx solo."""
from llama_cloud import AsyncLlamaCloud

from app.core.config import Settings


def make_client(s: Settings) -> AsyncLlamaCloud:
    return AsyncLlamaCloud(api_key=s.llama_cloud_api_key, base_url=s.llama_cloud_base_url.rstrip("/"), timeout=60, max_retries=3)
