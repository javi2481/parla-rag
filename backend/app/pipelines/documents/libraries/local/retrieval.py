"""Buscar en una biblioteca local: qué páginas le llegan al modelo para responder.

    candidatos   "hibrida" (vectores + BM25), "default" (solo vectores) o "mmr" (vectores variados)
    reranker     rerank-2.5 de Voyage deja las mejores (6 en el chat)
    filtros      acotan la búsqueda por metadata (por ejemplo, una clase)

Lo usan el chat, el agente, la búsqueda de prueba y los evals, así todos miden la misma búsqueda.
"""
import asyncio

import Stemmer
from llama_index.core import VectorStoreIndex
from llama_index.core.llms import MockLLM
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.schema import QueryBundle
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.retrievers.bm25 import BM25Retriever

from app.core.runs.store import RunStore, now, stamp, write_json
from app.pipelines.documents.settings import DocumentsSettings

from ..document_metadata import summarize_search
from . import ai_models
from .index_builder import load_index

# Cuántos candidatos trae la búsqueda por cada resultado final que deja el reranker.
CANDIDATES_PER_RESULT = 3


# La búsqueda que comparten el chat, la búsqueda de prueba y los evals (así los evals miden lo mismo).
# Trae "candidates" páginas (por defecto, top_k × 3) para que después el reranker deje las mejores.
# Con library_retrieval_mode = "mmr" usa el MMR nativo del índice de LlamaIndex: candidatos parecidos pero distintos.
# Con "hibrida" junta los vectores con BM25 (ver make_hybrid_retriever).
def make_retriever(index: VectorStoreIndex, settings: DocumentsSettings, candidates: int | None = None,
                   filters: MetadataFilters | None = None):
    mode = settings.library_retrieval_mode
    if mode not in ("default", "mmr", "hibrida"):
        raise ValueError(f'El modo de búsqueda "{mode}" no existe: tiene que ser "default", "mmr" o "hibrida".')
    candidates = candidates or settings.library_chat_top_k * CANDIDATES_PER_RESULT
    if mode == "hibrida":
        return make_hybrid_retriever(index, candidates, filters)
    extra = {"vector_store_kwargs": {"mmr_threshold": settings.library_mmr_threshold}} if mode == "mmr" else {}
    return index.as_retriever(similarity_top_k=candidates, filters=filters, vector_store_query_mode=mode, **extra)


# La búsqueda híbrida: vectores (voyage-4, entiende el sentido aunque cambien las palabras) + BM25 (busca las
# palabras exactas, como "Bolukbasi" o "GRU", que los vectores a veces pierden). BM25 corta en palabras en español
# y les saca la terminación ("redes" y "red" cuentan igual). Se arma en el momento con las páginas del índice: son pocas.
# QueryFusionRetriever junta las dos listas con reciprocal rank fusion: suben las páginas que están arriba en las dos.
# num_queries=1 busca la pregunta tal cual: no le pide a un modelo que invente otras, por eso alcanza con MockLLM.
# Con filtros, BM25 se arma solo con las páginas que los cumplen: su opción "filters" no las saca, les pone
# puntaje 0 y las sigue devolviendo. Si ninguna página cumple, queda la búsqueda por vectores sola (que no trae nada).
def make_hybrid_retriever(index: VectorStoreIndex, candidates: int, filters: MetadataFilters | None):
    vectors = index.as_retriever(similarity_top_k=candidates, filters=filters)
    nodes = [node for node in index.docstore.docs.values()
             if all(node.metadata.get(f.key) == f.value for f in (filters.filters if filters else []))]
    if not nodes:
        return vectors
    words = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=candidates,
                                        stemmer=Stemmer.Stemmer("spanish"), language="es")
    return QueryFusionRetriever([vectors, words], llm=MockLLM(), mode="reciprocal_rerank",
                                similarity_top_k=candidates, num_queries=1, use_async=False)


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


# ¿La metadata de una página cumple los filtros? (los mismos de to_filters: solo igualdad)
def matches(metadata: dict, filters: dict | None) -> bool:
    return all(metadata.get(key) == condition["value"] for key, condition in (filters or {}).items())


# Una búsqueda de prueba: trae candidatos y rerank-2.5 deja los más relevantes.
# Devuelve lo mismo que la búsqueda de LlamaCloud (content, score, rerank_score, metadata, static_fields).
async def search(client, store: RunStore, settings: DocumentsSettings, library: dict, query: str, top_k: int = 8, filters: dict | None = None) -> dict:
    ai_models.check_ready(settings)
    metadata_filters = to_filters(filters)  # primero se validan, antes de abrir el índice
    ai_models.prepare_nltk(ai_models.data_dir_of(store))
    index = load_index(store, settings, library)

    # Busca y rerankea (código bloqueante: corre en otro hilo). Guarda el score de la búsqueda para mostrarlo junto al del reranker.
    def run() -> list:
        retriever = make_retriever(index, settings, candidates=top_k * CANDIDATES_PER_RESULT, filters=metadata_filters)
        candidates = retriever.retrieve(query)
        vector_scores = {node.node.node_id: node.score for node in candidates}
        reranked = ai_models.make_reranker(settings, top_k).postprocess_nodes(candidates, QueryBundle(query))
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
    request = {"query": query, "top_k": top_k, "filters": filters, "modo": settings.library_retrieval_mode,
               "embed_model": settings.library_embed_model, "rerank_model": settings.library_rerank_model}
    response = {"results": results}
    result = {"at": now(), "request": request, "response": response, **summarize_search(response)}
    write_json(store.step_dir(library["id"], "searches") / f"{stamp()}.json", result)
    return result
