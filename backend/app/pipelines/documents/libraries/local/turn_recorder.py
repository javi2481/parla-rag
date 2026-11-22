"""Registrar todo lo que pasa en un turno del chat, con la instrumentación nativa de LlamaIndex:
qué se buscó, cada llamada al modelo con su prompt y su respuesta, y los tokens que gastó (con su costo estimado).
Lo usan el chat y los evals.
"""
from llama_index.core.instrumentation.event_handlers import BaseEventHandler
from llama_index.core.instrumentation.events.llm import (
    LLMChatEndEvent,
    LLMCompletionEndEvent,
)
from llama_index.core.instrumentation.events.retrieval import RetrievalEndEvent
from llama_index.core.schema import QueryBundle
from pydantic import Field

from app.pipelines.documents.settings import DocumentsSettings


# Escucha lo que hace LlamaIndex durante un turno (instrumentación nativa): qué buscó y cada llamada al modelo con sus tokens.
class TurnRecorder(BaseEventHandler):
    searches: list = Field(default_factory=list)
    llm_calls: list = Field(default_factory=list)

    # LlamaIndex llama a esta función con cada evento: se anotan la búsqueda y las llamadas al modelo.
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
# El costo en dólares es estimado: tokens × la lista de precios de settings (OpenAI no informa el costo en la respuesta).
def total_usage(llm_calls: list, settings: DocumentsSettings) -> dict:
    usages = [call["usage"] or {} for call in llm_calls]
    reasoning = sum((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0 for u in usages)
    tokens_in = sum(u.get("prompt_tokens") or 0 for u in usages)
    tokens_out = sum(u.get("completion_tokens") or 0 for u in usages)
    cost = (tokens_in * settings.library_chat_price_input_usd + tokens_out * settings.library_chat_price_output_usd) / 1_000_000
    return {
        "modelo": settings.library_chat_model,
        "llamadas_al_modelo": sum(1 for u in usages if u),
        "tokens_de_entrada": tokens_in,
        "tokens_de_salida": tokens_out,
        "de_esos_razonamiento": reasoning,
        "tokens_en_cache": sum((u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0 for u in usages),
        "costo_estimado_usd": round(cost, 6),
    }
