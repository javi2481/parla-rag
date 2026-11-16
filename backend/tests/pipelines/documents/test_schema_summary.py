"""La interpretación del paso Schema, con schemas armados a mano (sin red ni créditos)."""
from app.pipelines.documents.steps.s5_schema import (
    TEMPLATES,
    fields_to_schema,
    forced_fields,
    only_identity_required,
    summarize,
)

NUMBER = {"type": "number"}


# Un campo es "forzado" solo si es obligatorio él y todos los grupos que lo contienen.
def test_forced_fields_follows_the_whole_path():
    schema = {
        "type": "object", "required": ["a", "grupo"],
        "properties": {
            "a": NUMBER, "b": NUMBER,
            "grupo": {"type": "object", "required": ["c"], "properties": {"c": NUMBER, "d": NUMBER}},
        },
    }
    assert forced_fields(schema) == 2  # a y grupo.c


# Si todo es obligatorio (como lo propone el agente), la interpretación avisa que Extract puede inventar.
def test_summary_warns_when_everything_is_required():
    schema = {"type": "object", "required": ["x", "y"], "properties": {"x": NUMBER, "y": NUMBER}}
    result = summarize(schema, "auto", "cfg")
    assert {"label": "Obligatorios", "value": "2 de 2"} in result["metricas"]
    assert any("puede inventarlo" in sentence for sentence in result["interpretacion"])


# La plantilla de resultados trimestrales solo obliga los datos de identidad.
def test_template_only_requires_identity_fields():
    schema = fields_to_schema(TEMPLATES["Resultados trimestrales"])
    assert schema["required"] == ["emisor", "razon_social", "periodo", "fecha_de_cierre"]
    assert not any("puede inventarlo" in s for s in summarize(schema, "manual", "cfg")["interpretacion"])


# La opción A: solo quedan obligatorios los campos sueltos del primer nivel; los grupos y su contenido, no.
def test_only_identity_required():
    schema = {
        "type": "object", "required": ["ticker", "periodo", "resultados"],
        "properties": {
            "ticker": {"type": "string"}, "periodo": {"type": "string"},
            "resultados": {"type": "object", "required": ["ebitda"], "properties": {
                "ebitda": NUMBER,
                "ajustado": {"type": "object", "required": ["ebitda"], "properties": {"ebitda": NUMBER}},
            }},
        },
    }
    fixed = only_identity_required(schema)
    assert fixed["required"] == ["ticker", "periodo"]
    assert fixed["properties"]["resultados"]["required"] == []
    assert fixed["properties"]["resultados"]["properties"]["ajustado"]["required"] == []
    assert forced_fields(fixed) == 2
    assert schema["required"] == ["ticker", "periodo", "resultados"]  # el original no se toca
