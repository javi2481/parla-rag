"""Bibliotecas locales: el mismo funcionamiento que library.py, pero el índice vive en nuestro servidor.

Se usa porque el índice de LlamaCloud necesita un plan pago (ver docs/bitacora.md, 13/11).
Todo es nativo de la familia LlamaIndex: el framework LlamaIndex (código abierto) arma el índice,
Voyage AI hace los embeddings (voyage-4) y el reranking (rerank-2.5), y OpenAI escribe las respuestas
del chat (gpt-5-nano). Las dos con sus integraciones oficiales de LlamaIndex.

    Biblioteca "Aprendizaje Automático II"
     ├── Clase 01 · Clase 02 · … · Clase 13  (corridas del wizard: se usa su parse, NO se vuelve a parsear)
     │      ↓ una página = un documento, con su número y la metadata de identidad
     ├── index/            el índice vectorial de LlamaIndex, guardado en la carpeta (carpeta como DB)
     ├── búsqueda          voyage-4 trae candidatos → rerank-2.5 los ordena por relevancia
     └── chat              el chat engine de LlamaIndex: busca como arriba y OpenAI responde citando documento y página

Mismas funciones y mismas respuestas que library.py, así la pantalla de Bibliotecas no cambia.
"""
import asyncio
import json
import logging
import os
from pathlib import Path

import nltk
from llama_index.core import (
    Document,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.instrumentation import get_dispatcher
from llama_index.core.instrumentation.event_handlers import BaseEventHandler
from llama_index.core.instrumentation.events.llm import (
    LLMChatEndEvent,
    LLMCompletionEndEvent,
)
from llama_index.core.instrumentation.events.retrieval import RetrievalEndEvent
from llama_index.core.llms import ChatMessage
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.schema import QueryBundle, TextNode
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.postprocessor.voyageai_rerank import VoyageAIRerank
from pydantic import Field

from app.core.runs.store import (
    RunStore,
    mark_done,
    mark_failed,
    mark_running,
    now,
    read_json,
    write_json,
)

from .library import identity_metadata, stamp, summarize_search
from .settings import DocumentsSettings

# Metadata que se guarda con cada página pero no entra en el embedding (son IDs, no dicen nada del contenido).
NOT_EMBEDDED = ["corrida", "pagina"]

log = logging.getLogger(__name__)

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


# El modelo de lenguaje del chat (OpenAI). include_usage hace que OpenAI mande los tokens usados al final de la respuesta.
def make_llm(settings: DocumentsSettings):
    return OpenAI(model=settings.library_chat_model, api_key=settings.openai_api_key,
                  reasoning_effort=settings.library_reasoning_effort,
                  additional_kwargs={"stream_options": {"include_usage": True}})


# El reranker de Voyage. También se reemplaza en los tests.
def make_reranker(settings: DocumentsSettings, top_n: int):
    return VoyageAIRerank(model=settings.library_rerank_model, api_key=settings.voyage_api_key, top_n=top_n)


# La búsqueda por vectores que comparten el chat, la búsqueda de prueba y los evals (así los evals miden lo mismo).
# Trae "candidates" páginas (por defecto, top_k × 3) para que después el reranker deje las mejores.
# Con library_retrieval_mode = "mmr" usa el MMR nativo del índice de LlamaIndex: candidatos parecidos pero distintos.
def make_retriever(index: VectorStoreIndex, settings: DocumentsSettings, candidates: int | None = None,
                   filters: MetadataFilters | None = None):
    mode = settings.library_retrieval_mode
    if mode not in ("default", "mmr"):
        raise ValueError(f'El modo de búsqueda "{mode}" no existe: tiene que ser "default" o "mmr".')
    extra = {"vector_store_kwargs": {"mmr_threshold": settings.library_mmr_threshold}} if mode == "mmr" else {}
    return index.as_retriever(similarity_top_k=candidates or settings.library_chat_top_k * CANDIDATES_PER_RESULT,
                              filters=filters, vector_store_query_mode=mode, **extra)


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
# Las bibliotecas creadas antes de esta opción usaban "oraciones".
#   - "oraciones": SentenceSplitter, el de por defecto de LlamaIndex (chunks de hasta 1024 tokens). Puede partir una tabla
#     y dejar las filas sin su encabezado (las unidades, si es histórico o ajustado…).
#   - "markdown": MarkdownNodeParser, corta por títulos del Markdown: cada tabla queda entera con su encabezado.
#   - "pagina": no corta nada, cada página es un chunk. Respeta las tablas que LlamaParse unió entre páginas
#     (merge_continued_tables las pone enteras en la primera página) y la cita por página queda exacta.
def build_nodes(library: dict, documents: list[Document]) -> list:
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
    check_ready(settings)
    prepare_nltk(data_dir_of(store))
    mark_running(library, "sync")
    store.save(library)
    try:
        documents = build_documents(store, library)
        store.archive(library["id"], "index")
        folder = store.step_dir(library["id"], "index")
        nodes = build_nodes(library, documents)
        index = await asyncio.to_thread(VectorStoreIndex, nodes, embed_model=make_embed_model(settings))
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


# Pasa los filtros con el formato de LlamaCloud ({"tipo": {"operator": "eq", "value": "x"}}) a filtros de LlamaIndex.
# Solo se acepta "eq", que es lo que soporta el índice local. Si el filtro viene mal armado,
# avisa con un ValueError (la ruta lo devuelve como 409 con el formato esperado) en vez de romper con un 500.
def to_filters(filters: dict | None) -> MetadataFilters | None:
    if not filters:
        return None
    exact = []
    for key, condition in filters.items():
        if not isinstance(condition, dict) or "value" not in condition:
            raise ValueError(f'El filtro "{key}" está mal armado. El formato es '
                             f'{{"{key}": {{"operator": "eq", "value": ...}}}}.')
        if condition.get("operator", "eq") != "eq":
            raise ValueError("La biblioteca local solo filtra por igualdad (eq).")
        exact.append(ExactMatchFilter(key=key, value=condition["value"]))
    return MetadataFilters(filters=exact)


# Abre el índice guardado en la carpeta de la biblioteca.
def load_index(store: RunStore, settings: DocumentsSettings, library: dict) -> VectorStoreIndex:
    folder = store.run_dir(library["id"]) / "index"
    if not folder.is_dir():
        raise ValueError("Primero hay que sincronizar la biblioteca.")
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=str(folder)), embed_model=make_embed_model(settings))


# Una búsqueda de prueba: voyage-4 trae candidatos y rerank-2.5 deja los más relevantes.
# Devuelve lo mismo que la búsqueda de LlamaCloud (content, score, rerank_score, metadata, static_fields).
async def search(client, store: RunStore, settings: DocumentsSettings, library: dict, query: str, top_k: int = 8, filters: dict | None = None) -> dict:
    check_ready(settings)
    metadata_filters = to_filters(filters)  # primero se validan, antes de abrir el índice
    prepare_nltk(data_dir_of(store))
    index = load_index(store, settings, library)

    def run() -> list:
        retriever = make_retriever(index, settings, candidates=top_k * CANDIDATES_PER_RESULT, filters=metadata_filters)
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


# Las instrucciones del chat: responder solo con lo que dicen los documentos y citar de dónde sale cada dato.
SYSTEM_PROMPT = """Sos un asistente que responde preguntas sobre los documentos de una biblioteca.
Respondé en español rioplatense, tratando de vos al usuario.
Usá SOLO la información de los fragmentos que se te pasan. Si lo que te preguntan no está en los fragmentos,
decí que no está en los documentos de la biblioteca: no inventes ni completes con lo que sabés por tu cuenta,
y no ofrezcas buscar en otros documentos (ya se buscó en toda la biblioteca).
Si la pregunta involucra varios temas o clases, relacioná lo que dice cada documento (en qué se parecen y en qué se diferencian) y citá cada uno.
Después de cada dato, citá de dónde salió con el nombre del documento y la página, así: (07 Clasificación de imágenes.pdf, pág. 12).
Copiá los números tal como aparecen, con su unidad y su moneda."""

# Cómo se le pasan los fragmentos al modelo. Cada fragmento es una página y empieza con su metadata (nombre, tipo, página).
CONTEXT_PROMPT = """Estos son los fragmentos de la biblioteca más relevantes para la pregunta.
Cada uno empieza con su metadata: el nombre del documento, su tipo y la página.

{context_str}

Respondé la pregunta del usuario usando solo estos fragmentos y citando documento y página."""

# Cuando ya hubo preguntas antes, el modelo reescribe la nueva para que se entienda sola (es la que se busca en el índice).
CONDENSE_PROMPT = """Dada esta conversación y una pregunta nueva, reescribí la pregunta nueva para que se entienda sola,
sin necesitar la conversación. Respondé solo con la pregunta reescrita.

Conversación:
{chat_history}

Pregunta nueva: {question}
Pregunta reescrita:"""


# Escucha lo que hace LlamaIndex durante un turno (instrumentación nativa): qué buscó y cada llamada al modelo con sus tokens.
class TurnRecorder(BaseEventHandler):
    searches: list = Field(default_factory=list)
    llm_calls: list = Field(default_factory=list)

    def handle(self, event, **kwargs) -> None:
        if isinstance(event, RetrievalEndEvent):
            query = event.str_or_query_bundle
            self.searches.append({"consulta": query.query_str if isinstance(query, QueryBundle) else str(query),
                                  "candidatos": len(event.nodes)})
        elif isinstance(event, LLMCompletionEndEvent):  # la que reescribe la pregunta usa "complete"
            self.llm_calls.append({"tipo": "completion", "mensajes": [{"rol": "user", "contenido": event.prompt}],
                                   "respuesta": event.response.text, "usage": usage_of(event.response)})
        elif isinstance(event, LLMChatEndEvent) and event.response is not None:  # la que responde usa "chat"
            self.llm_calls.append({"tipo": "chat", "mensajes": [{"rol": m.role.value, "contenido": m.content} for m in event.messages],
                                   "respuesta": event.response.message.content, "usage": usage_of(event.response)})


# Los tokens que informó el modelo en su respuesta (OpenAI los manda en "usage").
def usage_of(response) -> dict | None:
    usage = getattr(response.raw, "usage", None) if response.raw is not None else None
    return usage.model_dump() if hasattr(usage, "model_dump") else usage


# Suma los tokens de todas las llamadas al modelo del turno (la que reescribe la pregunta y la que responde).
# Las llamadas sin "usage" no suman (el modelo falso de los tests no lo informa).
def total_usage(llm_calls: list, model: str) -> dict:
    usages = [call["usage"] or {} for call in llm_calls]
    reasoning = sum((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0 for u in usages)
    return {
        "modelo": model,
        "llamadas_al_modelo": sum(1 for u in usages if u),
        "tokens_de_entrada": sum(u.get("prompt_tokens") or 0 for u in usages),
        "tokens_de_salida": sum(u.get("completion_tokens") or 0 for u in usages),
        "de_esos_razonamiento": reasoning,
        "tokens_en_cache": sum((u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0 for u in usages),
    }


# Las preguntas y respuestas anteriores del chat, para que el modelo entienda preguntas como "¿y el trimestre anterior?".
def chat_history(folder: Path) -> list[ChatMessage]:
    history = []
    for path in sorted(folder.glob("turno_*.json"), key=lambda p: int(p.stem.split("_")[1])):
        turn = read_json(path)
        if turn.get("answer"):
            history += [ChatMessage(role="user", content=turn["prompt"]), ChatMessage(role="assistant", content=turn["answer"])]
    return history


# Una línea de Server-Sent Events, el mismo formato que manda el chat de LlamaCloud.
def sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


# Arma el chat engine de LlamaIndex (condense_plus_context) con sus instrucciones, el buscador y el reranker.
# Lo usan el chat y los evals, así los evals miden exactamente el mismo chat.
# "candidates" es cuántos candidatos trae la búsqueda por vectores antes del reranker (por defecto, top_k × 3).
def make_chat_engine(index: VectorStoreIndex, settings: DocumentsSettings, history: list[ChatMessage],
                     candidates: int | None = None) -> CondensePlusContextChatEngine:
    top_k = settings.library_chat_top_k
    return CondensePlusContextChatEngine.from_defaults(
        retriever=make_retriever(index, settings, candidates),
        llm=make_llm(settings),
        chat_history=history,
        system_prompt=SYSTEM_PROMPT,
        context_prompt=CONTEXT_PROMPT,
        condense_prompt=CONDENSE_PROMPT,
        node_postprocessors=[make_reranker(settings, top_k)],
    )


# Un turno de chat con el chat engine de LlamaIndex (condense_plus_context):
#   1. si ya hubo preguntas, OpenAI reescribe la nueva para que se entienda sola;
#   2. voyage-4 busca candidatos y rerank-2.5 deja las mejores páginas;
#   3. OpenAI responde con esas páginas, citando documento y página. La respuesta llega en vivo.
# Manda los mismos eventos que el chat de LlamaCloud (tool_call, tool_result, text_delta, stop) y guarda todo el turno.
async def chat_turn(client, store: RunStore, settings: DocumentsSettings, library: dict, prompt: str):
    check_ready(settings)
    if not settings.openai_api_key:
        raise ValueError("Falta configurar OPENAI_API_KEY en backend/.env.")
    prepare_nltk(data_dir_of(store))
    index = load_index(store, settings, library)
    folder = store.step_dir(library["id"], "chats/local", reset=False)
    history = chat_history(folder)
    top_k = settings.library_chat_top_k
    engine = make_chat_engine(index, settings, history)
    recorder = TurnRecorder()
    dispatcher = get_dispatcher()
    dispatcher.add_event_handler(recorder)
    events, answer, sources, error = [], "", [], None
    try:
        response = await engine.astream_chat(prompt)
        search_call = {"type": "tool_call", "call_id": "busqueda", "name": "buscar_en_la_biblioteca",
                       "arguments": {"busquedas": recorder.searches, "paginas_para_el_modelo": top_k}}
        sources = [{"documento": node.node.metadata.get("nombre"), "pagina": node.node.metadata.get("pagina"),
                    "rerank_score": node.score, "metadata": node.node.metadata, "texto": node.node.get_content()}
                   for node in response.source_nodes]
        for event in (search_call, {"type": "tool_result", "call_id": "busqueda", "result": sources}):
            events.append(event)
            yield sse(event)
        async for token in response.async_response_gen():
            answer += token
            event = {"type": "text_delta", "content": token}
            events.append(event)
            yield sse(event)
    except Exception as e:  # el error se muestra en el chat y queda guardado en el turno
        log.exception("Chat local")
        error = str(e)[:500]
        events.append({"type": "error", "content": f"No se pudo responder: {error}"})
        yield sse(events[-1])
    finally:
        dispatcher.event_handlers.remove(recorder)

    usage = total_usage(recorder.llm_calls, settings.library_chat_model)
    stop = {"type": "stop", "usage": usage}
    events.append(stop)
    yield sse(stop)
    number = len(list(folder.glob("turno_*.json"))) + 1
    write_json(folder / f"turno_{number}.json", {
        "at": now(), "prompt": prompt, "answer": answer, "error": error, "engine": "local",
        "request": {"chat_model": settings.library_chat_model, "embed_model": settings.library_embed_model,
                    "rerank_model": settings.library_rerank_model, "top_k": top_k, "historial": len(history) // 2},
        "searches": recorder.searches, "sources": sources, "llm_calls": recorder.llm_calls, "usage": usage,
        "events_raw": [sse(event).strip() for event in events],
    })


# Borra la biblioteca: es solo la carpeta, no hay nada en LlamaCloud.
async def delete_library(client, store: RunStore, settings: DocumentsSettings, library: dict) -> None:
    store.delete(library["id"])
