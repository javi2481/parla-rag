"""Rutas HTTP de las bibliotecas: /api/documents/libraries/...

    GET    /libraries                          lista las bibliotecas
    POST   /libraries                          crea una (directorio + índice en LlamaCloud)
    GET    /libraries/{id}                     la biblioteca con sus documentos, búsquedas y turnos de chat
    DELETE /libraries/{id}                     la borra (en LlamaCloud y en la carpeta)
    POST   /libraries/{id}/documents           agrega una corrida del wizard
    DELETE /libraries/{id}/documents/{corrida} saca un documento
    POST   /libraries/{id}/sync                arranca la sincronización del índice
    GET    /libraries/{id}/sync                consulta la sincronización
    POST   /libraries/{id}/search              búsqueda de prueba
    POST   /libraries/{id}/chat                un turno de chat (los eventos llegan en vivo)
    POST   /libraries/{id}/evals               corre los evals con un set de preguntas (solo bibliotecas locales)
"""
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from llama_cloud import APIError
from voyageai.error import RateLimitError, VoyageError

from app.core.runs.store import RunStore, read_json
from app.core.settings import CoreSettings, get_core_settings

from . import library as lib
from . import library_evals, local_library
from .router import ClientDep, SettingsDep, get_store, llama_cloud_error

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents/libraries", tags=["libraries"])


# Devuelve la carpeta-DB de las bibliotecas.
def get_libraries(core: Annotated[CoreSettings, Depends(get_core_settings)]) -> RunStore:
    return RunStore(core.data_dir, "documents", "libraries")


LibrariesDep = Annotated[RunStore, Depends(get_libraries)]
RunsDep = Annotated[RunStore, Depends(get_store)]


# Busca una biblioteca; si no existe, responde 404.
def find(store: RunStore, library_id: str) -> dict:
    try:
        return store.get(library_id)
    except LookupError as e:
        raise HTTPException(404, "La biblioteca no existe.") from e


# El motor de una biblioteca: "local" (LlamaIndex + Voyage AI) o LlamaCloud. Cada biblioteca guarda con cuál se creó.
def engine_of(library: dict):
    return local_library if library.get("engine") == "local" else lib


# El motor para crear una biblioteca nueva, según LIBRARY_ENGINE en el .env.
def engine_for(settings) -> object:
    return local_library if settings.library_engine == "local" else lib


# Saca los eventos de las líneas de Server-Sent Events: cada "data: {...}" es un evento en JSON.
def parse_events(lines: list[str]) -> list[dict]:
    events = []
    for line in lines:
        if line.startswith("data:"):
            try:
                events.append(json.loads(line[5:].strip()))
            except json.JSONDecodeError:
                events.append({"type": "raw", "content": line})
    return events


# Arma lo que muestra la pantalla de una biblioteca: sus datos, las búsquedas guardadas y los turnos de chat.
def describe(store: RunStore, library: dict) -> dict:
    folder = store.run_dir(library["id"])
    searches = [read_json(path) for path in sorted((folder / "searches").glob("*.json"), reverse=True)]
    turns = []
    for path in sorted((folder / "chats").glob("*/turno_*.json"), key=lambda p: int(p.stem.split("_")[1])):
        turn = read_json(path)
        turns.append({"at": turn["at"], "prompt": turn["prompt"], "events": parse_events(turn["events_raw"]),
                      "summary": turn.get("summary")})
    return {**library, "searches": searches, "turns": turns}


# Ejecuta una llamada a LlamaCloud y traduce sus errores a HTTP.
async def guarded(call):
    try:
        return await call
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    except APIError as e:
        raise llama_cloud_error(e) from e
    except RateLimitError as e:
        log.error("Voyage AI: %s", e)
        raise HTTPException(429, "Voyage AI limitó los pedidos por minuto. Sin un medio de pago cargado permite "
                                 "3 pedidos y 10.000 tokens por minuto (los tokens gratis se mantienen igual).") from e
    except VoyageError as e:
        log.error("Voyage AI: %s", e)
        raise HTTPException(502, f"Voyage AI respondió con un error: {e}") from e


@router.get("")
def list_libraries(store: LibrariesDep):
    return store.list_runs()


@router.post("")
async def create_library(client: ClientDep, store: LibrariesDep, settings: SettingsDep,
                         name: Annotated[str, Body(embed=True)], description: Annotated[str, Body(embed=True)] = ""):
    library = await guarded(engine_for(settings).create_library(client, store, settings, name.strip() or "Biblioteca", description))
    return describe(store, library)


@router.get("/{library_id}")
def get_library(library_id: str, store: LibrariesDep):
    return describe(store, find(store, library_id))


@router.delete("/{library_id}")
async def delete_library(library_id: str, client: ClientDep, store: LibrariesDep, settings: SettingsDep):
    library = find(store, library_id)
    await engine_of(library).delete_library(client, store, settings, library)
    return {"deleted": library_id}


@router.post("/{library_id}/documents")
async def add_document(library_id: str, client: ClientDep, store: LibrariesDep, settings: SettingsDep, runs: RunsDep,
                       run_id: Annotated[str, Body(embed=True)]):
    library = find(store, library_id)
    library = await guarded(engine_of(library).add_document(client, store, settings, runs, library, run_id))
    return describe(store, library)


@router.delete("/{library_id}/documents/{run_id}")
async def remove_document(library_id: str, run_id: str, client: ClientDep, store: LibrariesDep, settings: SettingsDep):
    library = find(store, library_id)
    library = await guarded(engine_of(library).remove_document(client, store, settings, library, run_id))
    return describe(store, library)


@router.post("/{library_id}/sync")
async def start_sync(library_id: str, client: ClientDep, store: LibrariesDep, settings: SettingsDep):
    library = find(store, library_id)
    library = await guarded(engine_of(library).start_sync(client, store, settings, library))
    return describe(store, library)


@router.get("/{library_id}/sync")
async def check_sync(library_id: str, client: ClientDep, store: LibrariesDep, settings: SettingsDep):
    library = find(store, library_id)
    library = await guarded(engine_of(library).check_sync(client, store, settings, library))
    return describe(store, library)


@router.post("/{library_id}/search")
async def search(library_id: str, client: ClientDep, store: LibrariesDep, settings: SettingsDep,
                 query: Annotated[str, Body(embed=True)], top_k: Annotated[int, Body(embed=True)] = 8,
                 filters: Annotated[dict | None, Body(embed=True)] = None):
    if not query.strip():
        raise HTTPException(400, "Escribí qué querés buscar.")
    library = find(store, library_id)
    return await guarded(engine_of(library).search(client, store, settings, library, query, top_k, filters))


# Evals: mide la búsqueda (y, si se pide, las respuestas juzgadas por DeepSeek) con un set de preguntas verificadas.
# "candidatos" cambia cuántos candidatos trae la búsqueda por vectores antes del reranker (por defecto, el del chat).
@router.post("/{library_id}/evals")
async def run_evals(library_id: str, store: LibrariesDep, settings: SettingsDep,
                    conjunto: Annotated[str, Body(embed=True)] = "byma",
                    candidatos: Annotated[int | None, Body(embed=True)] = None,
                    respuestas: Annotated[bool, Body(embed=True)] = False):
    library = find(store, library_id)
    if library.get("engine") != "local":
        raise HTTPException(409, "Los evals solo están hechos para las bibliotecas locales.")
    return await guarded(library_evals.run_evals(store, settings, library, conjunto, candidatos, respuestas))


# El turno de chat se manda en vivo: cada línea es lo que va enviando LlamaCloud (Server-Sent Events).
@router.post("/{library_id}/chat")
async def chat(library_id: str, client: ClientDep, store: LibrariesDep, settings: SettingsDep,
               prompt: Annotated[str, Body(embed=True)]):
    if not prompt.strip():
        raise HTTPException(400, "Escribí una pregunta.")
    library = find(store, library_id)

    async def events():
        try:
            async for line in engine_of(library).chat_turn(client, store, settings, library, prompt):
                yield line
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n"
        except APIError as e:
            log.error("Chat: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'content': e.message})}\n"

    return StreamingResponse(events(), media_type="text/event-stream")
