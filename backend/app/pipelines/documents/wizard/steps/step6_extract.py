"""Paso 6 · Extract: saca del documento los datos del schema, con la cita y la confianza de cada uno.

Trabaja sobre el parse del paso 2 y usa la configuración guardada en el paso 5.
Si se elige una parte del Split, solo analiza esas páginas (target_pages).

    start()  crea el job
    check()  consulta el job; cuando termina, guarda el resultado, la metadata y las cajas, mide e interpreta
"""
from llama_cloud import AsyncLlamaCloud

from app.core.runs.store import RunStore, mark_done, mark_running, read_json, write_json

from app.pipelines.documents.number_format import percent
from app.pipelines.documents.settings import DocumentsSettings

from .llamacloud_jobs import LOW_CONFIDENCE, option, parse_job_id, poll
from .step5_schema import leaf_fields

NAME = "extract"
FOLDER = "6_extract"
TITLE = "Extract"
# El paso que tiene que estar terminado antes de correr este: el schema (y el parse, que ya está porque el schema lo necesita).
REQUIRES = "schema"
EXPLICACION = (
    "Extract busca en el documento cada dato del schema y lo devuelve como JSON, con números como números. "
    "De cada valor dice de dónde lo sacó (página, texto y caja en la página) y con cuánta confianza. "
    "Las cajas se dibujan sobre las capturas: así se puede comprobar a ojo que cada dato existe en el documento. "
    "Se puede limitar a las páginas de una parte del Split."
)

# Lo que se le pide a LlamaCloud al consultar el job: la configuración usada, la metadata por campo y los créditos.
EXPAND = ["configuration", "extract_metadata", "usage"]

# Las opciones de la configuración guardada que se copian cuando hay que cambiar las páginas.
CONFIG_KEYS = ["data_schema", "tier", "cite_sources", "advanced_citations", "confidence_scores", "extraction_target", "system_prompt"]


# Arma el pedido. Sin páginas elegidas usa la configuración guardada tal cual (configuration_id);
# con páginas, copia esa configuración y le agrega target_pages, porque el ID solo no admite cambios.
def build_request(run: dict, saved: dict, options: dict | None) -> dict:
    target_pages = option(options, "target_pages", None)
    if not target_pages:
        return {"file_input": parse_job_id(run), "configuration_id": run["steps"]["schema"]["configuration_id"]}
    parameters = saved["parameters"]
    configuration = {key: parameters[key] for key in CONFIG_KEYS if parameters.get(key) is not None}
    configuration["target_pages"] = target_pages
    return {"file_input": parse_job_id(run), "configuration": configuration}


# Crea el job de Extract con el schema del paso 5.
async def start(client: AsyncLlamaCloud, store: RunStore, run: dict, settings: DocumentsSettings, options: dict | None = None) -> None:
    folder = store.step_dir(run["id"], FOLDER, reset=True)
    saved = read_json(store.run_dir(run["id"]) / "5_schema" / "configuration.json")
    request = build_request(run, saved, options)
    write_json(folder / "request.json", {**request, "segment": option(options, "segment", None)})

    job = await client.extract.create(**request)
    write_json(folder / "create_response.json", job.model_dump())

    mark_running(run, NAME, job_id=job.id, job_status=str(job.status).upper())
    store.save(run)


# Consulta el job. Cuando termina, guarda todo y arma la lista de campos con sus citas y cajas.
async def check(client: AsyncLlamaCloud, store: RunStore, run: dict) -> None:
    response = await poll(store, run, NAME, lambda job_id: client.extract.get(job_id, expand=EXPAND))
    if response is None:
        return

    folder = store.step_dir(run["id"], FOLDER)
    write_json(folder / "response.json", response)
    write_json(folder / "result.json", response.get("extract_result"))
    write_json(folder / "metadata.json", response.get("extract_metadata"))

    schema = read_json(store.run_dir(run["id"]) / "5_schema" / "schema.json")
    fields = add_missing(collect_fields(response), schema)
    write_json(folder / "fields.json", fields)
    write_json(folder / "boxes.json", collect_boxes(fields))
    request = read_json(folder / "request.json")
    write_json(folder / "metrics.json", summarize(response, fields, request))

    mark_done(run, NAME, credits=own_credits(response))
    store.save(run)


# Los créditos propios de Extract. El total que informa LlamaCloud también incluye el parse que usó.
def own_credits(response: dict) -> float | None:
    usage = response.get("usage") or {}
    return usage.get("extract_credits")


# ¿Es la metadata de un valor final? (la que tiene citas o confianza).
def is_leaf_meta(meta) -> bool:
    return isinstance(meta, dict) and ("citation" in meta or "confidence" in meta)


# Recorre el resultado y su metadata en paralelo y devuelve cada campo final con su valor, confianza y citas.
# Por ejemplo: {"field": "ingresos", "value": 78124, "confidence": 0.95, "citations": [{"page": 3, ...}]}
def walk(value, meta, path: str, out: list) -> None:
    if isinstance(value, dict) and not is_leaf_meta(meta):
        for key, child in value.items():
            walk(child, (meta or {}).get(key) if isinstance(meta, dict) else None, f"{path}.{key}" if path else key, out)
        return
    if isinstance(value, list) and value and isinstance(value[0], dict):
        for index, child in enumerate(value):
            child_meta = meta[index] if isinstance(meta, list) and index < len(meta) else None
            walk(child, child_meta, f"{path}[{index}]", out)
        return

    metas = meta if isinstance(meta, list) else [meta]
    citations, confidences = [], []
    for item in metas:
        if not is_leaf_meta(item):
            continue
        if item.get("confidence") is not None:
            confidences.append(item["confidence"])
        for citation in item.get("citation") or []:
            size = citation.get("page_dimensions") or {}
            citations.append({
                "page": citation.get("page"),
                "text": citation.get("matching_text"),
                "boxes": citation.get("bounding_boxes") or [],
                "page_width": size.get("width"),
                "page_height": size.get("height"),
            })
    out.append({
        "field": path,
        "value": value,
        "confidence": min(confidences) if confidences else None,
        "citations": citations,
    })


# Arma la lista de campos a partir de la respuesta de Extract.
def collect_fields(response: dict) -> list[dict]:
    metadata = ((response.get("extract_metadata") or {}).get("field_metadata") or {}).get("document_metadata")
    fields: list[dict] = []
    walk(response.get("extract_result") or {}, metadata, "", fields)
    return fields


# Extract no devuelve los campos que no encontró. Se agregan como vacíos, comparando contra el schema,
# para que se vea qué datos del schema no aparecieron en el documento.
def add_missing(fields: list[dict], schema: dict) -> list[dict]:
    present = {field["field"] for field in fields}
    for path, _ in leaf_fields(schema):
        if "[]" not in path and path not in present:
            fields.append({"field": path, "value": None, "confidence": None, "citations": [], "missing": True})
    return fields


# Una caja por renglón, lista para dibujar sobre la captura de su página.
def collect_boxes(fields: list[dict]) -> list[dict]:
    boxes = []
    for field in fields:
        for citation in field["citations"]:
            for box in citation["boxes"]:
                boxes.append({
                    "field": field["field"], "value": field["value"], "confidence": field["confidence"],
                    "page": citation["page"], "text": citation["text"],
                    "page_width": citation["page_width"], "page_height": citation["page_height"], **box,
                })
    return boxes


# ¿El campo quedó sin valor?
def is_empty(value) -> bool:
    return value is None or value == "" or value == []


# Calcula las métricas y arma la interpretación, solo con lo que devolvió Extract.
def summarize(response: dict, fields: list[dict], request: dict) -> dict:
    filled = [f for f in fields if not is_empty(f["value"])]
    empty = [f for f in fields if is_empty(f["value"])]
    confidences = [f["confidence"] for f in filled if f["confidence"] is not None]
    low = [f for f in filled if f["confidence"] is not None and f["confidence"] < LOW_CONFIDENCE]
    uncited = [f for f in filled if not f["citations"]]
    pages = sorted({c["page"] for f in fields for c in f["citations"] if c["page"] is not None})
    usage = response.get("usage") or {}
    target_pages = (request.get("configuration") or {}).get("target_pages")

    metricas = [
        {"label": "Campos", "value": len(fields)},
        {"label": "Con valor", "value": len(filled)},
        {"label": "Vacíos", "value": len(empty)},
        {"label": "Confianza promedio", "value": percent(sum(confidences) / len(confidences)) if confidences else "—"},
        {"label": "Confianza más baja", "value": percent(min(confidences)) if confidences else "—"},
        {"label": "Para revisar", "value": len(low)},
        {"label": "Sin cita", "value": len(uncited)},
        {"label": "Páginas citadas", "value": ", ".join(map(str, pages)) or "—"},
        {"label": "Páginas analizadas", "value": target_pages or "todas"},
        {"label": "Créditos", "value": usage.get("extract_credits")},
    ]

    interpretacion = [f"Encontró valor para {len(filled)} de {len(fields)} campos del schema."]
    if target_pages:
        segment = request.get("segment")
        where = f" (la parte «{segment}» del Split)" if segment else ""
        several = "," in target_pages or "-" in target_pages
        interpretacion.append(f"Solo analizó {'las páginas' if several else 'la página'} {target_pages}{where}.")
    missing = [f for f in empty if f.get("missing")]
    nulls = [f for f in empty if not f.get("missing")]
    if missing:
        interpretacion.append("No los devolvió (no los encontró en las páginas analizadas): " + ", ".join(f["field"] for f in missing) + ".")
    if nulls:
        interpretacion.append("Los devolvió vacíos: " + ", ".join(f["field"] for f in nulls) + ".")
    for field in low:
        cited = field["citations"][0]["text"] if field["citations"] else None
        detail = f": la cita dice «{cited}»" if cited else ""
        interpretacion.append(f"Revisá «{field['field']}» (confianza {percent(field['confidence'])}){detail}.")
    if uncited:
        interpretacion.append(
            "Tienen valor pero no cita, así que no se pueden ubicar en el documento: "
            + ", ".join(f["field"] for f in uncited) + "."
        )
    if usage.get("extract_credits") is not None:
        text = f"Costó {usage['extract_credits']} créditos propios"
        if usage.get("credits") is not None:
            text += f"; el total que informa LlamaCloud ({usage['credits']}) incluye el parse que usó"
        interpretacion.append(text + ".")
    return {"metricas": metricas, "interpretacion": interpretacion}
