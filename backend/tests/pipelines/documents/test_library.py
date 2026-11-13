"""Bibliotecas de punta a punta con un LlamaCloud falso: crear, agregar, sincronizar, buscar, chatear y borrar."""
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.settings import CoreSettings, get_core_settings
from app.main import app
from app.pipelines.documents.settings import DocumentsSettings, get_documents_settings

from tests.pipelines.documents.test_wizard_flow import FakeLlamaCloud, Obj


class FakeLibraryCloud(FakeLlamaCloud):
    # Suma al cliente falso del wizard lo que usan las bibliotecas.
    def __init__(self):
        super().__init__(["COMPLETED"])
        self.index_checks = 0
        self.beta = SimpleNamespace(directories=SimpleNamespace(
            create=self.create_directory, delete=self.delete_thing,
            files=SimpleNamespace(add=self.add_file, delete=self.delete_dir_file)))
        self.indexes = SimpleNamespace(create=self.create_index, get=self.get_index, sync=self.sync_index, delete=self.delete_thing)
        self.retrieval = SimpleNamespace(retrieve=self.retrieve)
        self.chat = SimpleNamespace(create=self.create_chat, retrieve=self.chat_retrieve, get_summary=self.chat_summary,
                                    delete=self.delete_thing, with_streaming_response=SimpleNamespace(stream=self.chat_stream))
        self.parsing.list = self.list_parses

    async def create_directory(self, name, description=None):
        return Obj(id="dir-1", name=name)

    async def add_file(self, directory_id, file_id, display_name, unique_id, metadata):
        self.calls.append(("add_file", directory_id, file_id, unique_id, metadata))
        return Obj(id="dfi-1", file_id=file_id, directory_id=directory_id, unique_id=unique_id, metadata=metadata)

    async def delete_dir_file(self, directory_file_id, directory_id):
        self.calls.append(("delete_dir_file", directory_file_id))

    async def create_index(self, **request):
        self.calls.append(("create_index", request["products"][0]["product_config_id"], request["store_attachments"]))
        return Obj(id="idx-1", name=request["name"])

    # El índice: antes de sincronizar no tiene fecha; durante la sincronización dice que está en curso; después, listo.
    async def get_index(self, index_id, expand=None):
        self.index_checks += 1
        if self.index_checks == 1:
            return Obj(id=index_id, last_synced_at=None, sync_in_progress=False, metadata={"status": "ready"})
        if self.index_checks == 2:
            return Obj(id=index_id, last_synced_at=None, sync_in_progress=True, metadata={"status": "syncing"})
        return Obj(id=index_id, last_synced_at="2026-11-13T23:00:00", sync_in_progress=False, metadata={"status": "ready"})

    async def sync_index(self, index_id):
        self.calls.append(("sync", index_id))
        return Obj(id=index_id)

    # parsing.list es un paginador: se recorre con "async for".
    def list_parses(self, created_at_on_or_after=None):
        async def jobs():
            yield Obj(id="pjb-sync", status="COMPLETED", usage={"credits": 15.0})
        return jobs()

    async def retrieve(self, index_id, query, top_k, custom_filters=None):
        self.calls.append(("retrieve", query, custom_filters))
        return Obj(results=[{"content": "Resultado neto 22.161.940", "score": 0.9, "rerank_score": 0.8,
                             "metadata": {"nombre": "EEFF.pdf", "corrida": "x"}, "static_fields": {"page_range_start": 4}}])

    async def create_chat(self, index_ids):
        return Obj(id="chat-1", index_ids=index_ids)

    # chat.with_streaming_response.stream: un "with" que devuelve las líneas de Server-Sent Events.
    @asynccontextmanager
    async def chat_stream(self, session_id, index_ids, prompt):
        async def lines():
            for line in ['data: {"type": "text_delta", "content": "El resultado "}', "",
                         'data: {"type": "text_delta", "content": "es 22.161.940."}',
                         'data: {"type": "stop", "is_error": false, "usage": {"turns": 1}}']:
                yield line
        yield SimpleNamespace(iter_lines=lines)

    async def chat_retrieve(self, session_id):
        return Obj(session_id=session_id, events=[])

    async def chat_summary(self, session_id):
        return Obj(session_id=session_id, job_metadata={"total_input_tokens": 100})

    async def delete_thing(self, thing_id):
        self.calls.append(("delete", thing_id))


@pytest.fixture
def setup(tmp_path):
    fake = FakeLibraryCloud()
    app.dependency_overrides[get_core_settings] = lambda: CoreSettings(data_dir=str(tmp_path), _env_file=None)
    app.dependency_overrides[get_documents_settings] = lambda: DocumentsSettings(llama_cloud_api_key="x", _env_file=None)
    with TestClient(app) as client:
        app.state.documents_client = fake
        yield client, fake
    app.dependency_overrides.clear()


def test_library_end_to_end(setup):
    client, fake = setup

    # Una corrida del wizard con el parse terminado.
    run = client.post("/api/documents/runs", files={"file": ("EEFF.pdf", b"%PDF-1.7", "application/pdf")}).json()
    client.post(f"/api/documents/runs/{run['id']}/steps/parse")
    client.get(f"/api/documents/runs/{run['id']}/steps/parse")

    # Crear: directorio + índice con NUESTRA configuración de parse y las capturas e items guardados.
    library = client.post("/api/documents/libraries", json={"name": "BYMA 3T26"}).json()
    assert library["index_id"] == "idx-1" and library["directory_id"] == "dir-1"
    assert ("create_index", "cfg-parse_v2", ["screenshots", "items"]) in fake.calls
    base = f"/api/documents/libraries/{library['id']}"

    # Agregar: el mismo file_id (no se vuelve a subir), con la corrida como unique_id.
    library = client.post(f"{base}/documents", json={"run_id": run["id"]}).json()
    assert library["needs_sync"] is True
    _, _, file_id, unique_id, metadata = [c for c in fake.calls if c[0] == "add_file"][0]
    assert file_id == "dfl-1" and unique_id == run["id"] and metadata["nombre"] == "EEFF.pdf"
    assert client.post(f"{base}/documents", json={"run_id": run["id"]}).status_code == 409

    # Sincronizar: sigue corriendo mientras el índice está en curso; al terminar cuenta los parses que creó LlamaCloud.
    library = client.post(f"{base}/sync").json()
    assert library["steps"]["sync"]["state"] == "running"
    assert client.get(f"{base}/sync").json()["steps"]["sync"]["state"] == "running"
    sync = client.get(f"{base}/sync").json()["steps"]["sync"]
    assert sync["state"] == "done" and sync["credits"] == 15.0
    assert any("creó 1 parse" in s for s in sync["interpretacion"])

    # Buscar, con filtro por metadata.
    result = client.post(f"{base}/search", json={"query": "resultado neto", "filters": {"tipo": {"operator": "eq", "value": "x"}}}).json()
    assert result["response"]["results"][0]["score"] == 0.9
    assert "Encontró 1 fragmentos de 1 documento(s): EEFF.pdf." in result["interpretacion"]

    # Chatear: los eventos llegan tal cual y el turno queda guardado.
    with client.stream("POST", f"{base}/chat", json={"prompt": "¿Cuál fue el resultado neto?"}) as response:
        text = "".join(response.iter_text())
    assert "22.161.940" in text
    library = client.get(base).json()
    assert len(library["turns"]) == 1 and library["searches"]
    assert [e["content"] for e in library["turns"][0]["events"] if e["type"] == "text_delta"] == ["El resultado ", "es 22.161.940."]

    # Sacar el documento y borrar la biblioteca (índice, directorio y chat en LlamaCloud).
    library = client.delete(f"{base}/documents/{run['id']}").json()
    assert library["documents"] == [] and library["needs_sync"] is True
    client.delete(base)
    assert all(call in fake.calls for call in [("delete", "idx-1"), ("delete", "dir-1"), ("delete", "chat-1")])
    assert client.get("/api/documents/libraries").json() == []
