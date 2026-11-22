"""Responder en el chat de una biblioteca local: las instrucciones del modelo, los dos motores y el turno del chat.

    "contexto"  CondensePlusContextChatEngine: reescribe la pregunta si hay historial, busca UNA vez y responde
    "agente"    FunctionAgent: el modelo decide qué buscar y cuántas veces antes de responder (por ahora, solo en evals)

El chat de la pantalla usa "contexto". Los dos los arma este archivo, así los evals miden exactamente el mismo chat.
"""
import asyncio
import json
import logging
from pathlib import Path

from llama_index.core import VectorStoreIndex
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.instrumentation import get_dispatcher
from llama_index.core.llms import ChatMessage
from llama_index.core.schema import MetadataMode, QueryBundle
from llama_index.core.tools import FunctionTool
from llama_index.core.vector_stores import MetadataFilters

from app.core.runs.store import RunStore, now, write_json
from app.pipelines.documents.settings import DocumentsSettings

from . import ai_models
from .conversations import chat_history, conversation_folder, create_conversation
from .index_builder import load_index
from .retrieval import make_retriever, matches, to_filters
from .turn_recorder import TurnRecorder, total_usage

log = logging.getLogger(__name__)

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

# Las instrucciones del agente: las mismas del chat, más cómo usar la herramienta de búsqueda.
AGENT_PROMPT = SYSTEM_PROMPT + """
Para responder tenés la herramienta buscar_en_la_biblioteca. Usala siempre antes de responder: nunca respondas sin buscar.
Si la pregunta junta varios temas, modelos o clases, hacé una búsqueda corta y concreta por cada uno
y después relacioná lo que encontraste. Si una búsqueda no trae lo que necesitás, probá con otras palabras."""

# Cuántos pasos puede dar el agente como máximo (cada búsqueda es un paso). Al llegar al tope, responde con lo que tiene.
AGENT_MAX_STEPS = 6

# Lo que responde el chat cuando ninguna página cumple los filtros (sin llamar al modelo).
NO_PAGES_WITH_FILTERS = "No encontré páginas con esos filtros."


# Arma el chat engine de LlamaIndex (condense_plus_context) con sus instrucciones, el buscador y el reranker.
# Lo usan el chat y los evals, así los evals miden exactamente el mismo chat.
# "candidates" es cuántos candidatos trae la búsqueda antes del reranker (por defecto, top_k × 3).
def make_chat_engine(index: VectorStoreIndex, settings: DocumentsSettings, history: list[ChatMessage],
                     candidates: int | None = None, filters: MetadataFilters | None = None) -> CondensePlusContextChatEngine:
    top_k = settings.library_chat_top_k
    return CondensePlusContextChatEngine.from_defaults(
        retriever=make_retriever(index, settings, candidates, filters),
        llm=ai_models.make_llm(settings),
        chat_history=history,
        system_prompt=SYSTEM_PROMPT,
        context_prompt=CONTEXT_PROMPT,
        condense_prompt=CONDENSE_PROMPT,
        node_postprocessors=[ai_models.make_reranker(settings, top_k)],
    )


# El agente (FunctionAgent de LlamaIndex): en vez de una sola búsqueda, el modelo decide qué buscar y cuántas veces.
# Sirve para las preguntas que cruzan clases: puede buscar "atención en Transformers" y "atención en visión" por separado.
# Cada búsqueda usa el mismo buscador y el mismo reranker que el chat. Las páginas que va viendo se suman a "seen",
# así se pueden mostrar como fuentes y los evals pueden medir qué le llegó al modelo.
def make_agent(index: VectorStoreIndex, settings: DocumentsSettings, seen: list,
               filters: MetadataFilters | None = None) -> FunctionAgent:
    retriever = make_retriever(index, settings, filters=filters)
    reranker = ai_models.make_reranker(settings, settings.library_chat_top_k)

    # La herramienta del agente. El docstring es la descripción que lee el modelo para saber cuándo usarla.
    async def buscar_en_la_biblioteca(consulta: str) -> str:
        """Busca en la biblioteca de la materia las páginas más relevantes para una consulta corta y devuelve su texto, con el documento y la página."""
        # Buscar y rerankear es código bloqueante: corre en otro hilo.
        def run() -> list:
            return reranker.postprocess_nodes(retriever.retrieve(consulta), QueryBundle(consulta))
        nodes = await asyncio.to_thread(run)
        seen.extend(nodes)
        return "\n\n---\n\n".join(node.node.get_content(metadata_mode=MetadataMode.LLM) for node in nodes)

    return FunctionAgent(tools=[FunctionTool.from_defaults(async_fn=buscar_en_la_biblioteca)],
                         llm=ai_models.make_llm(settings), system_prompt=AGENT_PROMPT)


# Las páginas que vio el modelo, sin repetir (el agente puede traer la misma página en dos búsquedas).
def unique_nodes(nodes: list) -> list:
    unique = {}
    for node in nodes:
        unique.setdefault(node.node.node_id, node)
    return list(unique.values())


# Una línea de Server-Sent Events, el mismo formato que manda el chat de LlamaCloud.
def sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


# Un turno de chat con el chat engine de LlamaIndex (condense_plus_context):
#   1. si ya hubo preguntas, OpenAI reescribe la nueva para que se entienda sola;
#   2. la búsqueda trae candidatos y rerank-2.5 deja las mejores páginas;
#   3. OpenAI responde con esas páginas, citando documento y página. La respuesta llega en vivo.
# Manda los mismos eventos que el chat de LlamaCloud (tool_call, tool_result, text_delta, stop) y guarda todo el turno
# en la carpeta de su conversación. Sin conversation_id se crea una nueva; el evento "stop" dice cuál se usó.
# "filters" acota la búsqueda por metadata (por ejemplo, una unidad o una clase). Si ninguna página los cumple,
# se responde un mensaje fijo sin llamar a OpenAI: no tiene sentido pagar una respuesta sin páginas.
async def chat_turn(client, store: RunStore, settings: DocumentsSettings, library: dict, prompt: str,
                    conversation_id: str | None = None, filters: dict | None = None):
    ai_models.check_ready(settings)
    if not settings.openai_api_key:
        raise ValueError("Falta configurar OPENAI_API_KEY en backend/.env.")
    metadata_filters = to_filters(filters)  # primero se validan, antes de abrir el índice
    if conversation_id is None:
        conversation_id = create_conversation(store, library)["id"]
    folder = conversation_folder(store, library, conversation_id)
    ai_models.prepare_nltk(ai_models.data_dir_of(store))
    index = load_index(store, settings, library)
    history = chat_history(folder)
    top_k = settings.library_chat_top_k
    engine = make_chat_engine(index, settings, history, filters=metadata_filters)
    recorder = TurnRecorder()
    dispatcher = get_dispatcher()
    dispatcher.add_event_handler(recorder)
    events, answer, sources, error = [], "", [], None
    has_pages = any(matches(node.metadata, filters) for node in index.docstore.docs.values())
    if not has_pages:
        answer = NO_PAGES_WITH_FILTERS
        events.append({"type": "text_delta", "content": answer})
        yield sse(events[-1])
    try:
        if has_pages:
            response = await engine.astream_chat(prompt)
            search_call = {"type": "tool_call", "call_id": "busqueda", "name": "buscar_en_la_biblioteca",
                           "arguments": {"busquedas": recorder.searches, "paginas_para_el_modelo": top_k,
                                         "modo": settings.library_retrieval_mode}}
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
    yield finish_turn(folder, settings, prompt, answer, error, history, filters, recorder, sources, events,
                      conversation_id)


# Cierra un turno: manda el evento "stop" (con el uso de tokens y la conversación) y guarda todo en turno_N.json.
def finish_turn(folder: Path, settings: DocumentsSettings, prompt: str, answer: str, error: str | None,
                history: list, filters: dict | None, recorder, sources: list, events: list, conversation_id: str) -> str:
    usage = total_usage(recorder.llm_calls, settings)
    stop = {"type": "stop", "usage": usage, "conversation_id": conversation_id}
    events.append(stop)
    number = len(list(folder.glob("turno_*.json"))) + 1
    write_json(folder / f"turno_{number}.json", {
        "at": now(), "prompt": prompt, "answer": answer, "error": error, "engine": "local",
        "request": {"chat_model": settings.library_chat_model, "embed_model": settings.library_embed_model,
                    "rerank_model": settings.library_rerank_model, "top_k": settings.library_chat_top_k,
                    "modo": settings.library_retrieval_mode,
                    "historial": len(history) // 2, "filters": filters},
        "searches": recorder.searches, "sources": sources, "llm_calls": recorder.llm_calls, "usage": usage,
        "events_raw": [sse(event).strip() for event in events],
    })
    return sse(stop)
