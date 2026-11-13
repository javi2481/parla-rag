import pytest

from app.pipelines.documents.errors import DocumentError
from app.pipelines.documents.steps.validate import detect_kind, pdf_page_count, validate, validate_file


def test_detect_kind_by_magic_bytes():
    assert detect_kind(b"%PDF-1.7\n....") == "pdf"
    assert detect_kind(b"\xff\xd8\xff\xe0" + b"0" * 8) == "jpeg"
    assert detect_kind(b"\x89PNG\r\n\x1a\n0000") == "png"
    assert detect_kind(b"RIFF\x00\x00\x00\x00WEBP") == "webp"
    assert detect_kind(b"MZ not a doc") is None


def test_validate_file_name_and_size():
    validate_file("factura.PDF", 1000)
    with pytest.raises(DocumentError):
        validate_file("factura.exe", 1000)
    with pytest.raises(DocumentError):
        validate_file("factura.pdf", 6 * 1024 * 1024)


def test_validate_pages(pdf):
    doc = validate("f.pdf", pdf(2))
    assert (doc.kind, doc.pages, doc.mime) == ("pdf", 2, "application/pdf")
    with pytest.raises(DocumentError, match="3 páginas"):
        validate("f.pdf", pdf(4))
    with pytest.raises(DocumentError):
        pdf_page_count(b"%PDF-roto")


def test_rejects_renamed_file():
    with pytest.raises(DocumentError, match="no es un PDF"):
        validate("f.pdf", b"MZ......not a pdf")
