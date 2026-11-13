"""Paso 4 · Post-proceso del resultado de LlamaExtract.

    normalize_result   deja solo los campos conocidos, con valores limpios
    field_confidence   la confianza (0 a 1) de cada campo
    citation_boxes     dónde está cada dato en el documento, como fracciones de la página
"""
import regex as re

from ..errors import DocumentError
from ..schema import AMOUNT_FIELDS, INVOICE_FIELDS, MAX_PAGES

Value = str | float | None

# A veces el modelo devuelve el "vacío" como texto en lugar de null.
EMPTY_WORDS = {"none", "null", "n/a", "na", "-", "—", "no consta", "no aplica"}

MAX_TEXT_LENGTH = 6000      # largo máximo de un valor de texto
MAX_CITATIONS_PER_FIELD = 20
MAX_BOXES_PER_CITATION = 20
MAX_BOXES_TOTAL = 200


# ── Valores ──────────────────────────────────────────────────────────────


# Quita los asteriscos de protección de los importes: '$***56.764,62' → '$ 56.764,62'.
def clean_amount(value: str) -> str:
    text = re.sub(r"\*+", " ", value)
    text = re.sub(r"\$\s*", "$ ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


# Limpia un valor de un campo: recorta el texto, convierte los "vacíos" en None
# y descarta lo que no sea texto ni número.
def clean_value(key: str, value: object) -> Value:
    if isinstance(value, str):
        text = value.strip()[:MAX_TEXT_LENGTH]
        if not text or text.lower() in EMPTY_WORDS:
            return None
        if key in AMOUNT_FIELDS:
            return clean_amount(text)
        return text

    # bool es un tipo de int en Python, por eso se descarta aparte.
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


# Devuelve un diccionario con todos los campos conocidos y sus valores limpios.
# Los campos que el modelo no devolvió quedan en None; los desconocidos se ignoran.
def normalize_result(raw: object) -> dict[str, Value]:
    # A veces el resultado viene como una lista con un solo elemento.
    if isinstance(raw, list):
        raw = raw[0] if raw else {}
    if not isinstance(raw, dict):
        raise DocumentError("La extracción devolvió un formato inesperado.")

    result: dict[str, Value] = {}
    for key in INVOICE_FIELDS:
        result[key] = clean_value(key, raw.get(key))
    return result


# ── Metadata: confianza y citas ──────────────────────────────────────────


# Saca de la metadata de LlamaExtract la parte con la información de cada campo.
def document_metadata(meta: object) -> dict:
    if not isinstance(meta, dict):
        return {}
    field_metadata = meta.get("field_metadata") or {}
    fields = field_metadata.get("document_metadata")
    if isinstance(fields, dict):
        return fields
    return {}


# Devuelve la confianza (redondeada a 3 decimales) de cada campo conocido.
# Ignora los valores que no estén entre 0 y 1.
def field_confidence(meta: object) -> dict[str, float]:
    result: dict[str, float] = {}
    for field, info in document_metadata(meta).items():
        if field not in INVOICE_FIELDS or not isinstance(info, dict):
            continue
        confidence = info.get("confidence")
        if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
            result[field] = round(float(confidence), 3)
    return result


# Lee la página y sus dimensiones de una cita. Devuelve None si algo no es válido.
def citation_page(citation: dict) -> tuple[int, float, float] | None:
    try:
        page = int(citation.get("page"))
        dimensions = citation.get("page_dimensions") or {}
        width = float(dimensions.get("width"))
        height = float(dimensions.get("height"))
    except (TypeError, ValueError):
        return None
    if page < 1 or page > MAX_PAGES or width <= 0 or height <= 0:
        return None
    return page, width, height


# Convierte una caja en unidades de página a fracciones (de 0 a 1).
# Así se puede dibujar sobre la página sin importar el tamaño en pantalla.
# Devuelve None si la caja no es válida o se sale de la página.
def box_as_fraction(field: str, page: int, width: float, height: float, box: dict) -> dict | None:
    try:
        result = {
            "field": field,
            "page": page,
            "x": float(box["x"]) / width,
            "y": float(box["y"]) / height,
            "w": float(box["w"]) / width,
            "h": float(box["h"]) / height,
        }
    except (TypeError, ValueError, KeyError):
        return None

    # Se acepta un pequeño margen (1%) por redondeos.
    for key in ("x", "y", "w", "h"):
        if result[key] < -0.01 or result[key] > 1.01:
            return None
    if result["w"] <= 0 or result["h"] <= 0:
        return None
    return result


# Devuelve todas las cajas de cita de todos los campos, listas para dibujar sobre el documento.
def citation_boxes(meta: object) -> list[dict]:
    fields = document_metadata(meta)
    boxes: list[dict] = []

    for field in INVOICE_FIELDS:
        info = fields.get(field)
        if not isinstance(info, dict) or not isinstance(info.get("citation"), list):
            continue

        for citation in info["citation"][:MAX_CITATIONS_PER_FIELD]:
            if not isinstance(citation, dict) or not isinstance(citation.get("bounding_boxes"), list):
                continue
            page_info = citation_page(citation)
            if page_info is None:
                continue
            page, width, height = page_info

            for box in citation["bounding_boxes"][:MAX_BOXES_PER_CITATION]:
                fraction = box_as_fraction(field, page, width, height, box)
                if fraction is not None:
                    boxes.append(fraction)

    return boxes[:MAX_BOXES_TOTAL]
