"""Paso 3 · Extracción con LlamaExtract v2 (POST /api/v2/extract, GET /api/v2/extract/{id})."""
import logging
from dataclasses import dataclass
from typing import Literal

from llama_cloud import APIError, AsyncLlamaCloud

from app.core.config import Settings

from ..errors import InvoiceError
from ..schema import extract_configuration
from .validate import ValidDocument

log = logging.getLogger(__name__)
RUNNING = {"PENDING", "RUNNING"}
FAILED = {"FAILED", "CANCELLED"}


@dataclass
class ExtractStatus:
    state: Literal["pending", "complete", "failed"]
    result: object = None
    metadata: object = None


async def start_extract(client: AsyncLlamaCloud, s: Settings, file_id: str, doc: ValidDocument) -> str:
    try:
        job = await client.extract.create(file_input=file_id, configuration=extract_configuration(s, doc.pages if doc.kind == "pdf" else None))
    except APIError as e:
        log.error("LlamaExtract create: %s", e)
        raise InvoiceError("LlamaCloud no pudo iniciar la extracción. Intentá más tarde.") from e
    return job.id


async def get_extract(client: AsyncLlamaCloud, job_id: str) -> ExtractStatus:
    try:
        job = await client.extract.get(job_id, expand=["extract_metadata"])
    except APIError as e:
        log.error("LlamaExtract get: %s", e)
        raise InvoiceError("No se pudo consultar el estado de la extracción.") from e
    if job.status in FAILED:
        log.error("LlamaExtract %s %s: %s", job_id, job.status, job.error_message)
        return ExtractStatus("failed")
    if job.status != "COMPLETED":
        return ExtractStatus("pending")
    meta = job.extract_metadata
    return ExtractStatus("complete", job.extract_result, meta.model_dump() if hasattr(meta, "model_dump") else meta)
