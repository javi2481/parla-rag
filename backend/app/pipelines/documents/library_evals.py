"""Evals de una biblioteca local: miden la búsqueda y las respuestas del chat contra un set de preguntas verificadas a mano.

Todo es nativo de LlamaIndex (llama_index.core.evaluation):
  - Búsqueda: RetrieverEvaluator, con el mismo buscador y el mismo reranker que el chat. Métricas hit_rate y mrr.
    No usa un modelo de lenguaje: solo los tokens de Voyage (gratis hasta 200 millones).
  - Respuestas (opcional): el chat responde cada pregunta sin historial y DeepSeek hace de juez con
    FaithfulnessEvaluator (¿la respuesta sale de los fragmentos?) y CorrectnessEvaluator (¿coincide con la respuesta
    esperada?, de 1 a 5). Cuesta centavos de DeepSeek.

El set de preguntas vive junto a sus documentos: data/samples/<conjunto>/evals/preguntas.json (va a git).
Cada corrida se guarda en la carpeta de la biblioteca: libraries/<id>/evals/<fecha>/ (request, resultados y métricas).
"""
from llama_index.core.evaluation import CorrectnessEvaluator, FaithfulnessEvaluator, RetrieverEvaluator
from llama_index.core.instrumentation import get_dispatcher
from llama_index.llms.deepseek import DeepSeek

from app.core.runs.store import RunStore, now, read_json, write_json

from . import local_library as engine
from .library import stamp
from .settings import DocumentsSettings


# El juez de las respuestas: DeepSeek sin streaming (el del chat pide los tokens en streaming, que acá no sirve).
# Está en una función para que los tests lo reemplacen por uno falso.
def make_judge_llm(settings: DocumentsSettings):
    return DeepSeek(model=settings.library_chat_model, api_key=settings.deepseek_api_key)


# Lee el set de preguntas de data/samples/<conjunto>/evals/preguntas.json.
def load_questions(data_dir, name: str) -> dict:
    path = data_dir / "samples" / name / "evals" / "preguntas.json"
    if not path.is_file():
        raise LookupError(f"No existe el set de preguntas {path}.")
    return read_json(path)


# Los IDs de los chunks que son "correctos" para una pregunta: todos los de las páginas fuente.
# Se arman en cada biblioteca, porque cada separador corta distinto y los IDs cambian.
def expected_ids(index, question: dict, names: dict) -> list[str]:
    sources = {(names[source["doc"]], source["pagina"]) for source in question["fuentes"]}
    return [node_id for node_id, node in index.docstore.docs.items()
            if (node.metadata.get("nombre"), node.metadata.get("pagina")) in sources]


# Las páginas (documento y número) de una lista de chunks, en orden y sin repetir.
def pages_of(index, node_ids: list[str]) -> list[str]:
    pages = []
    for node_id in node_ids:
        metadata = index.docstore.docs[node_id].metadata
        page = f"{metadata.get('nombre')}, pág. {metadata.get('pagina')}"
        if page not in pages:
            pages.append(page)
    return pages


# Mide la búsqueda de una pregunta: ¿llegó al modelo algún chunk de las páginas fuente? ¿en qué puesto?
async def eval_retrieval(index, settings: DocumentsSettings, question: dict, names: dict, candidates: int) -> dict:
    top_k = settings.library_chat_top_k
    evaluator = RetrieverEvaluator.from_metric_names(
        ["hit_rate", "mrr"],
        retriever=index.as_retriever(similarity_top_k=candidates),
        node_postprocessors=[engine.make_reranker(settings, top_k)],
    )
    result = await evaluator.aevaluate(query=question["pregunta"], expected_ids=expected_ids(index, question, names))
    return {
        "hit_rate": result.metric_vals_dict["hit_rate"],
        "mrr": result.metric_vals_dict["mrr"],
        "paginas_esperadas": [f"{names[s['doc']]}, pág. {s['pagina']}" for s in question["fuentes"]],
        "paginas_encontradas": pages_of(index, result.retrieved_ids),
    }


# El chat responde la pregunta sin historial y DeepSeek la juzga: fidelidad a los fragmentos y corrección.
async def eval_answer(index, settings: DocumentsSettings, question: dict, candidates: int) -> dict:
    recorder = engine.TurnRecorder()
    dispatcher = get_dispatcher()
    dispatcher.add_event_handler(recorder)
    try:
        chat = engine.make_chat_engine(index, settings, history=[], candidates=candidates)
        response = await chat.astream_chat(question["pregunta"])
        answer = "".join([token async for token in response.async_response_gen()])
        contexts = [node.node.get_content() for node in response.source_nodes]
        judge = make_judge_llm(settings)
        faithfulness = await FaithfulnessEvaluator(llm=judge).aevaluate(
            query=question["pregunta"], response=answer, contexts=contexts)
        correctness = await CorrectnessEvaluator(llm=judge).aevaluate(
            query=question["pregunta"], response=answer, reference=question["respuesta_esperada"])
    finally:
        dispatcher.event_handlers.remove(recorder)
    return {
        "respuesta": answer,
        "fiel_a_los_fragmentos": faithfulness.passing,
        "fidelidad_explicacion": faithfulness.feedback,
        "correccion": correctness.score,
        "correcta": correctness.passing,
        "correccion_explicacion": correctness.feedback,
        "llamadas_al_modelo": recorder.llm_calls,
        "usage": engine.total_usage(recorder.llm_calls, settings.library_chat_model),
    }


# Promedio de una lista de números, o None si no hay ninguno.
def average(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 3) if values else None


# Las métricas y la interpretación de una corrida de evals, armadas solo con los resultados.
def summarize(library: dict, results: list[dict], candidates: int, with_answers: bool) -> dict:
    searched = [r["busqueda"] for r in results if r.get("busqueda")]
    hits = sum(1 for r in searched if r["hit_rate"] == 1)
    metricas = [
        {"label": "Preguntas", "value": len(results)},
        {"label": "Separador", "value": library.get("splitter", "oraciones")},
        {"label": "Candidatos antes del reranker", "value": candidates},
        {"label": "Búsqueda: hit rate", "value": average([r["hit_rate"] for r in searched])},
        {"label": "Búsqueda: MRR", "value": average([r["mrr"] for r in searched])},
    ]
    interpretacion = [
        f"La búsqueda trajo al menos una página correcta en {hits} de {len(searched)} preguntas con fuente "
        f"(las trampas no tienen página correcta y no se miden en la búsqueda).",
        "MRR es el promedio de 1/puesto del primer chunk correcto entre los que llegan al modelo: 1 es primero, 0,5 es segundo, 0 es que no llegó.",
    ]
    misses = [r["id"] for r in results if r.get("busqueda") and r["busqueda"]["hit_rate"] == 0]
    if misses:
        interpretacion.append(f"No llegó ninguna página correcta al modelo en: {', '.join(misses)}.")
    if with_answers:
        answers = [r["respuesta"] for r in results]
        faithful = sum(1 for a in answers if a["fiel_a_los_fragmentos"])
        correct = sum(1 for a in answers if a["correcta"])
        metricas += [
            {"label": "Respuestas fieles a los fragmentos", "value": f"{faithful} de {len(answers)}"},
            {"label": "Respuestas correctas (4 o más de 5)", "value": f"{correct} de {len(answers)}"},
            {"label": "Corrección promedio (1 a 5)", "value": average([a["correccion"] for a in answers])},
            {"label": "Tokens de DeepSeek (entrada / salida)",
             "value": f"{sum(a['usage']['tokens_de_entrada'] for a in answers)} / {sum(a['usage']['tokens_de_salida'] for a in answers)}"},
        ]
        wrong = [r["id"] for r in results if not r["respuesta"]["correcta"]]
        if wrong:
            interpretacion.append(f"El juez marcó como incorrectas: {', '.join(wrong)}. Su explicación está en cada resultado.")
        interpretacion.append("El juez es DeepSeek: también puede equivocarse. Conviene leer sus explicaciones.")
    metricas.append({"label": "Créditos de LlamaCloud", "value": 0})
    return {"metricas": metricas, "interpretacion": interpretacion}


# Corre los evals de una biblioteca: la búsqueda de cada pregunta y, si se pide, también la respuesta juzgada.
# Guarda todo en libraries/<id>/evals/<fecha>/.
async def run_evals(store: RunStore, settings: DocumentsSettings, library: dict, name: str = "byma",
                    candidates: int | None = None, with_answers: bool = False) -> dict:
    engine.check_ready(settings)
    if with_answers and not settings.deepseek_api_key:
        raise ValueError("Falta configurar DEEPSEEK_API_KEY en backend/.env.")
    data_dir = engine.data_dir_of(store)
    engine.prepare_nltk(data_dir)
    questions = load_questions(data_dir, name)
    candidates = candidates or settings.library_chat_top_k * engine.CANDIDATES_PER_RESULT
    index = engine.load_index(store, settings, library)

    results = []
    for question in questions["preguntas"]:
        result = {"id": question["id"], "tipo": question["tipo"], "pregunta": question["pregunta"],
                  "respuesta_esperada": question["respuesta_esperada"]}
        if question["fuentes"]:
            result["busqueda"] = await eval_retrieval(index, settings, question, questions["documentos"], candidates)
        if with_answers:
            result["respuesta"] = await eval_answer(index, settings, question, candidates)
        results.append(result)

    request = {"conjunto": name, "preguntas": len(results), "candidatos": candidates, "respuestas": with_answers,
               "splitter": library.get("splitter", "oraciones"), "top_k": settings.library_chat_top_k,
               "embed_model": settings.library_embed_model, "rerank_model": settings.library_rerank_model,
               "juez": settings.library_chat_model if with_answers else None}
    summary = summarize(library, results, candidates, with_answers)
    folder = store.step_dir(library["id"], f"evals/{stamp()}")
    write_json(folder / "request.json", request)
    write_json(folder / "resultados.json", results)
    write_json(folder / "metrics.json", summary)
    return {"at": now(), "carpeta": folder.name, "request": request, "resultados": results, **summary}
