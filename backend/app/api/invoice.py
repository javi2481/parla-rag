from dataclasses import asdict
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.core.config import get_settings
from app.core.limits import RateLimiter, client_ip
from app.pipelines.invoice.errors import InvoiceError
from app.pipelines.invoice.pipeline import InvoicePipeline
from app.pipelines.invoice.schema import MAX_BYTES

from .deps import invoice_pipeline

router = APIRouter(prefix="/api/invoice", tags=["invoice"])
PipelineDep = Annotated[InvoicePipeline, Depends(invoice_pipeline)]


@lru_cache
def _limiter() -> RateLimiter:
    return RateLimiter(get_settings().invoice_daily_limit, 86400, "Se alcanzó el límite diario de extracciones.")


@router.post("/extract")
async def extract(request: Request, pipeline: PipelineDep, file: Annotated[UploadFile, File()]):
    data = await file.read(MAX_BYTES + 1)
    ip = client_ip(request)
    try:
        ticket = await pipeline.start(file.filename or "", data, owner=ip, before_upload=lambda: _limiter().check(ip))
    except InvoiceError as e:
        raise HTTPException(400, str(e)) from e
    return {"ticket": ticket}


@router.get("/status/{ticket}")
async def status(ticket: str, request: Request, pipeline: PipelineDep):
    try:
        return asdict(await pipeline.poll(ticket, owner=client_ip(request)))
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except TimeoutError as e:
        raise HTTPException(408, str(e)) from e
    except InvoiceError as e:
        raise HTTPException(422, str(e)) from e
