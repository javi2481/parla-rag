"""Paso 1 · Validación local: tipo real por bytes mágicos, tamaño y cantidad de páginas."""
import io
from dataclasses import dataclass
from typing import Literal

from pypdf import PdfReader

from ..errors import InvoiceError
from ..schema import MAX_BYTES, MAX_PAGES

DocKind = Literal["pdf", "jpeg", "png", "webp"]
ALLOWED_SUFFIXES = (".pdf", ".jpg", ".jpeg", ".png", ".webp")


@dataclass(frozen=True)
class ValidDocument:
    data: bytes
    kind: DocKind
    pages: int

    @property
    def mime(self) -> str:
        return "application/pdf" if self.kind == "pdf" else f"image/{self.kind}"

    @property
    def filename(self) -> str:
        return f"comprobante.{'jpg' if self.kind == 'jpeg' else self.kind}"


def validate_file(name: str, size: int) -> None:
    if not name.lower().endswith(ALLOWED_SUFFIXES) or size < 5 or size > MAX_BYTES:
        raise InvoiceError("Elegí un PDF o una foto (JPG, PNG o WebP) de hasta 5 MB.")


def detect_kind(head: bytes) -> DocKind | None:
    """Detecta el tipo real del archivo por sus primeros bytes, ignorando el nombre."""
    if head[:5] == b"%PDF-":
        return "pdf"
    if head[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if head[:4] == b"\x89PNG":
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def pdf_page_count(data: bytes) -> int:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise InvoiceError("El PDF está dañado o protegido con contraseña.")
        return len(reader.pages)
    except InvoiceError:
        raise
    except Exception as e:
        raise InvoiceError("El PDF está dañado o protegido con contraseña.") from e


def validate_page_count(count: int) -> None:
    if count < 1 or count > MAX_PAGES:
        raise InvoiceError(f"Se admiten PDFs de hasta {MAX_PAGES} páginas.")


def validate(name: str, data: bytes) -> ValidDocument:
    validate_file(name, len(data))
    kind = detect_kind(data[:12])
    if not kind:
        raise InvoiceError("El archivo no es un PDF ni una imagen válida (JPG, PNG o WebP).")
    pages = pdf_page_count(data) if kind == "pdf" else 1
    validate_page_count(pages)
    return ValidDocument(data, kind, pages)
