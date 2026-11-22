"""Armar el índice de una biblioteca local: de las páginas del parse a los chunks y de los chunks a los vectores.

    agregar      copia el Markdown de cada página del parse a documents/<corrida>.json (no se vuelve a parsear)
    sincronizar  una página = un Document de LlamaIndex → build_nodes los corta en chunks
                 → VectorStoreIndex con los embeddings de voyage-4 → se guarda en index/
"""
import asyncio

from llama_index.core import (
    Document,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.schema import TextNode

from app.core.runs.store import (
    RunStore,
    mark_done,
    mark_failed,
    mark_running,
    now,
    read_json,
    stamp,
    write_json,
)
from app.pipelines.documents.settings import DocumentsSettings

from ..document_metadata import identity_metadata
from . import ai_models

# Metadata que se guarda con cada página pero no entra en el embedding (son IDs, no dicen nada del contenido).
NOT_EMBEDDED = ["corrida", "pagina"]


# Crea la biblioteca: solo la carpeta. El índice se arma al sincronizar.
async def create_library(client, store: RunStore, settings: DocumentsSettings, name: str, description: str = "") -> dict:
    ai_models.check_ready(settings)
    library = store.create(name, [])
    library.update({
        "engine": "local",
        "description": description,
        "embed_model": settings.library_embed_model,
        "rerank_model": settings.library_rerank_model,
        "splitter": settings.library_splitter,
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


# Corta las páginas en chunks (nodos de LlamaIndex) según el separador de la biblioteca.
#   - "oraciones": SentenceSplitter, el de por defecto de LlamaIndex (chunks de hasta 1024 tokens). Puede partir una tabla
#     y dejar las filas sin su encabezado (las unidades, si es histórico o ajustado…).
#   - "markdown": MarkdownNodeParser, corta por títulos del Markdown: cada tabla queda entera con su encabezado.
#   - "pagina": no corta nada, cada página es un chunk. Respeta las tablas que LlamaParse unió entre páginas
#     (merge_continued_tables las pone enteras en la primera página) y la cita por página queda exacta.
def build_nodes(library: dict, documents: list[Document]) -> list:
    # Las bibliotecas creadas antes de poder elegir el corte no lo tienen guardado: se armaron con "oraciones".
    splitter = library.get("splitter", "oraciones")
    if splitter == "pagina":
        # Un TextNode por página, con el mismo texto y la misma metadata (el reranker de Voyage pide TextNode).
        return [TextNode(text=doc.text, metadata=doc.metadata,
                         excluded_embed_metadata_keys=doc.excluded_embed_metadata_keys,
                         excluded_llm_metadata_keys=doc.excluded_llm_metadata_keys) for doc in documents]
    if splitter == "markdown":
        return MarkdownNodeParser().get_nodes_from_documents(documents)
    return SentenceSplitter().get_nodes_from_documents(documents)


# Sincroniza: vuelve a armar el índice entero con los documentos actuales y lo guarda en la carpeta.
# Es local y responde en el momento (no hay job que consultar). Lo único que se paga son los tokens de Voyage.
async def start_sync(client, store: RunStore, settings: DocumentsSettings, library: dict) -> dict:
    ai_models.check_ready(settings)
    ai_models.prepare_nltk(ai_models.data_dir_of(store))
    mark_running(library, "sync")
    store.save(library)
    try:
        documents = build_documents(store, library)
        store.archive(library["id"], "index")
        folder = store.step_dir(library["id"], "index")
        nodes = build_nodes(library, documents)
        index = await asyncio.to_thread(VectorStoreIndex, nodes, embed_model=ai_models.make_embed_model(settings))
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


# "1 página", "3 páginas".
def plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


# Las métricas y la interpretación de la sincronización local.
def summarize_sync(library: dict, documents: list[Document], chunks: int, settings: DocumentsSettings) -> dict:
    metricas = [
        {"label": "Documentos", "value": len(library["documents"])},
        {"label": "Páginas indexadas", "value": len(documents)},
        {"label": "Chunks", "value": chunks},
        {"label": "Separador", "value": library.get("splitter", "oraciones")},
        {"label": "Embeddings", "value": settings.library_embed_model},
        {"label": "Reranker", "value": settings.library_rerank_model},
        {"label": "Créditos de LlamaCloud", "value": 0},
    ]
    interpretacion = [
        (f"Se indexaron {plural(len(documents), 'página', 'páginas')} de {plural(len(library['documents']), 'documento', 'documentos')} "
        f"en {plural(chunks, 'chunk', 'chunks')}, "
        "usando el parse que ya hizo el wizard: no se volvió a parsear nada."),
        ("El índice está guardado en la carpeta de la biblioteca (index/). Los embeddings los hizo Voyage AI; "
        "los primeros 200 millones de tokens son gratis."),
    ]
    return {"metricas": metricas, "interpretacion": interpretacion}


# Abre el índice guardado en la carpeta de la biblioteca.
def load_index(store: RunStore, settings: DocumentsSettings, library: dict) -> VectorStoreIndex:
    folder = store.run_dir(library["id"]) / "index"
    if not folder.is_dir():
        raise ValueError("Primero hay que sincronizar la biblioteca.")
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=str(folder)),
                                   embed_model=ai_models.make_embed_model(settings))


# Borra la biblioteca: es solo la carpeta, no hay nada en LlamaCloud.
async def delete_library(client, store: RunStore, settings: DocumentsSettings, library: dict) -> None:
    store.delete(library["id"])
