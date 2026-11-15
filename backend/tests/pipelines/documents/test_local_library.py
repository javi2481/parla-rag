"""Bibliotecas locales (LlamaIndex + Voyage AI + DeepSeek) con modelos falsos: sin red ni créditos."""
import json

import pytest
from fastapi.testclient import TestClient
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

from app.core.settings import CoreSettings, get_core_settings
from app.main import app
from app.pipelines.documents import local_library
from app.pipelines.documents.settings import DocumentsSettings, get_documents_settings
from tests.pipelines.documents.test_wizard_flow import FakeLlamaCloud


class FakeReranker:
    # Imita al reranker de Voyage: deja los primeros top_n y les pone un score que baja de a 0,1.
    def __init__(self, top_n):
        self.top_n = top_n

    def postprocess_nodes(self, nodes, query):
        kept = nodes[: self.top_n]
        for i, node in enumerate(kept):
            node.score = 0.9 - i / 10
        return kept

    # La versión async, que es la que usa el chat engine.
    async def apostprocess_nodes(self, nodes, query_bundle=None, query_str=None):
        return self.postprocess_nodes(nodes, query_bundle)


class ParseWithPages(FakeLlamaCloud):
    # Un parse de dos páginas, para que la biblioteca tenga algo que indexar.
    async def get_parse(self, job_id, expand=None):
        result = await super().get_parse(job_id, expand)
        if expand is not None:
            result.markdown = {"pages": [{"page_number": 1, "markdown": "# Resultados\nEl resultado neto fue 22.162."},
                                         {"page_number": 2, "markdown": "Ingresos de la depositaria: +46%."}]}
        return result


@pytest.fixture
def setup(tmp_path, monkeypatch):
    fake = ParseWithPages(["COMPLETED"])
    monkeypatch.setattr(local_library, "make_embed_model", lambda settings: MockEmbedding(embed_dim=8))
    monkeypatch.setattr(local_library, "make_reranker", lambda settings, top_n: FakeReranker(top_n))
    monkeypatch.setattr(local_library, "make_llm", lambda settings: MockLLM(max_tokens=5))
    monkeypatch.setattr(local_library, "prepare_nltk", lambda data_dir: None)  # sin bajar nada de internet
    app.dependency_overrides[get_core_settings] = lambda: CoreSettings(data_dir=str(tmp_path), _env_file=None)
    settings = DocumentsSettings(llama_cloud_api_key="x", voyage_api_key="v", library_engine="local", _env_file=None)
    app.dependency_overrides[get_documents_settings] = lambda: settings
    with TestClient(app) as client:
        app.state.documents_client = fake
        yield client, settings, tmp_path
    app.dependency_overrides.clear()


def test_local_library_end_to_end(setup):
    client, settings, tmp_path = setup
    run = client.post("/api/documents/runs", files={"file": ("EEFF.pdf", b"%PDF-1.7", "application/pdf")}).json()
    client.post(f"/api/documents/runs/{run['id']}/steps/parse")
    client.get(f"/api/documents/runs/{run['id']}/steps/parse")

    # Crear: solo la carpeta, nada en LlamaCloud.
    library = client.post("/api/documents/libraries", json={"name": "BYMA 3T26"}).json()
    assert library["engine"] == "local" and library["embed_model"] == "voyage-4"
    base = f"/api/documents/libraries/{library['id']}"
    folder = tmp_path / "documents" / "libraries" / library["id"]

    # Agregar: se copia el Markdown de cada página del parse (no se vuelve a parsear).
    library = client.post(f"{base}/documents", json={"run_id": run["id"]}).json()
    assert library["documents"][0]["pages"] == 2 and library["needs_sync"] is True
    assert (folder / "documents" / f"{run['id']}.json").is_file()

    # Sincronizar: el índice se arma en el momento y queda guardado en la carpeta.
    sync = client.post(f"{base}/sync").json()["steps"]["sync"]
    assert sync["state"] == "done"
    assert {"label": "Páginas indexadas", "value": 2} in sync["metricas"]
    assert (folder / "index" / "docstore.json").is_file()

    # Buscar: vuelve con el mismo formato que LlamaCloud, con la página y la corrida para mostrar la captura.
    result = client.post(f"{base}/search", json={"query": "resultado neto", "top_k": 2}).json()
    first = result["response"]["results"][0]
    assert first["rerank_score"] == 0.9 and first["metadata"]["corrida"] == run["id"]
    assert first["static_fields"]["page_range_start"] in (1, 2)

    # Filtrar por metadata (igualdad) y rechazar lo que el índice local no soporta.
    filtered = client.post(f"{base}/search", json={"query": "x", "filters": {"pagina": {"operator": "eq", "value": 2}}}).json()
    assert [r["metadata"]["pagina"] for r in filtered["response"]["results"]] == [2]
    assert client.post(f"{base}/search", json={"query": "x", "filters": {"pagina": {"operator": "gt", "value": 1}}}).status_code == 409

    # Sin la key de DeepSeek, el chat avisa qué falta.
    with client.stream("POST", f"{base}/chat", json={"prompt": "hola"}) as response:
        assert "DEEPSEEK_API_KEY" in "".join(response.iter_text())

    # Con la key: llegan la búsqueda, las páginas que encontró, la respuesta en pedacitos y el uso. Todo queda guardado.
    settings.deepseek_api_key = "d"
    for prompt in ("¿Cuál fue el resultado neto?", "¿Y los ingresos?"):
        with client.stream("POST", f"{base}/chat", json={"prompt": prompt}) as response:
            events = [json.loads(line[5:]) for line in response.iter_lines() if line.startswith("data:")]
        types = [event["type"] for event in events]
        assert types[:2] == ["tool_call", "tool_result"] and "text_delta" in types and types[-1] == "stop"
        assert events[1]["result"][0]["pagina"] in (1, 2) and events[1]["result"][0]["documento"] == "EEFF.pdf"
    second = json.loads((folder / "chats" / "local" / "turno_2.json").read_text())
    assert second["answer"] and second["request"]["historial"] == 1 and second["sources"]
    # Con historial, el modelo primero reescribe la pregunta y lo que se busca es la pregunta reescrita.
    assert second["searches"][0]["consulta"] != "¿Y los ingresos?" and second["usage"]["modelo"] == "deepseek-flash"
    turns = client.get(base).json()["turns"]
    assert [turn["prompt"] for turn in turns] == ["¿Cuál fue el resultado neto?", "¿Y los ingresos?"]

    # Repetir la sincronización guarda el índice anterior en el historial; borrar la biblioteca borra la carpeta.
    client.post(f"{base}/sync")
    assert any(p.name.startswith("index_") for p in (folder / "historial").iterdir())
    client.delete(base)
    assert not folder.exists()
