"""Guarda en memoria qué ticket corresponde a qué job de LlamaCloud.

El navegador solo ve un ticket al azar, nunca los IDs internos del proveedor.
Cada ticket vence a los 10 minutos.
"""
import secrets
import time
from dataclasses import dataclass

JOB_TTL_S = 10 * 60


@dataclass
class Job:
    job_id: str    # ID del job de extracción en LlamaCloud
    file_id: str   # ID del archivo subido a LlamaCloud
    owner: str     # IP de quien lo pidió: solo esa IP puede consultarlo
    expires: float  # momento (en segundos) en que vence

    # Dice si el job ya venció.
    @property
    def expired(self) -> bool:
        return self.expires < time.time()


class JobStore:
    # Arranca con la lista de jobs vacía.
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    # Guarda un job nuevo y devuelve el ticket que se le da al navegador.
    def add(self, job_id: str, file_id: str, owner: str) -> str:
        self._remove_expired()
        ticket = secrets.token_urlsafe(24)
        self._jobs[ticket] = Job(job_id, file_id, owner, time.time() + JOB_TTL_S)
        return ticket

    # Busca el job de un ticket. Devuelve None si no existe o si es de otra IP.
    def get(self, ticket: str, owner: str) -> Job | None:
        job = self._jobs.get(ticket)
        if job is None or job.owner != owner:
            return None
        return job

    # Saca un ticket de la lista (cuando el job ya terminó).
    def pop(self, ticket: str) -> None:
        self._jobs.pop(ticket, None)

    # Borra todos los tickets vencidos.
    def _remove_expired(self) -> None:
        expired = [ticket for ticket, job in self._jobs.items() if job.expired]
        for ticket in expired:
            self._jobs.pop(ticket, None)
