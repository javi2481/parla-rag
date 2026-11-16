"""Bibliotecas: varios documentos relacionados con un índice compartido, búsqueda y chat. Todo nativo de LlamaCloud.

    Biblioteca "BYMA 3T26"
     ├── EEFF · Comunicado · Presentación       ┐
     │   (corridas del wizard ya parseadas)     ├─ directorio ─→ índice ─→ búsqueda ─→ chat
     └── metadata de identidad de cada uno       ┘  (files.add)    (sync)   (retrieve)  (stream)

Cada biblioteca es una carpeta en data/documents/libraries/<id>/ con su library (run.json) y:
    create/       lo que respondió LlamaCloud al crear el directorio, la configuración de parse y el índice
    documents/    la respuesta de agregar cada documento
    syncs/<fecha>/   cada sincronización: el pedido, el índice al terminar y los parses que creó LlamaCloud
    searches/<fecha>.json   cada búsqueda de prueba: lo que se pidió y los resultados
    chats/<sesión>/turno_<n>.json   cada turno de chat: los eventos tal cual y la transcripción final
"""
import logging
from datetime import UTC, datetime

from llama_cloud import AsyncLlamaCloud

from app.core.runs.store import (
    RunStore,
    mark_done,
    mark_failed,
    mark_running,
    now,
    read_json,
    write_json,
)

from .settings import DocumentsSettings
from .steps import s2_parse

log = logging.getLogger(__name__)

# Lo que guarda el índice además de los chunks: la captura de cada página y los items con sus cajas.
STORE_ATTACHMENTS = ["screenshots", "items"]

# Los tipos de valor que pueden ir en la metadata de identidad (los grupos y las listas no).
IDENTITY_TYPES = (str, int, float, bool)


# Una marca de tiempo para nombrar carpetas y archivos: 2026-11-13_201203.
def stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


# Crea la biblioteca: un directorio en LlamaCloud y un índice sobre él que parsea con nuestra configuración
# completa (la misma que el paso Parse del wizard). Sin product_config_id, el índice usaría el tier cost_effective.
# Si LlamaCloud falla a mitad de camino, no queda nada a medias: se borra lo creado (en LlamaCloud y en la carpeta).
async def create_library(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, name: str, description: str = "") -> dict:
    directory = await client.beta.directories.create(name=name, description=description or None)
    library = store.create(name, [])
    try:
        return await setup_index(client, store, settings, library, directory, description)
    except Exception:
        await delete_library(client, store, settings, {**library, "directory_id": directory.id})
        raise


# La segunda parte de crear una biblioteca: guarda el directorio, la configuración de parse y crea el índice.
async def setup_index(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, library: dict, directory, description: str) -> dict:
    name = library["name"]
    folder = store.step_dir(library["id"], "create")
    write_json(folder / "directory.json", directory.model_dump())

    configuration = await s2_parse.save_configuration(client, s2_parse.build_request(settings))
    write_json(folder / "configuration.json", configuration)

    index = await client.indexes.create(
        source_directory_id=directory.id,
        name=name,
        description=description or None,
        products=[{"product_type": "parse", "product_config_id": configuration["id"]}],
        store_attachments=STORE_ATTACHMENTS,
        sync_frequency="manual",
    )
    write_json(folder / "index.json", index.model_dump())

    library.update({
        "description": description,
        "directory_id": directory.id,
        "index_id": index.id,
        "parse_configuration_id": configuration["id"],
        "documents": [],
        "needs_sync": False,
        "steps": {"sync": {"state": "pending"}},
    })
    store.save(library)
    return library


# Arma la metadata de identidad de un documento a partir de su corrida del wizard:
# el tipo que eligió Classify y los datos de identidad que sacó Extract, o sea los campos sueltos del primer nivel
# que el schema marca como obligatorios (emisor, período, fecha…). Los datos como el resultado neto no entran.
# Son datos trazables: cada uno tiene su cita en la corrida. Sirven para filtrar la búsqueda.
def identity_metadata(runs: RunStore, run: dict) -> dict:
    folder = runs.run_dir(run["id"])
    metadata = {"corrida": run["id"], "nombre": run["name"]}
    if (folder / "4_classify" / "result.json").is_file():
        kind = (read_json(folder / "4_classify" / "result.json") or {}).get("type")
        if kind:
            metadata["tipo"] = kind
    if (folder / "6_extract" / "result.json").is_file() and (folder / "5_schema" / "schema.json").is_file():
        identity = set(read_json(folder / "5_schema" / "schema.json").get("required") or [])
        for key, value in (read_json(folder / "6_extract" / "result.json") or {}).items():
            if key in identity and isinstance(value, IDENTITY_TYPES) and value != "":
                metadata[key] = value
    return metadata


# Agrega una corrida del wizard a la biblioteca: suma su archivo (el mismo file_id, no se vuelve a subir)
# al directorio, con su metadata de identidad. El índice lo procesa en la próxima sincronización.
async def add_document(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, runs: RunStore, library: dict, run_id: str) -> dict:
    run = runs.get(run_id)
    if any(doc["run_id"] == run_id for doc in library["documents"]):
        raise ValueError("Ese documento ya está en la biblioteca.")
    if run["steps"].get("parse", {}).get("state") != "done":
        raise ValueError("Primero hay que terminar el paso Parse del documento.")

    metadata = identity_metadata(runs, run)
    added = await client.beta.directories.files.add(
        library["directory_id"],
        file_id=run["steps"]["upload"]["file_id"],
        display_name=run["name"],
        unique_id=run_id,  # una corrida = un documento; si se vuelve a agregar, reemplaza en vez de duplicar
        metadata=metadata,
    )
    write_json(store.step_dir(library["id"], "documents") / f"{run_id}.json", added.model_dump())

    library["documents"].append({
        "run_id": run_id, "name": run["name"], "file_id": added.file_id,
        "directory_file_id": added.id, "metadata": metadata, "added_at": now(),
    })
    library["needs_sync"] = True
    store.save(library)
    return library


# Saca un documento de la biblioteca (del directorio). Sus chunks se borran del índice en la próxima sincronización.
async def remove_document(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, library: dict, run_id: str) -> dict:
    document = next((doc for doc in library["documents"] if doc["run_id"] == run_id), None)
    if document is None:
        raise LookupError("Ese documento no está en la biblioteca.")
    await client.beta.directories.files.delete(document["directory_file_id"], directory_id=library["directory_id"])
    library["documents"].remove(document)
    library.setdefault("historial", []).append({"removed": document, "at": now()})
    library["needs_sync"] = True
    store.save(library)
    return library


# Arranca la sincronización del índice: parsea lo nuevo o cambiado, borra lo que se sacó y exporta los chunks.
async def start_sync(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, library: dict) -> dict:
    if library["steps"]["sync"].get("state") == "running":
        raise ValueError("La biblioteca ya se está sincronizando.")
    before = await client.indexes.get(library["index_id"], expand=["sync_in_progress"])
    folder = store.step_dir(library["id"], f"syncs/{stamp()}")
    write_json(folder / "index_before.json", before.model_dump())
    started_at_utc = datetime.now(UTC)

    response = await client.indexes.sync(library["index_id"])
    write_json(folder / "sync_response.json", response.model_dump() if hasattr(response, "model_dump") else response)

    mark_running(library, "sync", folder=folder.name, documents=len(library["documents"]),
                 started_at_utc=started_at_utc.isoformat(),
                 last_synced_before=str(before.last_synced_at) if before.last_synced_at else None)
    library["needs_sync"] = False
    store.save(library)
    return library


# Consulta la sincronización. Termina cuando el índice ya no está sincronizando y su last_synced_at avanzó.
# Al terminar, lista los parses que creó LlamaCloud durante la sincronización: así se sabe si volvió a parsear y cuánto costó.
async def check_sync(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, library: dict) -> dict:
    sync = library["steps"]["sync"]
    if sync.get("state") != "running":
        return library

    index = await client.indexes.get(library["index_id"], expand=["sync_in_progress"])
    synced = str(index.last_synced_at) if index.last_synced_at else None
    status = (index.metadata or {}).get("status")
    sync["index_status"] = status
    if status == "failed":
        mark_failed(library, "sync", "LlamaCloud informó que la sincronización falló (ver index.json).")
    elif index.sync_in_progress or synced == sync.get("last_synced_before"):
        store.save(library)
        return library

    folder = store.run_dir(library["id"]) / "syncs" / sync["folder"]
    write_json(folder / "index.json", index.model_dump())
    jobs = [job.model_dump() async for job in client.parsing.list(created_at_on_or_after=sync["started_at_utc"])] if sync.get("started_at_utc") else []
    write_json(folder / "parse_jobs.json", jobs)
    summary = summarize_sync(library, index.model_dump(), jobs)
    write_json(folder / "metrics.json", summary)

    if library["steps"]["sync"]["state"] == "running":
        credits = sum((job.get("usage") or {}).get("credits") or 0 for job in jobs)
        mark_done(library, "sync", credits=credits, metricas=summary["metricas"], interpretacion=summary["interpretacion"])
    store.save(library)
    return library


# Las métricas y la interpretación de una sincronización, solo con lo que devolvió LlamaCloud.
def summarize_sync(library: dict, index: dict, jobs: list[dict]) -> dict:
    credits = sum((job.get("usage") or {}).get("credits") or 0 for job in jobs)
    metricas = [
        {"label": "Documentos", "value": len(library["documents"])},
        {"label": "Estado del índice", "value": (index.get("metadata") or {}).get("status") or "—"},
        {"label": "Última sincronización", "value": index.get("last_synced_at")},
        {"label": "Parses creados por LlamaCloud", "value": len(jobs)},
        {"label": "Créditos de esos parses", "value": credits},
    ]
    interpretacion = []
    if jobs:
        interpretacion.append(
            f"Durante la sincronización LlamaCloud creó {len(jobs)} {'parse nuevo' if len(jobs) == 1 else 'parses nuevos'}, por {credits} créditos: "
            "el índice vuelve a leer los documentos, no reutiliza el parse del wizard."
        )
    else:
        interpretacion.append("Durante la sincronización no se creó ningún parse nuevo: el índice no volvió a cobrar el parse.")
    interpretacion.append(
        "La exportación de chunks al índice cuesta 2 créditos por página según la lista de precios, pero LlamaCloud no la informa por job."
    )
    return {"metricas": metricas, "interpretacion": interpretacion}


# Una búsqueda de prueba en el índice: los chunks más parecidos a la pregunta, con su score y de qué documento y páginas salieron.
async def search(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, library: dict, query: str, top_k: int = 8, filters: dict | None = None) -> dict:
    request = {"index_id": library["index_id"], "query": query, "top_k": top_k}
    if filters:
        request["custom_filters"] = filters
    response = (await client.retrieval.retrieve(**request)).model_dump()
    result = {"at": now(), "request": request, "response": response, **summarize_search(response)}
    write_json(store.step_dir(library["id"], "searches") / f"{stamp()}.json", result)
    return result


# Las métricas y la interpretación de una búsqueda.
def summarize_search(response: dict) -> dict:
    results = response.get("results") or []
    documents = {(r.get("metadata") or {}).get("nombre") for r in results} - {None}
    scores = [r["score"] for r in results if r.get("score") is not None]
    metricas = [
        {"label": "Resultados", "value": len(results)},
        {"label": "Documentos distintos", "value": len(documents)},
        {"label": "Mejor score", "value": round(max(scores), 3) if scores else "—"},
        {"label": "Créditos", "value": "1 por búsqueda (lista de precios; no se informa)"},
    ]
    interpretacion = []
    if results:
        interpretacion.append(f"Encontró {len(results)} {'fragmento' if len(results) == 1 else 'fragmentos'} de {len(documents)} {'documento' if len(documents) == 1 else 'documentos'}: " + ", ".join(sorted(documents)) + ".")
    else:
        interpretacion.append("No encontró nada parecido a la pregunta.")
    return {"metricas": metricas, "interpretacion": interpretacion}


# Devuelve la sesión de chat de la biblioteca; si todavía no hay, la crea atada a su índice.
async def chat_session(client: AsyncLlamaCloud, store: RunStore, library: dict) -> str:
    if not library.get("chat_session_id"):
        session = await client.chat.create(index_ids=[library["index_id"]])
        library["chat_session_id"] = session.id
        library["chat_turns"] = 0
        write_json(store.step_dir(library["id"], f"chats/{session.id}") / "session.json", session.model_dump())
        store.save(library)
    return library["chat_session_id"]


# Un turno de chat. Va devolviendo los eventos tal cual los manda LlamaCloud (Server-Sent Events), para verlos en vivo,
# y al terminar guarda los eventos crudos y la transcripción completa de la sesión (chat.retrieve).
async def chat_turn(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, library: dict, prompt: str):
    session_id = await chat_session(client, store, library)  # settings no se usa: está para que las dos versiones sean iguales
    lines = []
    async with client.chat.with_streaming_response.stream(session_id, index_ids=[library["index_id"]], prompt=prompt) as response:
        async for line in response.iter_lines():
            lines.append(line)
            yield line + "\n"

    library["chat_turns"] = library.get("chat_turns", 0) + 1
    transcript = await client.chat.retrieve(session_id)
    summary = await client.chat.get_summary(session_id)
    write_json(store.step_dir(library["id"], f"chats/{session_id}") / f"turno_{library['chat_turns']}.json", {
        "at": now(), "prompt": prompt, "events_raw": lines,
        "transcript": transcript.model_dump(), "summary": summary.model_dump(),
    })
    store.save(library)


# Borra en LlamaCloud el índice, el directorio y la sesión de chat de la biblioteca (los archivos de las corridas no se tocan).
async def delete_library(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, library: dict) -> None:
    for delete, target in [(client.chat.delete, library.get("chat_session_id")),
                           (client.indexes.delete, library.get("index_id")),
                           (client.beta.directories.delete, library.get("directory_id"))]:
        if target:
            try:
                await delete(target)
            except Exception as e:  # noqa: BLE001 -- a propósito: si falla un borrado, se avisa y se sigue con el resto
                log.warning("No se pudo borrar %s de la biblioteca %s: %s", target, library["id"], e)
    store.delete(library["id"])
