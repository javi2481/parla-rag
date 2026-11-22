"""Los modelos que usa el motor local: embeddings y reranker de Voyage AI, y el modelo de lenguaje de OpenAI.

Están en funciones para que los tests los reemplacen por modelos falsos (sin red ni créditos). Por eso el resto
del código los llama así: ai_models.make_llm(settings), y no los importa sueltos.
Acá también se prepara NLTK, la librería con la que LlamaIndex corta el texto en oraciones.
"""
import os
from pathlib import Path

import nltk
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.postprocessor.voyageai_rerank import VoyageAIRerank

from app.core.runs.store import RunStore
from app.pipelines.documents.settings import DocumentsSettings


# Revisa que esté la API key de Voyage antes de usarla.
def check_ready(settings: DocumentsSettings) -> None:
    if not settings.voyage_api_key:
        raise ValueError("Falta configurar VOYAGE_API_KEY en backend/.env.")


# El modelo de embeddings de Voyage: convierte cada página (y cada pregunta) en un vector.
def make_embed_model(settings: DocumentsSettings):
    return VoyageEmbedding(model_name=settings.library_embed_model, voyage_api_key=settings.voyage_api_key)


# El modelo de lenguaje del chat (OpenAI). include_usage hace que OpenAI mande los tokens usados al final de la respuesta.
def make_llm(settings: DocumentsSettings):
    return OpenAI(model=settings.library_chat_model, api_key=settings.openai_api_key,
                  reasoning_effort=settings.library_reasoning_effort,
                  additional_kwargs={"stream_options": {"include_usage": True}})


# El reranker de Voyage: de los candidatos de la búsqueda, deja los top_n más relevantes para la pregunta.
def make_reranker(settings: DocumentsSettings, top_n: int):
    return VoyageAIRerank(model=settings.library_rerank_model, api_key=settings.voyage_api_key, top_n=top_n)


# La carpeta data/ a partir de la carpeta-DB de bibliotecas (data/documents/libraries).
def data_dir_of(store: RunStore) -> Path:
    return store.root.parent.parent


# Prepara los datos de NLTK (la librería con la que LlamaIndex corta el texto en oraciones) en data/nltk/.
# NLTK se niega a leer carpetas que otros usuarios pueden modificar o archivos con hardlinks (como los que deja uv
# dentro de .venv), por seguridad. Por eso se bajan a una carpeta nuestra, con permisos privados (umask 022).
def prepare_nltk(data_dir: Path) -> None:
    folder = (data_dir / "nltk").resolve()
    os.environ["NLTK_DATA"] = str(folder)
    if (folder / "corpora" / "stopwords").is_dir() and (folder / "tokenizers" / "punkt_tab").is_dir():
        return
    previous = os.umask(0o022)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        folder.chmod(0o755)
        for package in ("stopwords", "punkt_tab"):
            nltk.download(package, download_dir=str(folder), quiet=True)
    finally:
        os.umask(previous)
