"""Tickets opacos → job de LlamaCloud, en memoria. El navegador nunca ve los IDs del proveedor."""
import secrets
import time
from dataclasses import dataclass

JOB_TTL_S = 10 * 60


@dataclass
class Job:
    job_id: str
    file_id: str
    owner: str
    expires: float

    @property
    def expired(self) -> bool:
        return self.expires < time.time()


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def add(self, job_id: str, file_id: str, owner: str) -> str:
        self._purge()
        ticket = secrets.token_urlsafe(24)
        self._jobs[ticket] = Job(job_id, file_id, owner, time.time() + JOB_TTL_S)
        return ticket

    def get(self, ticket: str, owner: str) -> Job | None:
        job = self._jobs.get(ticket)
        return job if job and job.owner == owner else None

    def pop(self, ticket: str) -> None:
        self._jobs.pop(ticket, None)

    def _purge(self) -> None:
        for t in [t for t, j in self._jobs.items() if j.expired]:
            self._jobs.pop(t, None)
