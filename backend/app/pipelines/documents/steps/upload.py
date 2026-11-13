"""Paso 2 · Subida del archivo a LlamaCloud Files (purpose="extract")."""
import logging

from llama_cloud import APIError, AsyncLlamaCloud

from ..errors import DocumentError
from .validate import ValidDocument

log = logging.getLogger(__name__)


# Sube el documento ya validado a LlamaCloud y devuelve el ID del archivo.
async def upload(client: AsyncLlamaCloud, doc: ValidDocument) -> str:
    try:
        file = await client.files.create(file=(doc.filename, doc.data, doc.mime), purpose="extract")
    except APIError as e:
        log.error("LlamaCloud upload: %s", e)
        raise DocumentError("LlamaCloud no pudo recibir el archivo. Intentá más tarde.") from e
    return file.id
