"""Paso 2 · Parse: LlamaParse lee el documento y lo convierte en texto estructurado.

Se pide TODO lo que ofrece Parse (ver docs/verificacion-1-parse.md):
Markdown, texto, items con cajas, confianza por página, tablas en Excel, gráficos convertidos
en tablas, capturas de cada página y recortes de cada tabla o gráfico.

    start()  crea el job en LlamaCloud y guarda lo que se pidió
    check()  consulta el job; cuando termina, guarda todo, mide e interpreta
"""
import asyncio
from pathlib import Path

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
    # Tres archivos extra: el texto sin formato por página (para búsqueda), el texto completo
    # en un solo archivo (para embeddings) y la caja de cada palabra (para marcar respuestas).
    "additional_outputs": ["stripped_md", "concatenated_stripped_txt", "word_bbox"],
}
PROCESSING_OPTIONS = {
    "aggressive_table_extraction": True,
    "specialized_chart_parsing": "agentic",  # gráficos → tablas de datos
    "confidence_score_effort": "high",       # confianza más precisa por página (+5 créditos por página)
    "forms": "enrich",
    "ocr_parameters": {"languages": ["es"]},
}

# Todas las salidas que devuelve Parse. Las "_content_metadata" llegan como links de descarga:
# así no se pierde nada aunque el documento sea muy largo.
EXPAND = [
    "text", "markdown", "items", "metadata", "forms", "job_metadata", "usage",
    "images_content_metadata", "xlsx_content_metadata",
    "text_content_metadata", "markdown_content_metadata", "items_content_metadata",
    "metadata_content_metadata", "forms_content_metadata", "raw_words_content_metadata",
    "stripped_markdown_content_metadata", "concatenated_stripped_markdown_content_metadata",
]

# Nombre con el que se guarda cada archivo descargable conocido. Los demás van a archivos/.
KNOWN_FILES = {"xlsx": "tables.xlsx", "grounded_items": "grounded_items.jsonl"}

# Estados del job que todavía no terminaron.
WAITING_STATES = {"PENDING", "RUNNING"}

# Debajo de esta confianza, una página se marca para revisar.
LOW_CONFIDENCE = 0.8


# Arma el pedido completo para Parse con la configuración del .env.
def build_request(settings: DocumentsSettings) -> dict:
    return {
        "tier": settings.parse_tier,
        "version": settings.parse_version,
        "input_options": {"image": {"camera_photo_correction": True}},  # endereza fotos sacadas con el celular
        "output_options": OUTPUT_OPTIONS,
        "processing_options": PROCESSING_OPTIONS,
    }


# Guarda el pedido como configuración con nombre en LlamaCloud (si ya existe, la actualiza).
# Así el índice de la biblioteca y los lotes pueden usar exactamente el mismo parse.
async def save_configuration(client: AsyncLlamaCloud, request: dict) -> dict:
    name = f"parla-parse-{request['tier']}-{request['version']}"
    configuration = await client.configurations.create(name=name, parameters={"product_type": "parse_v2", **request})
    return configuration.model_dump()


# Crea el job de Parse para el archivo subido en el paso 1.
# (Parse no tiene opciones en el wizard: siempre pide todo. `options` se recibe para que todos los pasos sean iguales.)
async def start(client: AsyncLlamaCloud, store: RunStore, run: dict, settings: DocumentsSettings, options: dict | None = None) -> None:
    folder = store.step_dir(run["id"], FOLDER, reset=True)
    request = build_request(settings)
    write_json(folder / "request.json", request)

    configuration = await save_configuration(client, request)
    write_json(folder / "configuration.json", configuration)

    file_id = run["steps"]["upload"]["file_id"]
    job = await client.parsing.create(file_id=file_id, **request)
    write_json(folder / "create_response.json", job.model_dump())

    mark_running(run, NAME, job_id=job.id, job_status=job.status, configuration_id=configuration["id"])
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
async def save_outputs(folder: Path, response: dict) -> None:
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


# Descarga lo que LlamaCloud devuelve como link temporal: imágenes, el Excel con las tablas,
# los items con las cajas y todos los demás archivos (texto sin formato, cajas por palabra…).
# Se bajan todos a la vez (en paralelo): un documento largo puede traer cientos de imágenes.
async def download_files(folder: Path, response: dict) -> None:
    images = (response.get("images_content_metadata") or {}).get("images") or []
    extra_files = response.get("result_content_metadata") or {}

    # Arma la lista de (link, archivo de destino).
    downloads = []
    (folder / "images").mkdir(exist_ok=True)
    for image in images:
        if image.get("presigned_url"):
            # Path(...).name se queda solo con el nombre, por si viniera algo como "../x".
            downloads.append((image["presigned_url"], folder / "images" / Path(image["filename"]).name))
    # Todos los archivos descargables que haya devuelto LlamaCloud, conocidos o no.
    (folder / "archivos").mkdir(exist_ok=True)
    for key, info in extra_files.items():
        url = (info or {}).get("presigned_url")
        if not url:
            continue
        if key in KNOWN_FILES:
            destination = folder / KNOWN_FILES[key]
        else:
            # El nombre sale del link, por ejemplo ".../output.raw_words.jsonl?firma" → "raw_words-output.raw_words.jsonl".
            link_name = Path(url.split("?")[0]).name
            destination = folder / "archivos" / f"{key}-{link_name}"
        downloads.append((url, destination))

    async with httpx.AsyncClient(timeout=120) as http:
        # Baja un archivo y lo guarda.
        async def download(url: str, destination: Path) -> None:
            res = await http.get(url)
            res.raise_for_status()
            destination.write_bytes(res.content)

        await asyncio.gather(*[download(url, destination) for url, destination in downloads])


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


# Las dudas que informa LlamaParse en cada tabla (parse_concerns), en castellano.
# "multi_table_page" es solo un aviso; las demás son cosas para revisar.
CONCERN_LABELS = {
    "multi_table_page": "página con varias tablas",
    "header_value_type_mismatch": "columna con un valor de otro tipo (por ejemplo, texto donde van números)",
    "header_row_in_body": "fila de encabezado en medio de la tabla",
    "inconsistent_row_cell_count": "filas con distinta cantidad de celdas",
    "possible_merged_columns": "posibles columnas pegadas en una sola",
    "multi_color_table_text": "tabla con texto en varios colores (el color puede tener significado)",
    "layout_lvm_disagreement": "el detector de diseño y el modelo de IA no coinciden sobre qué hay en la página (por ejemplo, un gráfico sin tabla)",
}
# El detalle de cada duda está en items.json, en el campo parse_concerns de cada tabla.
INFORMATIVE_CONCERNS = {"multi_table_page"}


# Junta las dudas de LlamaParse por tipo, con las páginas donde aparece cada una.
def collect_concerns(response: dict) -> dict[str, list[int]]:
    concerns: dict[str, list[int]] = {}
    for page in (response.get("items") or {}).get("pages") or []:
        for item in page.get("items") or []:
            for concern in item.get("parse_concerns") or []:
                kind = concern.get("type") or "otro"
                pages = concerns.setdefault(kind, [])
                if page["page_number"] not in pages:
                    pages.append(page["page_number"])
    return concerns


# Devuelve las tablas que LlamaParse unió porque seguían en la página siguiente: [[62, 63, 64], ...].
def merged_tables(response: dict) -> list[list[int]]:
    merged = []
    for page in (response.get("items") or {}).get("pages") or []:
        for item in page.get("items") or []:
            if item.get("merged_from_pages"):
                merged.append(item["merged_from_pages"])
    return merged


# Une una lista de páginas en texto: [3, 4, 9] → "3, 4 y 9".
def join_pages(pages: list[int]) -> str:
    texts = [str(page) for page in pages]
    if len(texts) == 1:
        return texts[0]
    return ", ".join(texts[:-1]) + " y " + texts[-1]


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
    concerns = collect_concerns(response)
    merged = merged_tables(response)
    review_concerns = {kind: found for kind, found in concerns.items() if kind not in INFORMATIVE_CONCERNS}

    metrics = [
        {"label": "Páginas", "value": page_count},
        {"label": "Palabras", "value": number_es(words)},
        {"label": "Tablas", "value": tables},
        {"label": "Gráficos", "value": charts},
        {"label": "Títulos", "value": items.get("heading", 0)},
        {"label": "Tablas unidas entre páginas", "value": len(merged)},
        {"label": "Dudas de LlamaParse para revisar", "value": sum(len(found) for found in review_concerns.values())},
        {"label": "Confianza del documento", "value": percent(document.get("confidence"))},
        {"label": "Créditos", "value": credits},
        {"label": "Tiempo de procesamiento", "value": f"{number_es(seconds, 1)} s"},
        {"label": "Tokens del modelo (entrada / salida)", "value": tokens_text(job_metadata)},
    ]

    sentences = []
    if page_count and credits:
        sentences.append(
            f"LlamaParse leyó {page_count} {'página' if page_count == 1 else 'páginas'} en {number_es(seconds, 1)} segundos "
            f"y cobró {credits:.0f} créditos ({credits / page_count:.0f} por página)."
        )
    elif page_count:
        sentences.append(f"LlamaParse leyó {page_count} {'página' if page_count == 1 else 'páginas'} en {number_es(seconds, 1)} segundos.")
    if document.get("confidence") is not None:
        sentences.append(f"La confianza general del documento es {percent(document['confidence'])}.")
    # LlamaParse no dice por qué una página tiene confianza baja: no se inventa un motivo.
    if len(low_pages) == 1:
        sentences.append(
            f"Conviene revisar la página {worst['page_number']}: tiene {percent(worst['confidence'])} de confianza. "
            "LlamaParse no informa el motivo; compará su captura con el Markdown."
        )
    elif low_pages:
        sentences.append(
            f"Conviene revisar las páginas {join_pages(low_pages)}: "
            f"la más baja es la {worst['page_number']} con {percent(worst['confidence'])} de confianza. "
            "LlamaParse no informa el motivo; compará cada captura con el Markdown."
        )
    elif worst:
        sentences.append("La página se leyó con confianza alta." if page_count == 1 else "Todas las páginas se leyeron con confianza alta.")
    if charts == 1:
        sentences.append(
            f"Encontró {tables} tablas, incluido 1 gráfico que convirtió en tabla de datos. "
            "Están todas en tables.xlsx, una por hoja."
        )
    elif charts:
        sentences.append(
            f"Encontró {tables} tablas, incluidos {charts} gráficos que convirtió en tablas de datos. "
            "Están todas en tables.xlsx, una por hoja."
        )
    elif tables:
        sentences.append(f"Encontró {tables} tablas. Están todas en tables.xlsx, una por hoja.")
    groups = [f"{group[0]}–{group[-1]}" for group in merged]
    if len(merged) == 1:
        sentences.append(
            f"Unió 1 tabla que seguía en la página siguiente (páginas {groups[0]}): "
            "queda como una sola tabla en la primera página."
        )
    elif merged:
        sentences.append(
            f"Unió {len(merged)} tablas que seguían en la página siguiente (páginas {', '.join(groups)}): "
            "cada una queda como una sola tabla en su primera página."
        )
    for kind, found in review_concerns.items():
        label = CONCERN_LABELS.get(kind, kind)
        where = "la página" if len(found) == 1 else "las páginas"
        sentences.append(f"LlamaParse avisa una duda en {where} {join_pages(found)}: {label}.")
    if rotated:
        sentences.append(f"Enderezó páginas que venían giradas: {', '.join(map(str, rotated))}.")
    if watermarked:
        sentences.append(f"Detectó marca de agua en las páginas {', '.join(map(str, watermarked))}.")

    return {"metricas": metrics, "interpretacion": sentences}
