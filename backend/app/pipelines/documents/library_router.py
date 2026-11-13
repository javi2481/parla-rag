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
"""
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from llama_cloud import APIError

from app.core.runs.store import RunStore, read_json
from app.core.settings import CoreSettings, get_core_settings

from . import library as lib
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


@router.get("")
def list_libraries(store: LibrariesDep):
    return store.list_runs()


@router.post("")
async def create_library(client: ClientDep, store: LibrariesDep, settings: SettingsDep,
                         name: Annotated[str, Body(embed=True)], description: Annotated[str, Body(embed=True)] = ""):
    library = await guarded(lib.create_library(client, store, settings, name.strip() or "Biblioteca", description))
    return describe(store, library)


@router.get("/{library_id}")
def get_library(library_id: str, store: LibrariesDep):
    return describe(store, find(store, library_id))


@router.delete("/{library_id}")
async def delete_library(library_id: str, client: ClientDep, store: LibrariesDep):
    await lib.delete_library(client, store, find(store, library_id))
    return {"deleted": library_id}


@router.post("/{library_id}/documents")
async def add_document(library_id: str, client: ClientDep, store: LibrariesDep, runs: RunsDep,
                       run_id: Annotated[str, Body(embed=True)]):
    library = await guarded(lib.add_document(client, store, runs, find(store, library_id), run_id))
    return describe(store, library)


@router.delete("/{library_id}/documents/{run_id}")
async def remove_document(library_id: str, run_id: str, client: ClientDep, store: LibrariesDep):
    library = await guarded(lib.remove_document(client, store, find(store, library_id), run_id))
    return describe(store, library)


@router.post("/{library_id}/sync")
async def start_sync(library_id: str, client: ClientDep, store: LibrariesDep):
    library = await guarded(lib.start_sync(client, store, find(store, library_id)))
    return describe(store, library)


@router.get("/{library_id}/sync")
async def check_sync(library_id: str, client: ClientDep, store: LibrariesDep):
    library = await guarded(lib.check_sync(client, store, find(store, library_id)))
    return describe(store, library)


@router.post("/{library_id}/search")
async def search(library_id: str, client: ClientDep, store: LibrariesDep,
                 query: Annotated[str, Body(embed=True)], top_k: Annotated[int, Body(embed=True)] = 8,
                 filters: Annotated[dict | None, Body(embed=True)] = None):
    if not query.strip():
        raise HTTPException(400, "Escribí qué querés buscar.")
    return await guarded(lib.search(client, store, find(store, library_id), query, top_k, filters))


# El turno de chat se manda en vivo: cada línea es lo que va enviando LlamaCloud (Server-Sent Events).
@router.post("/{library_id}/chat")
async def chat(library_id: str, client: ClientDep, store: LibrariesDep, prompt: Annotated[str, Body(embed=True)]):
    if not prompt.strip():
        raise HTTPException(400, "Escribí una pregunta.")
    library = find(store, library_id)

    async def events():
        try:
            async for line in lib.chat_turn(client, store, library, prompt):
                yield line
        except APIError as e:
            log.error("Chat: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'content': e.message})}\n"

    return StreamingResponse(events(), media_type="text/event-stream")
