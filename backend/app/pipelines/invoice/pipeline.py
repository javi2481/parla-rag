"""Orquestador del pipeline de facturas. Cada paso vive en steps/ y se encadena acá, en orden."""
from dataclasses import dataclass, field

from llama_cloud import AsyncLlamaCloud

from app.core.config import Settings

from .errors import InvoiceError
from .jobs import JobStore
from .steps.cleanup import cleanup
from .steps.extract import get_extract, start_extract
from .steps.postprocess import citation_boxes, field_confidence, normalize_result
from .steps.upload import upload
from .steps.validate import validate


@dataclass
class InvoiceResult:
    status: str  # "pending" | "complete"
    data: dict | None = None
    boxes: list = field(default_factory=list)
    confidence: dict = field(default_factory=dict)


class InvoicePipeline:
    def __init__(self, client: AsyncLlamaCloud, settings: Settings):
        self.client, self.settings, self.jobs = client, settings, JobStore()

    async def start(self, filename: str, data: bytes, owner: str, before_upload=None) -> str:
        """Pasos 1–3: valida, sube y crea el job. Devuelve un ticket para consultar."""
        doc = validate(filename, data)                                  # 1
        if before_upload:
            before_upload()  # p. ej. el límite de uso: solo cuenta archivos válidos
        file_id = await upload(self.client, doc)                        # 2
        try:
            job_id = await start_extract(self.client, self.settings, file_id, doc)  # 3
        except Exception:
            await cleanup(self.client, file_id)                         # 5
            raise
        return self.jobs.add(job_id, file_id, owner)

    async def poll(self, ticket: str, owner: str) -> InvoiceResult:
        """Paso 3 (polling) → 4 → 5 cuando termina."""
        job = self.jobs.get(ticket, owner)
        if not job:
            raise LookupError("Solicitud no encontrada o vencida.")
        if job.expired:
            self.jobs.pop(ticket)
            await cleanup(self.client, job.file_id, job.job_id)
            raise TimeoutError("El procesamiento superó el tiempo permitido.")
        status = await get_extract(self.client, job.job_id)             # 3
        if status.state == "pending":
            return InvoiceResult("pending")
        self.jobs.pop(ticket)
        try:
            if status.state == "failed":
                raise InvoiceError("No se pudo extraer esta factura.")
            return InvoiceResult(                                       # 4
                "complete",
                data=normalize_result(status.result),
                boxes=citation_boxes(status.metadata),
                confidence=field_confidence(status.metadata),
            )
        finally:
            await cleanup(self.client, job.file_id, job.job_id)         # 5
