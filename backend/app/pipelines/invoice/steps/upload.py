"""Paso 2 · Subida a LlamaCloud Files (POST /api/v1/beta/files, purpose="extract")."""
import logging

from llama_cloud import APIError, AsyncLlamaCloud

from ..errors import InvoiceError
from .validate import ValidDocument

log = logging.getLogger(__name__)


async def upload(client: AsyncLlamaCloud, doc: ValidDocument) -> str:
    try:
        file = await client.files.create(file=(doc.filename, doc.data, doc.mime), purpose="extract")
    except APIError as e:
        log.error("LlamaCloud upload: %s", e)
        raise InvoiceError("LlamaCloud no pudo recibir el archivo. Intentá más tarde.") from e
    return file.id
