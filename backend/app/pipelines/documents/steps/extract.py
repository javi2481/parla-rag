"""Paso 3 · Extracción con LlamaExtract v2.

Primero se crea el job (start_extract) y después se consulta su estado hasta que termina (get_extract).
"""
import logging
from dataclasses import dataclass
from typing import Literal

from llama_cloud import APIError, AsyncLlamaCloud

from ..errors import DocumentError
from ..schema import extract_configuration
from ..settings import DocumentsSettings
from .validate import ValidDocument

log = logging.getLogger(__name__)

FAILED_STATES = {"FAILED", "CANCELLED"}


@dataclass
class ExtractStatus:
    state: Literal["pending", "complete", "failed"]
    result: object = None    # los datos extraídos (cuando terminó bien)
    metadata: object = None  # citas y confianza por campo


# Crea el job de extracción para un archivo ya subido y devuelve el ID del job.
async def start_extract(client: AsyncLlamaCloud, settings: DocumentsSettings, file_id: str, doc: ValidDocument) -> str:
    if doc.kind == "pdf":
        page_count = doc.pages
    else:
        page_count = None
    configuration = extract_configuration(settings, page_count)

    try:
        job = await client.extract.create(file_input=file_id, configuration=configuration)
    except APIError as e:
        log.error("LlamaExtract create: %s", e)
        raise DocumentError("LlamaCloud no pudo iniciar la extracción. Intentá más tarde.") from e
    return job.id


# Consulta el estado del job: si sigue corriendo, si falló o si terminó (con su resultado).
async def get_extract(client: AsyncLlamaCloud, job_id: str) -> ExtractStatus:
    try:
        job = await client.extract.get(job_id, expand=["extract_metadata"])
    except APIError as e:
        log.error("LlamaExtract get: %s", e)
        raise DocumentError("No se pudo consultar el estado de la extracción.") from e

    if job.status in FAILED_STATES:
        log.error("LlamaExtract %s %s: %s", job_id, job.status, job.error_message)
        return ExtractStatus("failed")

    if job.status != "COMPLETED":
        return ExtractStatus("pending")

    metadata = job.extract_metadata
    if hasattr(metadata, "model_dump"):
        metadata = metadata.model_dump()
    return ExtractStatus("complete", job.extract_result, metadata)
