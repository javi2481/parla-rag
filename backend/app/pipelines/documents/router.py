"""Rutas HTTP del pipeline de documentos: /api/documents/...

Son finas a propósito: reciben el pedido, llaman al pipeline y traducen los errores a códigos HTTP.
"""
from dataclasses import asdict
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.core.limits import RateLimiter, client_ip

from .errors import DocumentError
from .pipeline import DocumentPipeline
from .schema import INVOICE_FIELDS, MAX_BYTES, MAX_PAGES
from .settings import DocumentsSettings, get_documents_settings

router = APIRouter(prefix="/api/documents", tags=["documents"])

SettingsDep = Annotated[DocumentsSettings, Depends(get_documents_settings)]


# Devuelve el pipeline creado al arrancar la app. Si falta la API key, responde 503.
def get_pipeline(request: Request, settings: SettingsDep) -> DocumentPipeline:
    if not settings.ready:
        raise HTTPException(503, "Falta configurar LLAMA_CLOUD_API_KEY.")
    return request.app.state.documents_pipeline


PipelineDep = Annotated[DocumentPipeline, Depends(get_pipeline)]


# Crea (una sola vez) el limitador de extracciones por día.
@lru_cache
def daily_limiter() -> RateLimiter:
    limit = get_documents_settings().documents_daily_limit
    return RateLimiter(limit, 24 * 60 * 60, "Se alcanzó el límite diario de extracciones.")


# Configuración pública que necesita el frontend (nunca incluye la API key).
def public_config(settings: DocumentsSettings) -> dict:
    return {
        "ready": settings.ready,
        "fields": INVOICE_FIELDS,
        "maxBytes": MAX_BYTES,
        "maxPages": MAX_PAGES,
        "dailyLimit": settings.documents_daily_limit,
        "tier": settings.extract_tier,
    }


# POST /api/documents/extract: recibe el archivo, arranca la extracción y devuelve un ticket.
@router.post("/extract")
async def extract(request: Request, pipeline: PipelineDep, file: Annotated[UploadFile, File()]):
    # Se lee un byte de más para detectar si el archivo supera el máximo.
    data = await file.read(MAX_BYTES + 1)
    ip = client_ip(request)

    # Revisa el límite diario de esta IP (se llama solo si el archivo es válido).
    def check_limit() -> None:
        daily_limiter().check(ip)

    try:
        ticket = await pipeline.start(file.filename or "", data, owner=ip, before_upload=check_limit)
    except DocumentError as e:
        raise HTTPException(400, str(e)) from e
    return {"ticket": ticket}


# GET /api/documents/status/{ticket}: dice si la extracción terminó y, si terminó, devuelve los datos.
@router.get("/status/{ticket}")
async def status(ticket: str, request: Request, pipeline: PipelineDep):
    try:
        result = await pipeline.poll(ticket, owner=client_ip(request))
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except TimeoutError as e:
        raise HTTPException(408, str(e)) from e
    except DocumentError as e:
        raise HTTPException(422, str(e)) from e
    return asdict(result)
