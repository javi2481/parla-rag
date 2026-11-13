"""Paso 1 · Validación local, antes de gastar créditos.

Revisa el tipo real del archivo (por sus primeros bytes, no por el nombre), el tamaño y la cantidad de páginas.
Si algo falla, el archivo nunca llega a LlamaCloud.
"""
import io
from dataclasses import dataclass
from typing import Literal

from pypdf import PdfReader

from ..errors import DocumentError
from ..schema import MAX_BYTES, MAX_PAGES

DocKind = Literal["pdf", "jpeg", "png", "webp"]
ALLOWED_SUFFIXES = (".pdf", ".jpg", ".jpeg", ".png", ".webp")


@dataclass(frozen=True)
class ValidDocument:
    data: bytes    # el contenido del archivo
    kind: DocKind  # el tipo real detectado
    pages: int     # cantidad de páginas (las imágenes cuentan como 1)

    # Devuelve el tipo MIME para subir el archivo (ej. "application/pdf").
    @property
    def mime(self) -> str:
        if self.kind == "pdf":
            return "application/pdf"
        return f"image/{self.kind}"

    # Devuelve un nombre de archivo neutro: no se manda el nombre original del usuario.
    @property
    def filename(self) -> str:
        extension = "jpg" if self.kind == "jpeg" else self.kind
        return f"comprobante.{extension}"


# Revisa que la extensión sea válida y que el tamaño esté entre 5 bytes y 5 MB.
def validate_file(name: str, size: int) -> None:
    if not name.lower().endswith(ALLOWED_SUFFIXES) or size < 5 or size > MAX_BYTES:
        raise DocumentError("Elegí un PDF o una foto (JPG, PNG o WebP) de hasta 5 MB.")


# Detecta el tipo real del archivo mirando sus primeros bytes ("bytes mágicos").
# Devuelve None si no es ninguno de los tipos aceptados.
def detect_kind(head: bytes) -> DocKind | None:
    if head[:5] == b"%PDF-":
        return "pdf"
    if head[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if head[:4] == b"\x89PNG":
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


# Cuenta las páginas de un PDF. Si está roto o tiene contraseña, corta con un error.
def pdf_page_count(data: bytes) -> int:
    message = "El PDF está dañado o protegido con contraseña."
    try:
        reader = PdfReader(io.BytesIO(data))
        encrypted = reader.is_encrypted
        pages = len(reader.pages)
    except Exception as e:
        raise DocumentError(message) from e
    if encrypted:
        raise DocumentError(message)
    return pages


# Revisa que la cantidad de páginas esté entre 1 y el máximo permitido.
def validate_page_count(count: int) -> None:
    if count < 1 or count > MAX_PAGES:
        raise DocumentError(f"Se admiten PDFs de hasta {MAX_PAGES} páginas.")


# Corre todas las validaciones y devuelve el documento listo para subir.
def validate(name: str, data: bytes) -> ValidDocument:
    validate_file(name, len(data))

    kind = detect_kind(data[:12])
    if kind is None:
        raise DocumentError("El archivo no es un PDF ni una imagen válida (JPG, PNG o WebP).")

    if kind == "pdf":
        pages = pdf_page_count(data)
    else:
        pages = 1
    validate_page_count(pages)

    return ValidDocument(data, kind, pages)
