"""Paso 4 · Post-proceso: valores limpios, cajas de citas (fracciones de página) y confianza por campo."""
import regex as re

from ..errors import InvoiceError
from ..schema import AMOUNT_FIELDS, INVOICE_FIELDS, MAX_PAGES

Value = str | float | None
# A veces el modelo devuelve el "vacío" como texto en lugar de null.
_EMPTY = {"none", "null", "n/a", "na", "-", "—", "no consta", "no aplica"}


def clean_amount(value: str) -> str:
    """Quita los asteriscos de protección de importes: '$***56.764,62' → '$ 56.764,62'."""
    v = re.sub(r"\*+", " ", value)
    v = re.sub(r"\$\s*", "$ ", v)
    return re.sub(r"\s{2,}", " ", v).strip()


def normalize_result(raw: object) -> dict[str, Value]:
    if isinstance(raw, list):
        raw = raw[0] if raw else {}
    if not isinstance(raw, dict):
        raise InvoiceError("La extracción devolvió un formato inesperado.")
    out: dict[str, Value] = {}
    for key in INVOICE_FIELDS:
        v = raw.get(key)
        if isinstance(v, str):
            v = v.strip()[:6000]
            v = None if not v or v.lower() in _EMPTY else v
            if v and key in AMOUNT_FIELDS:
                v = clean_amount(v)
        elif not isinstance(v, (int, float)) or isinstance(v, bool):
            v = None
        out[key] = v
    return out


def _document_metadata(meta: object) -> dict:
    fields = ((meta or {}).get("field_metadata") or {}).get("document_metadata") if isinstance(meta, dict) else None
    return fields if isinstance(fields, dict) else {}


def field_confidence(meta: object) -> dict[str, float]:
    out: dict[str, float] = {}
    for field, info in _document_metadata(meta).items():
        c = info.get("confidence") if isinstance(info, dict) else None
        if field in INVOICE_FIELDS and isinstance(c, (int, float)) and 0 <= c <= 1:
            out[field] = round(float(c), 3)
    return out


def citation_boxes(meta: object) -> list[dict]:
    """Convierte las citas (unidades de página) a fracciones para superponerlas en cualquier tamaño de render."""
    fields = _document_metadata(meta)
    out: list[dict] = []
    for field in INVOICE_FIELDS:
        info = fields.get(field)
        citations = info.get("citation") if isinstance(info, dict) else None
        if not isinstance(citations, list):
            continue
        for c in citations[:20]:
            if not isinstance(c, dict):
                continue
            try:
                page = int(c.get("page"))
                dims = c.get("page_dimensions") or {}
                W, H = float(dims.get("width")), float(dims.get("height"))
            except (TypeError, ValueError):
                continue
            if not 1 <= page <= MAX_PAGES or W <= 0 or H <= 0 or not isinstance(c.get("bounding_boxes"), list):
                continue
            for b in c["bounding_boxes"][:20]:
                try:
                    box = {"field": field, "page": page, "x": float(b["x"]) / W, "y": float(b["y"]) / H, "w": float(b["w"]) / W, "h": float(b["h"]) / H}
                except (TypeError, ValueError, KeyError):
                    continue
                if all(-0.01 <= box[k] <= 1.01 for k in ("x", "y", "w", "h")) and box["w"] > 0 and box["h"] > 0:
                    out.append(box)
    return out[:200]
