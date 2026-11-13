"""El wizard de punta a punta (Subir → Parse → Split → Classify → Schema → Extract) con un cliente de LlamaCloud falso: sin red ni créditos."""
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
        self.split = SimpleNamespace(create=self.create_split, get=self.get_split, delete=self.delete_job)
        self.classify = SimpleNamespace(create=self.create_classify, get=self.get_classify, delete=self.delete_job)
        self.extract = SimpleNamespace(create=self.create_extract, get=self.get_extract, delete=self.delete_job,
                                       generate_schema=self.generate_schema, validate_schema=self.validate_schema)

    # Imita files.create.
    async def upload(self, file, purpose):
        self.calls.append(("upload", file[0], purpose))
        return Obj(id="dfl-1", name=file[0])

    # Imita configurations.create: devuelve un ID distinto por producto.
    async def save_configuration(self, name, parameters):
        self.calls.append(("configuration", name, parameters["product_type"]))
        return Obj(id=f"cfg-{parameters['product_type']}", name=name, parameters=parameters)

    # Imita split.create y split.get (Split informa el estado en minúscula).
    async def create_split(self, file_input, configuration_id):
        self.calls.append(("split", file_input, configuration_id))
        return Obj(id="spl-1", status="pending")

    async def get_split(self, job_id):
        return Obj(id=job_id, status="completed", error_message=None,
                   categories=[{"name": "resumen", "description": "x"}, {"name": "notas", "description": "y"}],
                   result={"segments": [{"category": "resumen", "confidence_category": "high", "pages": [1, 2, 3]}]})

    # Imita classify.create y classify.get.
    async def create_classify(self, file_input, configuration_id):
        self.calls.append(("classify", file_input, configuration_id))
        return Obj(id="clj-1", status="PENDING")

    async def get_classify(self, job_id, expand=None):
        return Obj(id=job_id, status="COMPLETED", error_message=None, usage={"credits": 0},
                   result={"type": "comunicado_de_prensa", "confidence": 0.95, "reasoning": "Tiene encabezado de comunicado."})

    # Imita extract.generate_schema y extract.validate_schema.
    async def generate_schema(self, file_id, prompt):
        self.calls.append(("generate_schema", file_id))
        return Obj(name="auto", parameters={"data_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}}})

    async def validate_schema(self, data_schema):
        return Obj(data_schema=data_schema)

    # Imita extract.create y extract.get, con citas y confianza por campo.
    async def create_extract(self, file_input, **request):
        self.calls.append(("extract", file_input, request))
        return Obj(id="ext-1", status="PENDING")

    async def get_extract(self, job_id, expand=None):
        box = {"x": 10, "y": 20, "w": 30, "h": 5}
        citation = {"page": 3, "matching_text": "78,124", "bounding_boxes": [box], "page_dimensions": {"width": 612, "height": 792}}
        return Obj(id=job_id, status="COMPLETED", error_message=None,
                   usage={"credits": 30.0, "extract_credits": 9.0},
                   extract_result={"emisor": "BYMA", "ingresos": 78124, "gastos": None},
                   extract_metadata={"field_metadata": {"document_metadata": {
                       "emisor": {"citation": [], "confidence": 0.7},
                       "ingresos": {"citation": [citation], "confidence": 0.95},
                   }}})

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

    # Imita el delete de split, classify y extract.
    async def delete_job(self, job_id):
        self.calls.append(("delete_job", job_id))

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
    upload, parse = run["steps"][:2]
    assert upload["state"] == "done" and upload["file_id"] == "dfl-1"
    assert parse["state"] == "pending" and parse["locked"] is False

    run = client.post(f"/api/documents/runs/{run['id']}/steps/parse").json()
    assert run["steps"][1]["state"] == "running"
    assert run["steps"][1]["configuration_id"] == "cfg-parse_v2"
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


# Después del parse: Split, Classify, Schema (manual y automático) y Extract sobre una parte del Split.
def test_split_classify_schema_extract(setup):
    client, fake, tmp_path = setup
    run = client.post("/api/documents/runs", files={"file": ("EEFF.pdf", b"%PDF-1.7", "application/pdf")}).json()
    base = f"/api/documents/runs/{run['id']}"
    client.post(f"{base}/steps/parse")
    client.get(f"{base}/steps/parse")
    client.get(f"{base}/steps/parse")

    # Split con categorías propias: se guarda la configuración y se manda solo el ID del parse.
    categories = [{"name": "resumen", "description": "x"}, {"name": "notas", "description": "y"}]
    run = client.post(f"{base}/steps/split", json={"categories": categories}).json()
    assert ("split", "pjb-1", "cfg-split_v1") in fake.calls
    split = client.get(f"{base}/steps/split").json()["steps"][2]
    assert split["state"] == "done"
    assert "resumen: páginas 1-3 (confianza high)." in split["interpretacion"]
    assert "No encontró ninguna parte de: notas." in split["interpretacion"]

    # Classify: el razonamiento aparece en la interpretación.
    client.post(f"{base}/steps/classify")
    classify = client.get(f"{base}/steps/classify").json()["steps"][3]
    assert classify["state"] == "done" and classify["credits"] == 0
    assert any("Tiene encabezado de comunicado." in s for s in classify["interpretacion"])

    # Schema automático: lo propone el agente y se guarda con citas y confianza.
    schema = client.post(f"{base}/steps/schema", json={"mode": "auto", "prompt": "datos clave"}).json()["steps"][4]
    assert schema["state"] == "done" and schema["configuration_id"] == "cfg-extract_v2"
    assert ("generate_schema", "dfl-1") in fake.calls

    # Schema manual con la plantilla de por defecto.
    schema = client.post(f"{base}/steps/schema", json={"mode": "manual"}).json()["steps"][4]
    assert schema["state"] == "done" and schema["defaults"]["templates"]

    # Extract sobre las páginas de una parte del Split: la configuración va copiada con target_pages.
    client.post(f"{base}/steps/extract", json={"target_pages": "1-3", "segment": "resumen"})
    _, _, request = [c for c in fake.calls if c[0] == "extract"][0]
    assert request["configuration"]["target_pages"] == "1-3" and request["configuration"]["cite_sources"] is True
    extract = client.get(f"{base}/steps/extract").json()["steps"][5]
    assert extract["state"] == "done" and extract["credits"] == 9.0
    assert "Encontró valor para 2 de 11 campos del schema." in extract["interpretacion"]
    assert any(s.startswith("No los devolvió") and "razon_social" in s for s in extract["interpretacion"])
    assert "Revisá «emisor» (confianza 70%)." in extract["interpretacion"]
    assert any("no cita" in s and "emisor" in s for s in extract["interpretacion"])
    boxes = client.get(f"{base}/files/6_extract/boxes.json").json()
    assert boxes == [{"field": "ingresos", "value": 78124, "confidence": 0.95, "page": 3, "text": "78,124",
                      "page_width": 612, "page_height": 792, "x": 10, "y": 20, "w": 30, "h": 5}]

    # Repetir Split: lo anterior va al historial y los pasos siguientes vuelven a pendiente.
    client.post(f"{base}/steps/split", json={"categories": categories})
    run = client.get(f"{base}/steps/split").json()
    assert [step["state"] for step in run["steps"]] == ["done", "done", "done", "pending", "pending", "pending"]
    history = sorted(p.name.rsplit("_", 3)[0] for p in (tmp_path / "documents" / "runs" / run["id"] / "historial").iterdir())
    assert history == ["3_split", "4_classify", "5_schema", "5_schema", "6_extract"]

    # Al borrar la corrida se borran en LlamaCloud todos sus jobs.
    client.delete(base)
    assert ("delete_job", "spl-1") in fake.calls and ("delete_job", "clj-1") in fake.calls and ("delete_job", "ext-1") in fake.calls
