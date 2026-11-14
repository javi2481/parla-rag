"""Bibliotecas locales: el mismo funcionamiento que library.py, pero el índice vive en nuestro servidor.

Se usa porque el índice de LlamaCloud necesita un plan pago (ver docs/bitacora.md, 13/11).
Todo es nativo de la familia LlamaIndex: el framework LlamaIndex (código abierto) arma el índice,
y Voyage AI hace los embeddings (voyage-4) y el reranking (rerank-2.5) con sus integraciones oficiales.

    Biblioteca "BYMA 3T26"
     ├── EEFF · Comunicado · Presentación    (corridas del wizard: se usa su parse, NO se vuelve a parsear)
     │      ↓ una página = un documento, con su número y la metadata de identidad
     ├── index/            el índice vectorial de LlamaIndex, guardado en la carpeta (carpeta como DB)
     ├── búsqueda          voyage-4 trae candidatos → rerank-2.5 los ordena por relevancia
     └── chat              pendiente: hace falta un modelo de lenguaje (Voyage no tiene)

Mismas funciones y mismas respuestas que library.py, así la pantalla de Bibliotecas no cambia.
"""
import asyncio
import os
from pathlib import Path

import nltk

from llama_index.core import Document, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.schema import QueryBundle
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.postprocessor.voyageai_rerank import VoyageAIRerank

from app.core.runs.store import RunStore, mark_done, mark_failed, mark_running, now, read_json, write_json

from .library import identity_metadata, stamp, summarize_search
from .settings import DocumentsSettings

# Metadata que se guarda con cada página pero no entra en el embedding (son IDs, no dicen nada del contenido).
NOT_EMBEDDED = ["corrida", "pagina"]

# Cuántos candidatos trae la búsqueda vectorial por cada resultado final que deja el reranker.
CANDIDATES_PER_RESULT = 3


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


# La carpeta data/ a partir de la carpeta-DB de bibliotecas (data/documents/libraries).
def data_dir_of(store: RunStore) -> Path:
    return store.root.parent.parent


# El modelo de embeddings de Voyage. Está en una función para que los tests lo reemplacen por uno falso.
def make_embed_model(settings: DocumentsSettings):
    return VoyageEmbedding(model_name=settings.library_embed_model, voyage_api_key=settings.voyage_api_key)


# El reranker de Voyage. También se reemplaza en los tests.
def make_reranker(settings: DocumentsSettings, top_n: int):
    return VoyageAIRerank(model=settings.library_rerank_model, api_key=settings.voyage_api_key, top_n=top_n)


# Revisa que esté la API key de Voyage antes de usarla.
def check_ready(settings: DocumentsSettings) -> None:
    if not settings.voyage_api_key:
        raise ValueError("Falta configurar VOYAGE_API_KEY en backend/.env.")


# Crea la biblioteca: solo la carpeta. El índice se arma al sincronizar.
async def create_library(client, store: RunStore, settings: DocumentsSettings, name: str, description: str = "") -> dict:
    check_ready(settings)
    library = store.create(name, [])
    library.update({
        "engine": "local",
        "description": description,
        "embed_model": settings.library_embed_model,
        "rerank_model": settings.library_rerank_model,
        "documents": [],
        "needs_sync": False,
        "steps": {"sync": {"state": "pending"}},
    })
    store.save(library)
    return library


# Agrega una corrida del wizard: copia a la biblioteca el Markdown de cada página de su parse, con la metadata de identidad.
# Así la biblioteca queda completa en su carpeta y se puede auditar qué texto se indexó.
async def add_document(client, store: RunStore, settings: DocumentsSettings, runs: RunStore, library: dict, run_id: str) -> dict:
    run = runs.get(run_id)
    if any(doc["run_id"] == run_id for doc in library["documents"]):
        raise ValueError("Ese documento ya está en la biblioteca.")
    if run["steps"].get("parse", {}).get("state") != "done":
        raise ValueError("Primero hay que terminar el paso Parse del documento.")

    response = read_json(runs.run_dir(run_id) / "2_parse" / "response.json")
    pages = [{"pagina": page["page_number"], "markdown": page.get("markdown") or ""}
             for page in (response.get("markdown") or {}).get("pages") or []]
    metadata = identity_metadata(runs, run)
    write_json(store.step_dir(library["id"], "documents") / f"{run_id}.json", {"metadata": metadata, "pages": pages})

    library["documents"].append({"run_id": run_id, "name": run["name"], "pages": len(pages), "metadata": metadata, "added_at": now()})
    library["needs_sync"] = True
    store.save(library)
    return library


# Saca un documento. Su texto deja de estar en el índice en la próxima sincronización.
async def remove_document(client, store: RunStore, settings: DocumentsSettings, library: dict, run_id: str) -> dict:
    document = next((doc for doc in library["documents"] if doc["run_id"] == run_id), None)
    if document is None:
        raise LookupError("Ese documento no está en la biblioteca.")
    library["documents"].remove(document)  # su copia en documents/ queda, para auditar qué se había indexado
    library.setdefault("historial", []).append({"removed": document, "at": now()})
    library["needs_sync"] = True
    store.save(library)
    return library


# Arma los documentos de LlamaIndex: una página de cada corrida = un documento, con su metadata.
def build_documents(store: RunStore, library: dict) -> list[Document]:
    documents = []
    for doc in library["documents"]:
        saved = read_json(store.run_dir(library["id"]) / "documents" / f"{doc['run_id']}.json")
        for page in saved["pages"]:
            if not page["markdown"].strip():
                continue
            documents.append(Document(
                text=page["markdown"],
                metadata={**saved["metadata"], "pagina": page["pagina"]},
                excluded_embed_metadata_keys=NOT_EMBEDDED,
                excluded_llm_metadata_keys=["corrida"],
            ))
    return documents


# Sincroniza: vuelve a armar el índice entero con los documentos actuales y lo guarda en la carpeta.
# Es local y responde en el momento (no hay job que consultar). Lo único que se paga son los tokens de Voyage.
async def start_sync(client, store: RunStore, settings: DocumentsSettings, library: dict) -> dict:
    check_ready(settings)
    prepare_nltk(data_dir_of(store))
    mark_running(library, "sync")
    store.save(library)
    try:
        documents = build_documents(store, library)
        store.archive(library["id"], "index")
        folder = store.step_dir(library["id"], "index")
        index = await asyncio.to_thread(VectorStoreIndex.from_documents, documents, embed_model=make_embed_model(settings))
        index.storage_context.persist(persist_dir=str(folder))
    except Exception as e:
        mark_failed(library, "sync", f"No se pudo armar el índice: {str(e)[:300]}")
        store.save(library)
        raise
    summary = summarize_sync(library, documents, len(index.docstore.docs), settings)
    write_json(store.step_dir(library["id"], f"syncs/{stamp()}") / "metrics.json", summary)
    mark_done(library, "sync", credits=None, metricas=summary["metricas"], interpretacion=summary["interpretacion"])
    library["needs_sync"] = False
    store.save(library)
    return library


# No hay nada que consultar: la sincronización local termina en el momento.
async def check_sync(client, store: RunStore, settings: DocumentsSettings, library: dict) -> dict:
    return library


# Las métricas y la interpretación de la sincronización local.
def summarize_sync(library: dict, documents: list[Document], chunks: int, settings: DocumentsSettings) -> dict:
    metricas = [
        {"label": "Documentos", "value": len(library["documents"])},
        {"label": "Páginas indexadas", "value": len(documents)},
        {"label": "Chunks", "value": chunks},
        {"label": "Embeddings", "value": settings.library_embed_model},
        {"label": "Reranker", "value": settings.library_rerank_model},
        {"label": "Créditos de LlamaCloud", "value": 0},
    ]
    interpretacion = [
        f"Se indexaron {len(documents)} páginas de {len(library['documents'])} documento(s) en {chunks} chunks, "
        "usando el parse que ya hizo el wizard: no se volvió a parsear nada.",
        "El índice está guardado en la carpeta de la biblioteca (index/). Los embeddings los hizo Voyage AI; "
        "los primeros 200 millones de tokens son gratis.",
    ]
    return {"metricas": metricas, "interpretacion": interpretacion}


# Pasa los filtros con el formato de LlamaCloud ({"tipo": {"operator": "eq", "value": "x"}}) a filtros de LlamaIndex.
# Solo se acepta "eq", que es lo que soporta el índice local.
def to_filters(filters: dict | None) -> MetadataFilters | None:
    if not filters:
        return None
    exact = []
    for key, condition in filters.items():
        if condition.get("operator", "eq") != "eq":
            raise ValueError("La biblioteca local solo filtra por igualdad (eq).")
        exact.append(ExactMatchFilter(key=key, value=condition["value"]))
    return MetadataFilters(filters=exact)


# Una búsqueda de prueba: voyage-4 trae candidatos y rerank-2.5 deja los más relevantes.
# Devuelve lo mismo que la búsqueda de LlamaCloud (content, score, rerank_score, metadata, static_fields).
async def search(client, store: RunStore, settings: DocumentsSettings, library: dict, query: str, top_k: int = 8, filters: dict | None = None) -> dict:
    check_ready(settings)
    folder = store.run_dir(library["id"]) / "index"
    if not folder.is_dir():
        raise ValueError("Primero hay que sincronizar la biblioteca.")
    prepare_nltk(data_dir_of(store))

    def run() -> list:
        storage = StorageContext.from_defaults(persist_dir=str(folder))
        index = load_index_from_storage(storage, embed_model=make_embed_model(settings))
        retriever = index.as_retriever(similarity_top_k=top_k * CANDIDATES_PER_RESULT, filters=to_filters(filters))
        candidates = retriever.retrieve(query)
        vector_scores = {node.node.node_id: node.score for node in candidates}
        reranked = make_reranker(settings, top_k).postprocess_nodes(candidates, QueryBundle(query))
        return [(node, vector_scores.get(node.node.node_id)) for node in reranked]

    results = []
    for node, vector_score in await asyncio.to_thread(run):
        page = node.node.metadata.get("pagina")
        results.append({
            "content": node.node.get_content(),
            "score": vector_score,
            "rerank_score": node.score,
            "metadata": node.node.metadata,
            "static_fields": {"page_range_start": page, "page_range_end": page},
        })
    request = {"query": query, "top_k": top_k, "filters": filters,
               "embed_model": settings.library_embed_model, "rerank_model": settings.library_rerank_model}
    response = {"results": results}
    result = {"at": now(), "request": request, "response": response, **summarize_search(response)}
    write_json(store.step_dir(library["id"], "searches") / f"{stamp()}.json", result)
    return result


# El chat necesita un modelo de lenguaje que escriba las respuestas, y Voyage AI no tiene. Queda pendiente.
async def chat_turn(client, store: RunStore, settings: DocumentsSettings, library: dict, prompt: str):
    raise ValueError("El chat de la biblioteca local todavía no tiene un modelo de lenguaje configurado.")
    yield  # para que sea un generador como el de LlamaCloud


# Borra la biblioteca: es solo la carpeta, no hay nada en LlamaCloud.
async def delete_library(client, store: RunStore, settings: DocumentsSettings, library: dict) -> None:
    store.delete(library["id"])
