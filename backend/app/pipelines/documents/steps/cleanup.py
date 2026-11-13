"""Paso 5 · Limpieza: borra el archivo y el job de LlamaCloud.

Si algo falla al borrar, solo se anota en el log: nunca se rompe la respuesta al usuario.
"""
import logging

from llama_cloud import AsyncLlamaCloud

log = logging.getLogger(__name__)


# Borra el archivo subido y, si se indica, también el job de extracción.
async def cleanup(client: AsyncLlamaCloud, file_id: str, job_id: str | None = None) -> None:
    try:
        await client.files.delete(file_id)
    except Exception as e:
        log.warning("No se pudo borrar el archivo %s: %s", file_id, e)

    if job_id:
        try:
            await client.extract.delete(job_id)
        except Exception as e:
            log.warning("No se pudo borrar el job %s: %s", job_id, e)
