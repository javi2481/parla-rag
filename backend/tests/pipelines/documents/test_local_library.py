"""Bibliotecas locales (LlamaIndex + Voyage AI + OpenAI) con modelos falsos: sin red ni créditos."""
import json

import pytest
from fastapi.testclient import TestClient
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor

from app.core.settings import CoreSettings, get_core_settings
from app.main import app
from app.pipelines.documents.libraries.local import ai_models, retrieval, turn_recorder
from app.pipelines.documents.settings import DocumentsSettings, get_documents_settings
from tests.pipelines.documents.test_wizard_flow import FakeLlamaCloud


class FakeReranker(BaseNodePostprocessor):
    # Imita al reranker de Voyage (que también es un BaseNodePostprocessor de LlamaIndex):
    # deja los primeros top_n y les pone un score que baja de a 0,1.
    top_n: int = 2

    def _postprocess_nodes(self, nodes, query_bundle=None):
        kept = nodes[: self.top_n]
        for i, node in enumerate(kept):
            node.score = 0.9 - i / 10
        return kept


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
    monkeypatch.setattr(ai_models, "make_embed_model", lambda settings: MockEmbedding(embed_dim=8))
    monkeypatch.setattr(ai_models, "make_reranker", lambda settings, top_n: FakeReranker(top_n=top_n))
    monkeypatch.setattr(ai_models, "make_llm", lambda settings: MockLLM(max_tokens=5))
    monkeypatch.setattr(ai_models, "prepare_nltk", lambda data_dir: None)  # sin bajar nada de internet
    app.dependency_overrides[get_core_settings] = lambda: CoreSettings(data_dir=str(tmp_path), _env_file=None)
    settings = DocumentsSettings(llama_cloud_api_key="x", voyage_api_key="v", library_engine="local", _env_file=None)
    app.dependency_overrides[get_documents_settings] = lambda: settings
    with TestClient(app) as client:
        app.state.documents_client = fake
        yield client, settings, tmp_path
    app.dependency_overrides.clear()


def test_local_library_end_to_end(setup):
    client, settings, tmp_path = setup
    run = client.post("/api/documents/runs", files={"file": ("clase.pdf", b"%PDF-1.7", "application/pdf")}).json()
    client.post(f"/api/documents/runs/{run['id']}/steps/parse")
    client.get(f"/api/documents/runs/{run['id']}/steps/parse")

    # Crear: solo la carpeta, nada en LlamaCloud.
    library = client.post("/api/documents/libraries", json={"name": "Aprendizaje Automático II"}).json()
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
    # Un filtro mal armado (sin "operator"/"value") avisa con el formato correcto, no rompe con un 500.
    for malformed in ({"pagina": 2}, {"pagina": {"operator": "eq"}}):
        response = client.post(f"{base}/search", json={"query": "x", "filters": malformed})
        assert response.status_code == 409 and "mal armado" in response.json()["detail"]

    # Sin la key de OpenAI, el chat avisa qué falta.
    with client.stream("POST", f"{base}/chat", json={"prompt": "hola"}) as response:
        assert "OPENAI_API_KEY" in "".join(response.iter_text())

    # Con la key: llegan la búsqueda, las páginas que encontró, la respuesta en pedacitos y el uso. Todo queda guardado.
    settings.openai_api_key = "d"
    conversation_id = None  # la primera pregunta crea la conversación; la segunda va a la misma
    for prompt in ("¿Cuál fue el resultado neto?", "¿Y los ingresos?"):
        with client.stream("POST", f"{base}/chat", json={"prompt": prompt, "conversation_id": conversation_id}) as response:
            events = [json.loads(line[5:]) for line in response.iter_lines() if line.startswith("data:")]
        types = [event["type"] for event in events]
        assert types[:2] == ["tool_call", "tool_result"] and "text_delta" in types and types[-1] == "stop"
        assert events[1]["result"][0]["pagina"] in (1, 2) and events[1]["result"][0]["documento"] == "clase.pdf"
        conversation_id = events[-1]["conversation_id"]
    second = json.loads((folder / "chats" / "local" / conversation_id / "turno_2.json").read_text())
    assert second["answer"] and second["request"]["historial"] == 1 and second["sources"]
    # Con historial, el modelo primero reescribe la pregunta y lo que se busca es la pregunta reescrita.
    assert second["searches"][0]["consulta"] != "¿Y los ingresos?" and second["usage"]["modelo"] == "gpt-5-nano"
    turns = client.get(base).json()["turns"]
    assert [turn["prompt"] for turn in turns] == ["¿Cuál fue el resultado neto?", "¿Y los ingresos?"]

    # Repetir la sincronización guarda el índice anterior en el historial; borrar la biblioteca borra la carpeta.
    client.post(f"{base}/sync")
    assert any(p.name.startswith("index_") for p in (folder / "historial").iterdir())
    client.delete(base)
    assert not folder.exists()


class FakeJudge(MockLLM):
    # Imita al juez: aprueba la fidelidad ("YES") y le pone 4,5 de 5 a la corrección (con su explicación).
    async def apredict(self, prompt, **prompt_args):
        text = prompt.format(**prompt_args)
        return "4.5\nCoincide con la respuesta esperada." if "reference" in text.lower() else "YES"


def test_local_library_evals(setup, monkeypatch):
    from app.pipelines.documents.libraries.local import rag_evals

    client, settings, tmp_path = setup
    monkeypatch.setattr(rag_evals, "make_judge_llm", lambda settings: FakeJudge())
    run = client.post("/api/documents/runs", files={"file": ("clase.pdf", b"%PDF-1.7", "application/pdf")}).json()
    client.post(f"/api/documents/runs/{run['id']}/steps/parse")
    client.get(f"/api/documents/runs/{run['id']}/steps/parse")
    library = client.post("/api/documents/libraries", json={"name": "Prueba"}).json()
    base = f"/api/documents/libraries/{library['id']}"
    client.post(f"{base}/documents", json={"run_id": run["id"]})
    client.post(f"{base}/sync")

    # El set de preguntas vive junto a sus documentos, en samples/<conjunto>/evals/.
    questions = {"documentos": {"CLASE": "clase.pdf"}, "preguntas": [
        {"id": "neto", "tipo": "dato", "pregunta": "¿Resultado neto?", "respuesta_esperada": "22.162",
         "fuentes": [{"doc": "CLASE", "pagina": 1}, {"doc": "CLASE", "pagina": 2}]},
        {"id": "trampa", "tipo": "trampa", "pregunta": "¿Empleados?", "respuesta_esperada": "No está", "fuentes": []},
    ]}
    folder = tmp_path / "samples" / "prueba" / "evals"
    folder.mkdir(parents=True)
    (folder / "preguntas.json").write_text(json.dumps(questions))

    # Solo la búsqueda: no necesita OpenAI. Las dos páginas son fuente, así que el primer resultado ya es correcto.
    response = client.post(f"{base}/evals", json={"conjunto": "prueba", "candidatos": 4})
    assert response.status_code == 200, response.text
    result = response.json()
    neto, trampa = result["resultados"]
    assert neto["busqueda"]["hit_rate"] == 1 and neto["busqueda"]["mrr"] == 1
    assert "busqueda" not in trampa  # las trampas no tienen página correcta
    assert {"label": "Candidatos antes del reranker", "value": 4} in result["metricas"]

    # Con respuestas: pide la key de OpenAI y después el juez califica cada una.
    assert client.post(f"{base}/evals", json={"conjunto": "prueba", "respuestas": True}).status_code == 409
    settings.openai_api_key = "d"
    result = client.post(f"{base}/evals", json={"conjunto": "prueba", "respuestas": True}).json()
    answer = result["resultados"][0]["respuesta"]
    assert answer["fiel_a_los_fragmentos"] is True and answer["correccion"] == 4.5 and answer["correcta"] is True
    # El pedido anota el razonamiento del chat y el del juez, que son aparte.
    assert result["request"]["razonamiento"] == settings.library_reasoning_effort
    assert result["request"]["juez_razonamiento"] == settings.library_judge_reasoning_effort

    # Cada corrida queda en su carpeta: libraries/<id>/evals/<fecha>/.
    runs = sorted((tmp_path / "documents" / "libraries" / library["id"] / "evals").iterdir())
    assert {p.name for p in runs[-1].iterdir()} == {"request.json", "resultados.json", "metrics.json"}
    # La pantalla de la biblioteca trae las corridas guardadas, la más nueva primero y sin las llamadas crudas al modelo.
    saved = client.get(base).json()["evals"]
    assert len(saved) == 2 and saved[0]["request"]["respuestas"] is True and saved[0]["metricas"]
    assert "llamadas_al_modelo" not in saved[0]["resultados"][0]["respuesta"]
    assert client.post(f"{base}/evals", json={"conjunto": "no-existe"}).status_code == 404


# Una pregunta que cruza dos clases, pero solo una está en la biblioteca: la cobertura de clases es 0,5.
# Y con respuestas, cada una dice cuánto tardó.
def test_evals_miden_cobertura_y_tiempo(setup, monkeypatch):
    from app.pipelines.documents.libraries.local import rag_evals

    client, settings, tmp_path = setup
    monkeypatch.setattr(rag_evals, "make_judge_llm", lambda settings: FakeJudge())
    run = client.post("/api/documents/runs", files={"file": ("clase.pdf", b"%PDF-1.7", "application/pdf")}).json()
    client.post(f"/api/documents/runs/{run['id']}/steps/parse")
    client.get(f"/api/documents/runs/{run['id']}/steps/parse")
    library = client.post("/api/documents/libraries", json={"name": "Prueba"}).json()
    base = f"/api/documents/libraries/{library['id']}"
    client.post(f"{base}/documents", json={"run_id": run["id"]})
    client.post(f"{base}/sync")
    questions = {"documentos": {"CLASE": "clase.pdf", "OTRA": "otra.pdf"}, "preguntas": [
        {"id": "cruza", "tipo": "cruza_clases", "pregunta": "¿Qué tienen en común?", "respuesta_esperada": "Algo",
         "fuentes": [{"doc": "CLASE", "pagina": 1}, {"doc": "OTRA", "pagina": 3}]},
    ]}
    folder = tmp_path / "samples" / "cobertura" / "evals"
    folder.mkdir(parents=True)
    (folder / "preguntas.json").write_text(json.dumps(questions))

    resultado = client.post(f"{base}/evals", json={"conjunto": "cobertura"}).json()
    busqueda = resultado["resultados"][0]["busqueda"]
    assert busqueda["clases_esperadas"] == ["clase.pdf", "otra.pdf"]
    assert busqueda["clases_encontradas"] == ["clase.pdf"]
    assert busqueda["cobertura_de_clases"] == 0.5
    assert any(m["label"] == "Cobertura de clases (promedio)" and m["value"] == "0,5" for m in resultado["metricas"])

    settings.openai_api_key = "d"
    con_respuestas = client.post(f"{base}/evals", json={"conjunto": "cobertura", "respuestas": True}).json()
    assert con_respuestas["resultados"][0]["respuesta"]["segundos"] >= 0
    assert any(m["label"] == "Tiempo por respuesta (promedio / máximo)" for m in con_respuestas["metricas"])


# La búsqueda compartida (chat, búsqueda de prueba y evals) usa MMR solo si está configurado.
def test_make_retriever_usa_mmr_si_esta_configurado():
    from llama_index.core import VectorStoreIndex
    from llama_index.core.schema import TextNode
    from llama_index.core.vector_stores.types import VectorStoreQueryMode

    index = VectorStoreIndex([TextNode(text="hola")], embed_model=MockEmbedding(embed_dim=8))
    settings = DocumentsSettings(library_retrieval_mode="mmr", library_mmr_threshold=0.3, _env_file=None)
    retriever = retrieval.make_retriever(index, settings)
    assert retriever._vector_store_query_mode == VectorStoreQueryMode.MMR
    assert retriever._kwargs == {"mmr_threshold": 0.3}
    assert retriever._similarity_top_k == settings.library_chat_top_k * retrieval.CANDIDATES_PER_RESULT

    settings.library_retrieval_mode = "default"
    assert retrieval.make_retriever(index, settings, candidates=4)._vector_store_query_mode == VectorStoreQueryMode.DEFAULT

    settings.library_retrieval_mode = "otro"
    with pytest.raises(ValueError, match="mmr"):
        retrieval.make_retriever(index, settings)


# La híbrida junta vectores y BM25. Con filtros, BM25 solo ve las páginas que los cumplen;
# si ninguna cumple, queda la búsqueda por vectores sola (sin el error de BM25 con el índice vacío).
def test_busqueda_hibrida_respeta_los_filtros():
    from llama_index.core import VectorStoreIndex
    from llama_index.core.retrievers import QueryFusionRetriever
    from llama_index.core.schema import TextNode

    nodes = [TextNode(text="redes convolucionales", metadata={"pagina": 1}),
             TextNode(text="redes recurrentes", metadata={"pagina": 2})]
    index = VectorStoreIndex(nodes, embed_model=MockEmbedding(embed_dim=8))
    settings = DocumentsSettings(library_retrieval_mode="hibrida", _env_file=None)
    assert isinstance(retrieval.make_retriever(index, settings), QueryFusionRetriever)

    only_two = retrieval.to_filters({"pagina": {"operator": "eq", "value": 2}})
    found = retrieval.make_retriever(index, settings, filters=only_two).retrieve("redes")
    assert [node.node.metadata["pagina"] for node in found] == [2]

    nothing = retrieval.to_filters({"pagina": {"operator": "eq", "value": 9}})
    assert not isinstance(retrieval.make_retriever(index, settings, filters=nothing), QueryFusionRetriever)


# Los evals pueden probar otra cantidad de páginas y otro modo de búsqueda, y lo dejan anotado en la corrida.
def test_evals_aceptan_top_k_y_modo(setup):
    client, settings, tmp_path = setup
    run = client.post("/api/documents/runs", files={"file": ("clase.pdf", b"%PDF-1.7", "application/pdf")}).json()
    client.post(f"/api/documents/runs/{run['id']}/steps/parse")
    client.get(f"/api/documents/runs/{run['id']}/steps/parse")
    library = client.post("/api/documents/libraries", json={"name": "Prueba"}).json()
    base = f"/api/documents/libraries/{library['id']}"
    client.post(f"{base}/documents", json={"run_id": run["id"]})
    client.post(f"{base}/sync")
    questions = {"documentos": {"CLASE": "clase.pdf"}, "preguntas": [
        {"id": "neto", "tipo": "dato", "pregunta": "¿Resultado neto?", "respuesta_esperada": "22.162",
         "fuentes": [{"doc": "CLASE", "pagina": 1}]},
    ]}
    folder = tmp_path / "samples" / "modos" / "evals"
    folder.mkdir(parents=True)
    (folder / "preguntas.json").write_text(json.dumps(questions))

    result = client.post(f"{base}/evals", json={"conjunto": "modos", "top_k": 12, "modo": "mmr"}).json()
    assert result["request"]["top_k"] == 12 and result["request"]["modo"] == "mmr"
    assert result["request"]["candidatos"] == 12 * retrieval.CANDIDATES_PER_RESULT
    # La configuración del servidor no cambia: el cambio vale solo para esa corrida.
    assert settings.library_chat_top_k == 6 and settings.library_retrieval_mode == "hibrida"


# Arma una biblioteca local sincronizada con el parse de dos páginas y devuelve la ruta base de la API.
def synced_library(client) -> tuple[str, dict]:
    run = client.post("/api/documents/runs", files={"file": ("clase.pdf", b"%PDF-1.7", "application/pdf")}).json()
    client.post(f"/api/documents/runs/{run['id']}/steps/parse")
    client.get(f"/api/documents/runs/{run['id']}/steps/parse")
    library = client.post("/api/documents/libraries", json={"name": "Prueba"}).json()
    base = f"/api/documents/libraries/{library['id']}"
    client.post(f"{base}/documents", json={"run_id": run["id"]})
    client.post(f"{base}/sync")
    return base, library


# Manda una pregunta al chat y devuelve los eventos que llegaron en vivo.
def ask(client, base: str, prompt: str, conversation_id: str | None = None) -> list[dict]:
    with client.stream("POST", f"{base}/chat", json={"prompt": prompt, "conversation_id": conversation_id}) as response:
        return [json.loads(line[5:]) for line in response.iter_lines() if line.startswith("data:")]


# Cada conversación tiene su carpeta y su historial: lo que se habló en una no se ve en la otra.
def test_conversaciones_separadas(setup):
    client, settings, tmp_path = setup
    settings.openai_api_key = "d"
    base, library = synced_library(client)
    a = client.post(f"{base}/conversations").json()
    b = client.post(f"{base}/conversations").json()
    assert a["id"] != b["id"]

    ask(client, base, "¿Cuál fue el resultado neto de la empresa?", a["id"])
    ask(client, base, "¿Y los ingresos?", a["id"])
    stop = ask(client, base, "¿Qué dice la página dos?", b["id"])[-1]
    assert stop["type"] == "stop" and stop["conversation_id"] == b["id"]

    chats = tmp_path / "documents" / "libraries" / library["id"] / "chats" / "local"
    assert json.loads((chats / a["id"] / "turno_2.json").read_text())["request"]["historial"] == 1
    assert json.loads((chats / b["id"] / "turno_1.json").read_text())["request"]["historial"] == 0

    listed = client.get(f"{base}/conversations").json()
    assert [(c["id"], c["turnos"]) for c in listed] == [(a["id"], 2), (b["id"], 1)]
    assert listed[0]["titulo"] == "¿Cuál fue el resultado neto de"  # las primeras 6 palabras
    detail = client.get(f"{base}/conversations/{a['id']}").json()
    assert [t["prompt"] for t in detail["turns"]] == ["¿Cuál fue el resultado neto de la empresa?", "¿Y los ingresos?"]

    # Sin conversation_id se crea una nueva; con uno que no existe, 404.
    nueva = ask(client, base, "Hola")[-1]["conversation_id"]
    assert nueva not in (a["id"], b["id"])
    assert client.post(f"{base}/chat", json={"prompt": "x", "conversation_id": "no-existe"}).status_code == 404
    # La pestaña Bibliotecas sigue viendo todos los turnos.
    assert len(client.get(base).json()["turns"]) == 4


# Cerrar una conversación la saca de la lista, pero no borra nada del disco.
def test_conversacion_cerrada_no_se_lista(setup):
    client, settings, tmp_path = setup
    base, library = synced_library(client)
    vacia = client.post(f"{base}/conversations").json()
    otra = client.post(f"{base}/conversations").json()
    assert client.get(f"{base}/conversations").json()[0]["titulo"] == "Conversación nueva"

    assert client.post(f"{base}/conversations/{vacia['id']}/close").json()["cerrada"] is True
    assert [c["id"] for c in client.get(f"{base}/conversations").json()] == [otra["id"]]
    assert (tmp_path / "documents" / "libraries" / library["id"] / "chats" / "local" / vacia["id"] / "conversacion.json").is_file()
    assert client.post(f"{base}/conversations/no-existe/close").status_code == 404
    assert client.get(f"{base}/conversations/..%2F..%2Fx").status_code == 404


# Manda una pregunta con filtros y devuelve los eventos.
def ask_filtered(client, base: str, prompt: str, filters: dict) -> list[dict]:
    with client.stream("POST", f"{base}/chat", json={"prompt": prompt, "filters": filters}) as response:
        return [json.loads(line[5:]) for line in response.iter_lines() if line.startswith("data:")]


# Con un filtro, el chat solo usa las páginas que cumplen (acá, solo la página 2) y el filtro queda en el turno.
def test_chat_con_filtro_solo_usa_esa_clase(setup):
    client, settings, tmp_path = setup
    settings.openai_api_key = "d"
    base, library = synced_library(client)
    filters = {"pagina": {"operator": "eq", "value": 2}}
    events = ask_filtered(client, base, "¿Qué pasó con los ingresos?", filters)
    assert [source["pagina"] for source in events[1]["result"]] == [2]
    folder = tmp_path / "documents" / "libraries" / library["id"] / "chats" / "local" / events[-1]["conversation_id"]
    assert json.loads((folder / "turno_1.json").read_text())["request"]["filters"] == filters

    # Un filtro mal armado se rechaza antes de empezar, como en la búsqueda de prueba.
    response = client.post(f"{base}/chat", json={"prompt": "x", "filters": {"pagina": 2}})
    assert response.status_code == 409 and "mal armado" in response.json()["detail"]


# Si ninguna página cumple los filtros, el chat lo dice sin llamar al modelo, y el turno se guarda igual.
def test_chat_con_filtros_sin_paginas(setup):
    client, settings, tmp_path = setup
    settings.openai_api_key = "d"
    base, library = synced_library(client)
    events = ask_filtered(client, base, "¿Qué es CLIP?", {"nombre": {"operator": "eq", "value": "otra.pdf"}})
    assert [e["type"] for e in events] == ["text_delta", "stop"]
    assert events[0]["content"] == "No encontré páginas con esos filtros."
    folder = tmp_path / "documents" / "libraries" / library["id"] / "chats" / "local" / events[-1]["conversation_id"]
    turn = json.loads((folder / "turno_1.json").read_text(encoding="utf-8"))
    assert turn["answer"] == "No encontré páginas con esos filtros." and turn["llm_calls"] == []


# El costo en dólares de un turno se estima con la lista de precios de OpenAI (por millón de tokens): 0,05 entrada y 0,40 salida.
def test_usage_trae_costo_estimado():
    calls = [{"usage": {"prompt_tokens": 1_000_000, "completion_tokens": 100_000}}]
    usage = turn_recorder.total_usage(calls, DocumentsSettings())
    assert usage["costo_estimado_usd"] == 0.09
    assert usage["modelo"] == DocumentsSettings().library_chat_model


# El juez tiene su propio razonamiento: cambiar el del chat no lo cambia (así se compara con el mismo juez).
def test_el_juez_no_depende_del_razonamiento_del_chat():
    from app.pipelines.documents.libraries.local.rag_evals import make_judge_llm

    settings = DocumentsSettings(openai_api_key="d", library_reasoning_effort="minimal", library_judge_reasoning_effort="low")
    assert make_judge_llm(settings).reasoning_effort == "low"
    assert make_judge_llm(settings.model_copy(update={"library_reasoning_effort": "high"})).reasoning_effort == "low"
