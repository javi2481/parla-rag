"""Pruebas de las métricas y la interpretación del paso Parse, con una respuesta parecida a la real."""
from app.pipelines.documents.steps.s2_parse import summarize

# Una respuesta de LlamaParse recortada: 3 páginas, la 2 con confianza baja y un gráfico.
RESPONSE = {
    "job": {"usage": {"credits": 63.0}},
    "metadata": {
        "pages": [
            {"page_number": 1, "confidence": 1.0, "original_orientation_angle": 0, "watermark": None},
            {"page_number": 2, "confidence": 0.3, "original_orientation_angle": 0, "watermark": None},
            {"page_number": 3, "confidence": 0.95, "original_orientation_angle": 90, "watermark": None},
        ],
        "document": {"confidence": 0.75},
    },
    "text": {"pages": [{"text": "uno dos tres"}, {"text": "cuatro"}, {"text": ""}]},
    "items": {"pages": [
        {"page_number": 1, "items": [{"type": "heading"}, {"type": "table"}]},
        {"page_number": 2, "items": [{"type": "table", "merged_from_pages": [2, 3],
                    "parse_concerns": [{"type": "header_value_type_mismatch", "details": "..."},
                                       {"type": "multi_table_page", "details": "2 tables"}]},
                   {"type": "table"}]},
        {"page_number": 3, "items": []},
    ]},
    "images_content_metadata": {"images": [
        {"filename": "page_2_chart_1_v2.jpg", "category": "layout"},
        {"filename": "page_1_table_1_v2.jpg", "category": "layout"},
        {"filename": "page_1.jpg", "category": "screenshot"},
    ]},
    "job_metadata": {"latency": {"total_ms": 9500}, "pdf-inputTokens": 1000, "pdf-outputTokens": 200},
}


# Las métricas salen de contar lo que devolvió LlamaParse.
def test_metrics():
    metrics = {m["label"]: m["value"] for m in summarize(RESPONSE)["metricas"]}
    assert metrics["Páginas"] == 3
    assert metrics["Palabras"] == "4"
    assert metrics["Tablas"] == 3
    assert metrics["Gráficos"] == 1
    assert metrics["Confianza del documento"] == "75%"
    assert metrics["Créditos"] == 63.0
    assert metrics["Tiempo de procesamiento"] == "9,5 s"
    assert metrics["Tablas unidas entre páginas"] == 1
    assert metrics["Dudas de LlamaParse para revisar"] == 1
    assert metrics["Tokens del modelo (entrada / salida)"] == "1.000 / 200"


# La interpretación señala la página a revisar, el costo por página y la página girada.
def test_interpretation():
    text = " ".join(summarize(RESPONSE)["interpretacion"])
    assert "cobró 63 créditos (21 por página)" in text
    assert "Conviene revisar la página 2: tiene 30% de confianza. LlamaParse no informa el motivo" in text
    assert "incluido 1 gráfico que convirtió en tabla" in text
    assert "Unió 1 tabla que seguía en la página siguiente (páginas 2–3)" in text
    assert "duda en la página 2: columna con un valor de otro tipo" in text
    assert "varias tablas" not in text  # el aviso informativo no se lista como duda
    assert "girada" in text
