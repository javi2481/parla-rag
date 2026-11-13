from app.pipelines.documents.steps.postprocess import citation_boxes, clean_amount, field_confidence, normalize_result


def test_clean_amount_removes_check_protection_asterisks():
    assert clean_amount("$***56.764,62") == "$ 56.764,62"
    assert clean_amount("ARS $ 20.000,00") == "ARS $ 20.000,00"
    assert clean_amount("21%: $****9.201,27") == "21%: $ 9.201,27"


def test_normalize_result_keeps_only_known_fields():
    out = normalize_result([{"total": "$***1.000,00", "neto": 826, "iva": True, "hack": "x", "detalle": "  "}])
    assert out["total"] == "$ 1.000,00" and out["neto"] == 826 and out["iva"] is None and "hack" not in out
    assert out["fecha"] is None and out["detalle"] is None


def test_normalize_result_treats_textual_null_as_empty():
    out = normalize_result({"neto": "None", "iva": "null", "cliente": "No consta", "total": "$ 1"})
    assert (out["neto"], out["iva"], out["cliente"], out["total"]) == (None, None, None, "$ 1")


META = {"field_metadata": {"document_metadata": {
    "total": {"confidence": 0.97, "citation": [
        {"page": 1, "page_dimensions": {"width": 200, "height": 100}, "bounding_boxes": [{"x": 20, "y": 10, "w": 100, "h": 50}, {"x": 500, "y": 0, "w": 1, "h": 1}]},
        {"page": 9, "page_dimensions": {"width": 200, "height": 100}, "bounding_boxes": [{"x": 1, "y": 1, "w": 1, "h": 1}]},
    ]},
    "iva": {"confidence": 1.7},
    "hack": {"confidence": 0.5},
}}}


def test_citation_boxes_converts_to_page_fractions():
    assert citation_boxes(META) == [{"field": "total", "page": 1, "x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5}]
    assert citation_boxes(None) == []


def test_field_confidence_only_valid_known_fields():
    assert field_confidence(META) == {"total": 0.97}
