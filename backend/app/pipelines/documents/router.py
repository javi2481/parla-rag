"""Rutas HTTP del pipeline de documentos: /api/documents/...

Son finas a propósito: reciben el pedido, llaman al pipeline y traducen los errores a códigos HTTP.

    GET    /runs                       lista las corridas
    POST   /runs                       sube un archivo y crea la corrida (paso 1)
    GET    /runs/{id}                  la corrida con todos sus pasos
    DELETE /runs/{id}                  borra la corrida (la carpeta y lo que haya en LlamaCloud)
    POST   /runs/{id}/steps/{paso}     arranca un paso
    GET    /runs/{id}/steps/{paso}     consulta un paso (si está corriendo, pregunta a LlamaCloud)
    GET    /runs/{id}/files/{ruta}     descarga un archivo guardado
"""
import logging
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from llama_cloud import APIError, AsyncLlamaCloud

from app.core.limits import RateLimiter, client_ip
from app.core.runs.store import RunStore
from app.core.settings import CoreSettings, get_core_settings

from . import pipeline
from .errors import DocumentError
from .settings import DocumentsSettings, get_documents_settings
from .steps import s1_upload

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

SettingsDep = Annotated[DocumentsSettings, Depends(get_documents_settings)]


# Devuelve el cliente de LlamaCloud creado al arrancar la app. Si falta la API key, responde 503.
def get_client(request: Request, settings: SettingsDep) -> AsyncLlamaCloud:
    if not settings.ready:
        raise HTTPException(503, "Falta configurar LLAMA_CLOUD_API_KEY.")
    return request.app.state.documents_client


# Devuelve la carpeta-DB de las corridas de documentos.
def get_store(core: Annotated[CoreSettings, Depends(get_core_settings)]) -> RunStore:
    return RunStore(core.data_dir, "documents")


ClientDep = Annotated[AsyncLlamaCloud, Depends(get_client)]
StoreDep = Annotated[RunStore, Depends(get_store)]


# Crea (una sola vez) el limitador de documentos subidos por día.
@lru_cache
def daily_limiter() -> RateLimiter:
    limit = get_documents_settings().documents_daily_limit
    return RateLimiter(limit, 24 * 60 * 60, "Se alcanzó el límite diario de documentos.")


# Configuración pública que necesita el frontend (nunca incluye la API key).
def public_config(settings: DocumentsSettings) -> dict:
    return {
        "ready": settings.ready,
        "maxUploadMb": settings.max_upload_mb,
        "parseTier": settings.parse_tier,
        "parseVersion": settings.parse_version,
        "parseMaxPages": settings.parse_max_pages,
    }


# Busca una corrida; si no existe, responde 404.
def find_run(store: RunStore, run_id: str) -> dict:
    try:
        return store.get(run_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e


# Convierte un error de LlamaCloud en un 502 con un mensaje entendible.
def llama_cloud_error(e: APIError) -> HTTPException:
    log.error("LlamaCloud: %s", e)
    return HTTPException(502, f"LlamaCloud respondió con un error: {e.message}")


# GET /runs: lista las corridas, de la más nueva a la más vieja.
@router.get("/runs")
def list_runs(store: StoreDep):
    runs = []
    for run in store.list_runs():
        runs.append(pipeline.describe_run(store, run))
    return runs


# POST /runs: sube el archivo a LlamaCloud y crea la corrida con el paso 1 terminado.
@router.post("/runs")
async def create_run(request: Request, client: ClientDep, store: StoreDep, settings: SettingsDep,
                     file: Annotated[UploadFile, File()]):
    # Se lee un byte de más para detectar si el archivo supera el máximo.
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    try:
        s1_upload.check_size(data, settings.max_upload_mb)
    except DocumentError as e:
        raise HTTPException(400, str(e)) from e
    daily_limiter().check(client_ip(request))

    filename = file.filename or "documento"
    mime = file.content_type or "application/octet-stream"
    run = store.create(filename, pipeline.STEP_NAMES)
    try:
        await s1_upload.run_step(client, store, run, filename, mime, data)
    except APIError as e:
        store.delete(run["id"])
        raise llama_cloud_error(e) from e
    return pipeline.describe_run(store, run)


# GET /runs/{id}: la corrida con todos sus pasos.
@router.get("/runs/{run_id}")
def get_run(run_id: str, store: StoreDep):
    return pipeline.describe_run(store, find_run(store, run_id))


# DELETE /runs/{id}: borra la corrida en LlamaCloud y en la carpeta.
@router.delete("/runs/{run_id}")
async def delete_run(run_id: str, client: ClientDep, store: StoreDep):
    run = find_run(store, run_id)
    await pipeline.delete_remote(client, run)
    store.delete(run_id)
    return {"deleted": run_id}


# POST /runs/{id}/steps/{paso}: arranca un paso.
@router.post("/runs/{run_id}/steps/{step_name}")
async def start_step(run_id: str, step_name: str, client: ClientDep, store: StoreDep, settings: SettingsDep):
    run = find_run(store, run_id)
    try:
        await pipeline.start_step(client, store, settings, run, step_name)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    except APIError as e:
        raise llama_cloud_error(e) from e
    return pipeline.describe_run(store, run)


# GET /runs/{id}/steps/{paso}: si el paso está corriendo, le pregunta a LlamaCloud cómo va.
# Devuelve la corrida entera, para que el wizard se actualice de una vez.
@router.get("/runs/{run_id}/steps/{step_name}")
async def check_step(run_id: str, step_name: str, client: ClientDep, store: StoreDep):
    run = find_run(store, run_id)
    try:
        await pipeline.check_step(client, store, run, step_name)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except APIError as e:
        raise llama_cloud_error(e) from e
    return pipeline.describe_run(store, run)


# Extensiones que el navegador puede mostrar directamente sin riesgo.
INLINE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


# GET /runs/{id}/files/{ruta}: descarga un archivo guardado por algún paso.
# Las imágenes y los PDF se muestran en el navegador; el resto se baja como archivo
# (así un documento subido nunca se ejecuta como página web).
@router.get("/runs/{run_id}/files/{relative_path:path}")
def download_file(run_id: str, relative_path: str, store: StoreDep):
    try:
        path = store.file_path(run_id, relative_path)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    headers = {"X-Content-Type-Options": "nosniff"}
    if path.suffix.lower() in INLINE_SUFFIXES:
        return FileResponse(path, headers=headers)
    return FileResponse(path, filename=path.name, headers=headers)
