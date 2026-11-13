"""El wizard de punta a punta (Subir → Parse) con un cliente de LlamaCloud falso: sin red ni créditos."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.settings import CoreSettings, get_core_settings
from app.main import app
from app.pipelines.documents.settings import DocumentsSettings, get_documents_settings


# Imita las respuestas del SDK: objetos con atributos y con model_dump().
class Obj(SimpleNamespace):
    # Devuelve el objeto como diccionario, igual que los modelos del SDK.
    def model_dump(self):
        result = {}
        for key, value in vars(self).items():
            result[key] = value.model_dump() if isinstance(value, Obj) else value
        return result


class FakeLlamaCloud:
    # Arranca con una lista de estados que va a devolver el job de parse, en orden.
    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.calls = []
        self.files = SimpleNamespace(create=self.upload, delete=self.delete_file)
        self.parsing = SimpleNamespace(create=self.create_parse, get=self.get_parse, delete=self.delete_parse)
        self.configurations = SimpleNamespace(create=self.save_configuration)

    # Imita files.create.
    async def upload(self, file, purpose):
        self.calls.append(("upload", file[0], purpose))
        return Obj(id="dfl-1", name=file[0])

    # Imita configurations.create.
    async def save_configuration(self, name, parameters):
        self.calls.append(("configuration", name, parameters["product_type"]))
        return Obj(id="cfg-1", name=name)

    # Imita parsing.create.
    async def create_parse(self, file_id, **request):
        self.calls.append(("parse", file_id, request["tier"]))
        return Obj(id="pjb-1", status="PENDING")

    # Imita parsing.get: sin expand devuelve el estado; con expand, el resultado completo.
    async def get_parse(self, job_id, expand=None):
        if expand is None:
            return Obj(job=Obj(status=self.statuses.pop(0)))
        return Obj(
            job=Obj(id=job_id, status="COMPLETED", usage={"credits": 21.0}),
            markdown={"pages": [{"page_number": 1, "markdown": "# Hola"}]},
            text={"pages": [{"page_number": 1, "text": "Hola mundo"}]},
            items={"pages": [{"items": [{"type": "heading"}]}]},
            metadata={"pages": [{"page_number": 1, "confidence": 1.0}], "document": {"confidence": 1.0}},
            forms=None, job_metadata={"latency": {"total_ms": 1000}},
            images_content_metadata=None, result_content_metadata=None,
        )

    # Imita parsing.delete.
    async def delete_parse(self, job_id):
        self.calls.append(("delete_parse", job_id))

    # Imita files.delete.
    async def delete_file(self, file_id):
        self.calls.append(("delete_file", file_id))

    # Imita close(), que la app llama al apagarse.
    async def close(self):
        pass


# Prepara la app con una carpeta-DB temporal, una API key falsa y el cliente falso.
@pytest.fixture
def setup(tmp_path):
    fake = FakeLlamaCloud(["RUNNING", "COMPLETED"])
    app.dependency_overrides[get_core_settings] = lambda: CoreSettings(data_dir=str(tmp_path), _env_file=None)
    app.dependency_overrides[get_documents_settings] = lambda: DocumentsSettings(llama_cloud_api_key="x", _env_file=None)
    with TestClient(app) as client:
        app.state.documents_client = fake
        yield client, fake, tmp_path
    app.dependency_overrides.clear()


# Sube, arranca Parse, consulta hasta que termina, descarga el .md y borra la corrida.
def test_upload_parse_and_delete(setup):
    client, fake, tmp_path = setup

    run = client.post("/api/documents/runs", files={"file": ("Comunicado.pdf", b"%PDF-1.7 ...", "application/pdf")}).json()
    upload, parse = run["steps"]
    assert upload["state"] == "done" and upload["file_id"] == "dfl-1"
    assert parse["state"] == "pending" and parse["locked"] is False

    run = client.post(f"/api/documents/runs/{run['id']}/steps/parse").json()
    assert run["steps"][1]["state"] == "running"
    assert run["steps"][1]["configuration_id"] == "cfg-1"
    assert ("configuration", "parla-parse-agentic-2026-10-16", "parse_v2") in fake.calls

    run = client.get(f"/api/documents/runs/{run['id']}/steps/parse").json()
    assert run["steps"][1]["state"] == "running" and run["steps"][1]["job_status"] == "RUNNING"

    run = client.get(f"/api/documents/runs/{run['id']}/steps/parse").json()
    parse = run["steps"][1]
    assert parse["state"] == "done" and parse["credits"] == 21.0
    assert run["total_credits"] == 21.0
    assert parse["interpretacion"] and parse["metricas"]
    assert "2_parse/document.md" in [f["path"] for f in parse["files"]]

    markdown = client.get(f"/api/documents/runs/{run['id']}/files/2_parse/document.md")
    assert "# Hola" in markdown.text

    assert client.delete(f"/api/documents/runs/{run['id']}").status_code == 200
    assert client.get("/api/documents/runs").json() == []
    assert ("delete_parse", "pjb-1") in fake.calls and ("delete_file", "dfl-1") in fake.calls


# Parse no se puede arrancar dos veces mientras corre.
def test_cannot_start_running_step_twice(setup):
    client, _, _ = setup
    run = client.post("/api/documents/runs", files={"file": ("a.pdf", b"%PDF-1.7", "application/pdf")}).json()
    assert client.post(f"/api/documents/runs/{run['id']}/steps/parse").status_code == 200
    assert client.post(f"/api/documents/runs/{run['id']}/steps/parse").status_code == 409
