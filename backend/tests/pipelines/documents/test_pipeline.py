"""Pipeline completo con un cliente LlamaCloud falso (sin red ni créditos)."""
from types import SimpleNamespace

import pytest

from app.pipelines.documents.settings import DocumentsSettings
from app.pipelines.documents.errors import DocumentError
from app.pipelines.documents.pipeline import DocumentPipeline


class FakeClient:
    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.calls: list = []
        self.files = SimpleNamespace(create=self._upload, delete=self._delete_file)
        self.extract = SimpleNamespace(create=self._create, get=self._get, delete=self._delete_job)

    async def _upload(self, file, purpose):
        self.calls.append(("upload", file[0], file[2], purpose))
        return SimpleNamespace(id="dfl-1")

    async def _create(self, file_input, configuration):
        self.calls.append(("create", file_input, configuration["tier"], configuration.get("target_pages"), configuration["confidence_scores"]))
        return SimpleNamespace(id="ext-1")

    async def _get(self, job_id, expand):
        st = self.statuses.pop(0)
        meta = {"field_metadata": {"document_metadata": {"total": {"confidence": 0.9}}}}
        return SimpleNamespace(status=st, error_message="boom" if st == "FAILED" else None,
                               extract_result={"total": "$**100"} if st == "COMPLETED" else None, extract_metadata=meta)

    async def _delete_file(self, file_id):
        self.calls.append(("delete_file", file_id))

    async def _delete_job(self, job_id):
        self.calls.append(("delete_job", job_id))


@pytest.fixture
def settings():
    return DocumentsSettings(llama_cloud_api_key="x", _env_file=None)


async def test_runs_all_steps_in_order(pdf, settings):
    client = FakeClient(["PENDING", "RUNNING", "COMPLETED"])
    p = DocumentPipeline(client, settings)
    ticket = await p.start("f.pdf", pdf(2), owner="ip")
    assert (await p.poll(ticket, "ip")).status == "pending"
    assert (await p.poll(ticket, "ip")).status == "pending"
    r = await p.poll(ticket, "ip")
    assert r.status == "complete" and r.data["total"] == "$ 100" and r.confidence == {"total": 0.9}
    assert client.calls == [
        ("upload", "comprobante.pdf", "application/pdf", "extract"),
        ("create", "dfl-1", "agentic", "1-2", True),
        ("delete_file", "dfl-1"), ("delete_job", "ext-1"),
    ]
    with pytest.raises(LookupError):
        await p.poll(ticket, "ip")


async def test_other_owner_cannot_poll(pdf, settings):
    p = DocumentPipeline(FakeClient(["COMPLETED"]), settings)
    ticket = await p.start("f.pdf", pdf(), owner="a")
    with pytest.raises(LookupError):
        await p.poll(ticket, "b")


async def test_failed_job_is_cleaned_up(pdf, settings):
    client = FakeClient(["FAILED"])
    p = DocumentPipeline(client, settings)
    ticket = await p.start("f.pdf", pdf(), owner="ip")
    with pytest.raises(DocumentError):
        await p.poll(ticket, "ip")
    assert ("delete_job", "ext-1") in client.calls


async def test_invalid_file_never_reaches_llamacloud(settings):
    client = FakeClient([])
    with pytest.raises(DocumentError):
        await DocumentPipeline(client, settings).start("f.pdf", b"MZ......", owner="ip")
    assert client.calls == []
