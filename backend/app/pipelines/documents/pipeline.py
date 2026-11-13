"""Orquestador del pipeline de documentos: encadena los pasos de steps/, en orden.

    start()  →  1 validar · 2 subir · 3 crear el job de extracción
    poll()   →  3 consultar el job · 4 post-procesar · 5 limpiar
"""
from dataclasses import dataclass, field

from llama_cloud import AsyncLlamaCloud

from .client import make_client
from .errors import DocumentError
from .jobs import JobStore
from .settings import DocumentsSettings
from .steps.cleanup import cleanup
from .steps.extract import get_extract, start_extract
from .steps.postprocess import citation_boxes, field_confidence, normalize_result
from .steps.upload import upload
from .steps.validate import validate


@dataclass
class DocumentResult:
    status: str                                       # "pending" o "complete"
    data: dict | None = None                          # los campos extraídos
    boxes: list = field(default_factory=list)         # dónde está cada dato en el documento
    confidence: dict = field(default_factory=dict)    # confianza por campo


class DocumentPipeline:
    # Guarda el cliente de LlamaCloud, la configuración y la lista de jobs en curso.
    def __init__(self, client: AsyncLlamaCloud, settings: DocumentsSettings):
        self.client = client
        self.settings = settings
        self.jobs = JobStore()

    # Pasos 1 a 3: valida el archivo, lo sube y crea el job de extracción.
    # Devuelve un ticket para consultar después cómo va.
    # `before_upload` se llama justo antes de subir (por ejemplo, para contar el límite de uso).
    async def start(self, filename: str, data: bytes, owner: str, before_upload=None) -> str:
        doc = validate(filename, data)                                   # 1
        if before_upload:
            before_upload()  # solo cuentan los archivos válidos

        file_id = await upload(self.client, doc)                         # 2
        try:
            job_id = await start_extract(self.client, self.settings, file_id, doc)  # 3
        except Exception:
            await cleanup(self.client, file_id)                          # 5
            raise

        return self.jobs.add(job_id, file_id, owner)

    # Consulta un ticket. Si la extracción terminó, post-procesa el resultado (paso 4)
    # y limpia en LlamaCloud (paso 5). Si todavía no terminó, devuelve "pending".
    async def poll(self, ticket: str, owner: str) -> DocumentResult:
        job = self.jobs.get(ticket, owner)
        if job is None:
            raise LookupError("Solicitud no encontrada o vencida.")

        if job.expired:
            self.jobs.pop(ticket)
            await cleanup(self.client, job.file_id, job.job_id)
            raise TimeoutError("El procesamiento superó el tiempo permitido.")

        status = await get_extract(self.client, job.job_id)              # 3
        if status.state == "pending":
            return DocumentResult("pending")

        # Terminó (bien o mal): el ticket ya no sirve y siempre se limpia.
        self.jobs.pop(ticket)
        try:
            if status.state == "failed":
                raise DocumentError("No se pudo extraer este documento.")
            return DocumentResult(                                       # 4
                "complete",
                data=normalize_result(status.result),
                boxes=citation_boxes(status.metadata),
                confidence=field_confidence(status.metadata),
            )
        finally:
            await cleanup(self.client, job.file_id, job.job_id)          # 5

    # Cierra la conexión con LlamaCloud (se llama al apagar el servidor).
    async def close(self) -> None:
        await self.client.close()


# Crea el pipeline listo para usar, con su cliente de LlamaCloud.
def create_pipeline(settings: DocumentsSettings) -> DocumentPipeline:
    return DocumentPipeline(make_client(settings), settings)
