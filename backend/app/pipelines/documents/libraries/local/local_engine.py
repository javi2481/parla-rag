"""El motor local de las bibliotecas: la puerta de entrada que usa la ruta (library_routes.py).

Hace lo mismo que el motor de LlamaCloud (../llamacloud_engine.py), pero el índice vive en nuestro servidor,
porque el de LlamaCloud necesita un plan pago (ver docs/bitacora.md, 13/11). Todo es nativo de la familia LlamaIndex:
el framework LlamaIndex (código abierto) arma el índice, Voyage AI hace los embeddings (voyage-4) y el reranking
(rerank-2.5), y OpenAI escribe las respuestas (gpt-5-nano). Las dos con sus integraciones oficiales de LlamaIndex.

    Biblioteca "Aprendizaje Automático II"
     ├── Clase 00 · Clase 01 · … · Clase 13   corridas del wizard: se usa su parse, NO se vuelve a parsear
     │      ↓ una página = un chunk, con la metadata de identidad          → index_builder.py
     ├── búsqueda   vectores + BM25 traen candidatos → rerank-2.5 deja 6    → retrieval.py
     ├── chat       OpenAI responde con esas páginas, citando cada una      → chat_engine.py
     │              (cada pestaña es una conversación con su historial)     → conversations.py
     └── evals      miden la búsqueda y las respuestas                      → rag_evals.py

Este archivo solo junta las funciones que la ruta llama con el mismo nombre en los dos motores
(create_library, add_document, remove_document, start_sync, check_sync, search, chat_turn y delete_library).
"""
from .chat_engine import chat_turn
from .index_builder import (
    add_document,
    check_sync,
    create_library,
    delete_library,
    remove_document,
    start_sync,
)
from .retrieval import search

__all__ = ["add_document", "chat_turn", "check_sync", "create_library", "delete_library",
           "remove_document", "search", "start_sync"]
