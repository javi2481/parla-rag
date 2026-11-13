"""Paso 2 · Parse: LlamaParse lee el documento y lo convierte en texto estructurado.

Se pide TODO lo que ofrece Parse (ver docs/verificacion-1-parse.md):
Markdown, texto, items con cajas, confianza por página, tablas en Excel, gráficos convertidos
en tablas, capturas de cada página y recortes de cada tabla o gráfico.

    start()  crea el job en LlamaCloud y guarda lo que se pidió
    check()  consulta el job; cuando termina, guarda todo, mide e interpreta
"""
import httpx
from llama_cloud import AsyncLlamaCloud

from app.core.runs.store import RunStore, mark_done, mark_failed, mark_running, write_json

from ..settings import DocumentsSettings

NAME = "parse"
FOLDER = "2_parse"
TITLE = "Parse"
EXPLICACION = (
    "LlamaParse lee el documento y lo convierte en texto estructurado: Markdown con títulos, listas y tablas, "
    "más la ubicación de cada elemento en la página. Con IA (tier agentic) también entiende fotos, "
    "tablas complejas y gráficos, que convierte en tablas de datos. "
    "Es el paso más importante: Split, Classify y Extract trabajan sobre este resultado, sin volver a leer el documento."
)

# Lo que se le pide a Parse además de lo que hace por defecto.
OUTPUT_OPTIONS = {
    "extract_printed_page_number": True,
    "images_to_save": ["layout", "screenshot"],       # recortes de tablas y gráficos, y captura de cada página
    "granular_bboxes": ["cell", "line", "word"],      # cajas por celda, línea y palabra
    "markdown": {
        "annotate_links": True,
        "tables": {"merge_continued_tables": True, "output_tables_as_markdown": True},
    },
    "tables_as_spreadsheet": {"enable": True, "guess_sheet_name": True},  # todas las tablas en un Excel
}
PROCESSING_OPTIONS = {
    "aggressive_table_extraction": True,
    "specialized_chart_parsing": "agentic",  # gráficos → tablas de datos
    "confidence_score_effort": "high",
    "forms": "enrich",
    "ocr_parameters": {"languages": ["es"]},
}

# Todas las salidas que devuelve Parse.
EXPAND = [
    "text", "markdown", "items", "metadata", "forms", "job_metadata", "usage",
    "images_content_metadata", "xlsx_content_metadata",
]

# Estados del job que todavía no terminaron.
WAITING_STATES = {"PENDING", "RUNNING"}

# Debajo de esta confianza, una página se marca para revisar.
LOW_CONFIDENCE = 0.8


# Arma el pedido completo para Parse con la configuración del .env.
def build_request(settings: DocumentsSettings) -> dict:
    return {
        "tier": settings.parse_tier,
        "version": settings.parse_version,
        "page_ranges": {"max_pages": settings.parse_max_pages},
        "input_options": {"image": {"camera_photo_correction": True}},  # endereza fotos sacadas con el celular
        "output_options": OUTPUT_OPTIONS,
        "processing_options": PROCESSING_OPTIONS,
    }


# Crea el job de Parse para el archivo subido en el paso 1.
async def start(client: AsyncLlamaCloud, store: RunStore, run: dict, settings: DocumentsSettings) -> None:
    folder = store.step_dir(run["id"], FOLDER, reset=True)
    request = build_request(settings)
    write_json(folder / "request.json", request)

    file_id = run["steps"]["upload"]["file_id"]
    job = await client.parsing.create(file_id=file_id, **request)
    write_json(folder / "create_response.json", job.model_dump())

    mark_running(run, NAME, job_id=job.id, job_status=job.status)
    store.save(run)


# Consulta el job. Si terminó bien, guarda todo y calcula las métricas; si falló, guarda el error.
async def check(client: AsyncLlamaCloud, store: RunStore, run: dict) -> None:
    step = run["steps"][NAME]
    if step["state"] != "running":
        return

    status = (await client.parsing.get(step["job_id"])).job.status
    step["job_status"] = status
    if status in WAITING_STATES:
        store.save(run)
        return
    if status != "COMPLETED":
        mark_failed(run, NAME, f"LlamaParse terminó con estado {status}.")
        store.save(run)
        return

    result = await client.parsing.get(step["job_id"], expand=EXPAND)
    response = result.model_dump()
    folder = store.step_dir(run["id"], FOLDER)
    await save_outputs(folder, response)
    write_json(folder / "metrics.json", summarize(response))

    credits = (response["job"].get("usage") or {}).get("credits")
    mark_done(run, NAME, credits=credits)
    store.save(run)


# Guarda la respuesta completa y, aparte, cada salida en su propio archivo para leerla fácil.
async def save_outputs(folder, response: dict) -> None:
    write_json(folder / "response.json", response)

    markdown_pages = (response.get("markdown") or {}).get("pages") or []
    markdown = []
    for page in markdown_pages:
        markdown.append(f"<!-- página {page['page_number']} -->\n{page.get('markdown') or ''}")
    (folder / "document.md").write_text("\n\n".join(markdown))

    text_pages = (response.get("text") or {}).get("pages") or []
    text = []
    for page in text_pages:
        text.append(page.get("text") or "")
    (folder / "text.txt").write_text("\n\n".join(text))

    for key in ("items", "metadata", "forms", "job_metadata"):
        if response.get(key) is not None:
            write_json(folder / f"{key}.json", response[key])

    await download_files(folder, response)


# Descarga lo que LlamaCloud devuelve como link temporal: imágenes, el Excel con las tablas
# y los items con las cajas por línea y palabra.
async def download_files(folder, response: dict) -> None:
    images = (response.get("images_content_metadata") or {}).get("images") or []
    extra_files = response.get("result_content_metadata") or {}

    async with httpx.AsyncClient(timeout=120) as http:
        for image in images:
            if image.get("presigned_url"):
                res = await http.get(image["presigned_url"])
                (folder / "images").mkdir(exist_ok=True)
                (folder / "images" / image["filename"]).write_bytes(res.content)

        for key, filename in (("xlsx", "tables.xlsx"), ("grounded_items", "grounded_items.jsonl")):
            url = (extra_files.get(key) or {}).get("presigned_url")
            if url:
                res = await http.get(url)
                (folder / filename).write_bytes(res.content)


# ── Métricas e interpretación ────────────────────────────────────────────


# Cuenta los items de cada tipo (table, heading, text…) en todas las páginas.
def count_items(response: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for page in (response.get("items") or {}).get("pages") or []:
        for item in page.get("items") or []:
            kind = item.get("type") or "otro"
            counts[kind] = counts.get(kind, 0) + 1
    return counts


# Cuenta las palabras del texto plano.
def count_words(response: dict) -> int:
    total = 0
    for page in (response.get("text") or {}).get("pages") or []:
        total += len((page.get("text") or "").split())
    return total


# Cuenta los gráficos: son los recortes de layout que LlamaParse nombra "..._chart_...".
def count_charts(response: dict) -> int:
    images = (response.get("images_content_metadata") or {}).get("images") or []
    return len([image for image in images if image.get("category") == "layout" and "_chart_" in image.get("filename", "")])


# Escribe un número con formato argentino: 133812 → "133.812" y 21.1 → "21,1".
def number_es(value: float, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


# Pasa un número de 0 a 1 a porcentaje: 0.93 → "93%".
def percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{round(value * 100)}%"


# Arma el texto de tokens del modelo: "133.812 / 46.288" (o "—" si LlamaParse no lo informa).
def tokens_text(job_metadata: dict) -> str:
    tokens_in = job_metadata.get("pdf-inputTokens")
    tokens_out = job_metadata.get("pdf-outputTokens")
    if tokens_in is None or tokens_out is None:
        return "—"
    return f"{number_es(tokens_in)} / {number_es(tokens_out)}"


# Calcula las métricas y arma las frases de interpretación, solo con lo que devolvió LlamaParse.
def summarize(response: dict) -> dict:
    metadata = response.get("metadata") or {}
    pages = metadata.get("pages") or []
    document = metadata.get("document") or {}
    job_metadata = response.get("job_metadata") or {}
    latency = job_metadata.get("latency") or {}

    page_count = len(pages)
    words = count_words(response)
    items = count_items(response)
    tables = items.get("table", 0)
    charts = count_charts(response)
    credits = (response["job"].get("usage") or {}).get("credits")
    seconds = (latency.get("total_ms") or 0) / 1000

    scored_pages = [page for page in pages if page.get("confidence") is not None]
    worst = min(scored_pages, key=lambda page: page["confidence"]) if scored_pages else None
    low_pages = [page["page_number"] for page in scored_pages if page["confidence"] < LOW_CONFIDENCE]
    rotated = [page["page_number"] for page in pages if page.get("original_orientation_angle")]
    watermarked = [page["page_number"] for page in pages if page.get("watermark")]

    metrics = [
        {"label": "Páginas", "value": page_count},
        {"label": "Palabras", "value": number_es(words)},
        {"label": "Tablas", "value": tables},
        {"label": "Gráficos", "value": charts},
        {"label": "Títulos", "value": items.get("heading", 0)},
        {"label": "Confianza del documento", "value": percent(document.get("confidence"))},
        {"label": "Créditos", "value": credits},
        {"label": "Tiempo de procesamiento", "value": f"{number_es(seconds, 1)} s"},
        {"label": "Tokens del modelo (entrada / salida)", "value": tokens_text(job_metadata)},
    ]

    sentences = []
    if page_count and credits:
        sentences.append(
            f"LlamaParse leyó {page_count} páginas en {number_es(seconds, 1)} segundos "
            f"y cobró {credits:.0f} créditos ({credits / page_count:.0f} por página)."
        )
    elif page_count:
        sentences.append(f"LlamaParse leyó {page_count} páginas en {number_es(seconds, 1)} segundos.")
    if document.get("confidence") is not None:
        sentences.append(f"La confianza general del documento es {percent(document['confidence'])}.")
    if len(low_pages) == 1:
        sentences.append(
            f"Conviene revisar la página {worst['page_number']}: tiene {percent(worst['confidence'])} de confianza. "
            "Suele pasar en páginas con gráficos o imágenes que tienen datos difíciles de leer."
        )
    elif low_pages:
        sentences.append(
            f"Conviene revisar las páginas {', '.join(map(str, low_pages))}: "
            f"la más baja es la {worst['page_number']} con {percent(worst['confidence'])} de confianza. "
            "Suele pasar en páginas con gráficos o imágenes que tienen datos difíciles de leer."
        )
    elif worst:
        sentences.append("Todas las páginas se leyeron con confianza alta.")
    if charts:
        sentences.append(
            f"Encontró {tables} tablas, incluidos {charts} gráficos que convirtió en tablas de datos. "
            "Están todas en tables.xlsx, una por hoja."
        )
    elif tables:
        sentences.append(f"Encontró {tables} tablas. Están todas en tables.xlsx, una por hoja.")
    if rotated:
        sentences.append(f"Enderezó páginas que venían giradas: {', '.join(map(str, rotated))}.")
    if watermarked:
        sentences.append(f"Detectó marca de agua en las páginas {', '.join(map(str, watermarked))}.")

    return {"metricas": metrics, "interpretacion": sentences}
