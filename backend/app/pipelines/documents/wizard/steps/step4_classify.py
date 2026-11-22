"""Paso 4 · Classify: decide de qué tipo es el documento, según reglas que definimos nosotros.

Trabaja sobre el parse del paso 2. Devuelve el tipo elegido, la confianza y el razonamiento del modelo.
Las reglas se editan en el wizard y se guardan como configuración en LlamaCloud (classify_v2).
"""
from llama_cloud import AsyncLlamaCloud

from app.core.runs.store import RunStore, mark_done, mark_running, read_json, write_json

from app.pipelines.documents.number_format import percent
from app.pipelines.documents.settings import DocumentsSettings

from .llamacloud_jobs import LOW_CONFIDENCE, option, parse_job_id, poll

NAME = "classify"
FOLDER = "4_classify"
TITLE = "Classify"
# El paso que tiene que estar terminado antes de correr este: el parse.
REQUIRES = "parse"
EXPLICACION = (
    "Classify decide de qué tipo es el documento eligiendo entre reglas que escribimos nosotros: "
    "un nombre y una descripción por tipo. Además de la respuesta devuelve la confianza y el razonamiento, "
    "es decir, por qué eligió ese tipo y no otro. Sirve para mandar cada documento al proceso que le corresponde."
)

# Las reglas por defecto son las unidades de la materia Aprendizaje Automático II. Las 4 unidades del temario están
# copiadas textuales de "00 Presentación.pdf", págs. 10 a 13; las otras dos cubren lo que el temario no nombra.
# Classify elige una por documento y queda como "tipo" en la metadata: así se filtra la biblioteca por unidad.
DEFAULTS = {
    "rules": [
        {"type": "redes_neuronales", "description": "Unidad 1, Redes Neuronales: Modelo matemático de una neurona biológica. "
         "Perceptrón simple y multicapa. Algoritmo de entrenamiento. Redes profundas (deep learning)."},
        {"type": "procesamiento_del_lenguaje_natural", "description": "Unidad 2, Procesamiento del Lenguaje Natural: "
         "Técnicas de procesamiento: tokenización, radicalización, lematización, etiquetado de partes del discurso, "
         "reconocimiento de entidades nombradas. Modelos de Embeddings y Representación Vectorial. Transformers y aplicaciones."},
        {"type": "procesamiento_digital_de_imagenes", "description": "Unidad 3, Procesamiento digital de imágenes: "
         "Operaciones puntuales en el dominio espacial, filtrado espacial, manejo del color, transformaciones geométricas."},
        {"type": "aprendizaje_profundo_en_imagenes", "description": "Unidad 4, Aprendizaje profundo aplicado a imágenes: "
         "Redes neuronales tipo perceptrón y profundas. Detección de objetos, segmentación semántica, reconocimiento de "
         "objetos y clasificación de imágenes. Transferencia de aprendizaje. Fotografía computacional: Generación de "
         "imágenes, transferencia de estilo."},
        {"type": "temas_complementarios", "description": "Temas de la materia que no están en el temario de las unidades: "
         "modelos multimodales (visión y lenguaje), sesgo, ética y evaluación robusta de modelos"},
        {"type": "presentacion_de_la_materia", "description": "Presentación del curso: docentes, temario completo, "
         "unidades y condiciones de aprobación"},
    ],
}


# Arma el pedido con las reglas elegidas en el wizard (o las de por defecto).
def build_request(options: dict | None) -> dict:
    return {"rules": option(options, "rules", DEFAULTS["rules"]), "mode": "FAST"}


# Guarda la configuración en LlamaCloud y crea el job de Classify sobre el parse.
async def start(client: AsyncLlamaCloud, store: RunStore, run: dict, settings: DocumentsSettings, options: dict | None = None) -> None:
    folder = store.step_dir(run["id"], FOLDER, reset=True)
    request = build_request(options)
    write_json(folder / "request.json", request)

    configuration = await client.configurations.create(name="parla-classify", parameters={"product_type": "classify_v2", **request})
    write_json(folder / "configuration.json", configuration.model_dump())

    job = await client.classify.create(file_input=parse_job_id(run), configuration_id=configuration.id)
    write_json(folder / "create_response.json", job.model_dump())

    mark_running(run, NAME, job_id=job.id, job_status=str(job.status).upper(), configuration_id=configuration.id)
    store.save(run)


# Consulta el job. Cuando termina, guarda la respuesta con el uso de créditos.
async def check(client: AsyncLlamaCloud, store: RunStore, run: dict) -> None:
    response = await poll(store, run, NAME, lambda job_id: client.classify.get(job_id, expand=["usage"]))
    if response is None:
        return

    folder = store.step_dir(run["id"], FOLDER)
    write_json(folder / "response.json", response)
    write_json(folder / "result.json", response.get("result"))
    write_json(folder / "metrics.json", summarize(response, read_json(folder / "request.json")))

    mark_done(run, NAME, credits=(response.get("usage") or {}).get("credits"))
    store.save(run)


# Calcula las métricas y arma la interpretación, solo con lo que devolvió Classify.
def summarize(response: dict, request: dict) -> dict:
    result = response.get("result") or {}
    usage = response.get("usage") or {}
    confidence = result.get("confidence")
    rules = request.get("rules") or []

    metricas = [
        {"label": "Tipo", "value": result.get("type") or "ninguno"},
        {"label": "Confianza", "value": percent(confidence)},
        {"label": "Reglas", "value": len(rules)},
        {"label": "Créditos", "value": usage.get("credits")},
    ]

    interpretacion = []
    if result.get("type"):
        interpretacion.append(f"Lo clasificó como {result['type']}, con {percent(confidence)} de confianza.")
    else:
        interpretacion.append("No encajó en ninguna de las reglas.")
    if confidence is not None and confidence < LOW_CONFIDENCE:
        interpretacion.append("La confianza es baja: conviene leer el razonamiento y revisar las descripciones de las reglas.")
    if usage.get("credits") == 0:
        interpretacion.append("No costó créditos: Classify sobre un parse ya hecho no cobra aparte.")
    if result.get("reasoning"):
        interpretacion.append(f"Razonamiento del modelo: {result['reasoning']}")
    return {"metricas": metricas, "interpretacion": interpretacion}
