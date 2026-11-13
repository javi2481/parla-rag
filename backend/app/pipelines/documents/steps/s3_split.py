"""Paso 3 · Split: divide el documento en partes según categorías que definimos nosotros.

Trabaja sobre el parse del paso 2 (solo se manda su ID). Las categorías se editan en el wizard
y se guardan como configuración en LlamaCloud (split_v1), igual que el parse.

    start()  guarda la configuración y crea el job
    check()  consulta el job; cuando termina, guarda los segmentos, mide e interpreta
"""
from llama_cloud import AsyncLlamaCloud

from app.core.runs.store import RunStore, mark_done, mark_running, write_json

from ..settings import DocumentsSettings
from .jobs import option, parse_job_id, poll

NAME = "split"
FOLDER = "3_split"
TITLE = "Split"
EXPLICACION = (
    "Split divide el documento en partes y le pone una categoría a cada una, por ejemplo "
    "'estado de resultados' de la página 4 a la 5. Las categorías las definimos nosotros. "
    "Sirve para documentos largos: después Extract puede trabajar solo sobre las páginas de una parte. "
    "Usa el parse del paso anterior, así que no vuelve a leer el documento."
)

# Categorías de ejemplo, pensadas para estados financieros. Se pueden cambiar en el wizard.
DEFAULTS = {
    "categories": [
        {"name": "portada_e_indice", "description": "Portada, índice y datos generales de la empresa"},
        {"name": "estado_de_situacion", "description": "Estado de situación financiera (balance): activos, pasivos y patrimonio"},
        {"name": "estado_de_resultados", "description": "Estado de resultados y otros resultados integrales"},
        {"name": "flujo_de_efectivo", "description": "Estado de flujo de efectivo"},
        {"name": "cambios_en_el_patrimonio", "description": "Estado de cambios en el patrimonio"},
        {"name": "notas", "description": "Notas a los estados financieros"},
        {"name": "informes", "description": "Informe del auditor, de la comisión fiscalizadora o reseña informativa"},
    ],
    # "include": las páginas que no encajan en ninguna categoría aparecen como "uncategorized".
    "allow_uncategorized": "include",
}


# Arma el pedido con las categorías elegidas en el wizard (o las de por defecto).
def build_request(options: dict | None) -> dict:
    return {
        "categories": option(options, "categories", DEFAULTS["categories"]),
        "splitting_strategy": {"allow_uncategorized": option(options, "allow_uncategorized", DEFAULTS["allow_uncategorized"])},
    }


# Guarda la configuración en LlamaCloud y crea el job de Split sobre el parse.
async def start(client: AsyncLlamaCloud, store: RunStore, run: dict, settings: DocumentsSettings, options: dict | None = None) -> None:
    folder = store.step_dir(run["id"], FOLDER, reset=True)
    request = build_request(options)
    write_json(folder / "request.json", request)

    configuration = await client.configurations.create(name="parla-split", parameters={"product_type": "split_v1", **request})
    write_json(folder / "configuration.json", configuration.model_dump())

    job = await client.split.create(file_input=parse_job_id(run), configuration_id=configuration.id)
    write_json(folder / "create_response.json", job.model_dump())

    mark_running(run, NAME, job_id=job.id, job_status=str(job.status).upper(), configuration_id=configuration.id)
    store.save(run)


# Consulta el job. Cuando termina, guarda la respuesta y los segmentos por separado.
async def check(client: AsyncLlamaCloud, store: RunStore, run: dict) -> None:
    response = await poll(store, run, NAME, client.split.get)
    if response is None:
        return

    folder = store.step_dir(run["id"], FOLDER)
    write_json(folder / "response.json", response)
    segments = (response.get("result") or {}).get("segments") or []
    write_json(folder / "segments.json", segments)
    write_json(folder / "metrics.json", summarize(response))

    # Split no informa créditos: su respuesta no tiene campo de uso (ver docs/bitacora.md).
    mark_done(run, NAME, credits=None)
    store.save(run)


# Pasa una lista de páginas a un texto corto: [4, 5, 6, 9] → "4-6, 9".
def pages_text(pages: list[int]) -> str:
    pages = sorted(pages)
    ranges = []
    start = previous = pages[0] if pages else None
    for page in pages[1:]:
        if page != previous + 1:
            ranges.append((start, previous))
            start = page
        previous = page
    if start is not None:
        ranges.append((start, previous))
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in ranges)


# Calcula las métricas y arma la interpretación, solo con lo que devolvió Split.
def summarize(response: dict) -> dict:
    segments = (response.get("result") or {}).get("segments") or []
    names = [category["name"] for category in response.get("categories") or []]
    found = {segment["category"] for segment in segments}
    pages = sum(len(segment["pages"]) for segment in segments)
    uncategorized = [s for s in segments if s["category"] not in names]
    low = [s for s in segments if s.get("confidence_category") == "low"]

    metricas = [
        {"label": "Partes", "value": len(segments)},
        {"label": "Páginas asignadas", "value": pages},
        {"label": "Categorías encontradas", "value": f"{len(found & set(names))} de {len(names)}"},
        {"label": "Sin categoría", "value": len(uncategorized)},
        {"label": "Confianza baja", "value": len(low)},
        {"label": "Créditos", "value": "no informa"},
    ]

    interpretacion = []
    for segment in segments:
        interpretacion.append(
            f"{segment['category']}: páginas {pages_text(segment['pages'])} (confianza {segment.get('confidence_category', '—')})."
        )
    missing = [name for name in names if name not in found]
    if missing:
        interpretacion.append(f"No encontró ninguna parte de: {', '.join(missing)}.")
    if low:
        interpretacion.append("Las partes con confianza baja conviene revisarlas contra las capturas del paso Parse.")
    interpretacion.append("Split no informa créditos: para saber cuánto costó hay que mirar el panel de LlamaCloud.")
    return {"metricas": metricas, "interpretacion": interpretacion}
