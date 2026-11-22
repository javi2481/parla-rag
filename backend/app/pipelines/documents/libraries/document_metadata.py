"""Lo que comparten los dos motores de bibliotecas (local y LlamaCloud):
la metadata de identidad de cada documento y el resumen de una búsqueda de prueba.
"""
from app.core.runs.store import RunStore, read_json

# Los tipos de valor que pueden ir en la metadata de identidad (los grupos y las listas no).
IDENTITY_TYPES = (str, int, float, bool)


# Arma la metadata de identidad de un documento a partir de su corrida del wizard:
# el tipo que eligió Classify y los datos de identidad que sacó Extract, o sea los campos sueltos del primer nivel
# que el schema marca como obligatorios (emisor, período, fecha…). Los datos como el resultado neto no entran.
# Son datos trazables: cada uno tiene su cita en la corrida. Sirven para filtrar la búsqueda.
def identity_metadata(runs: RunStore, run: dict) -> dict:
    folder = runs.run_dir(run["id"])
    metadata = {"corrida": run["id"], "nombre": run["name"]}
    if (folder / "4_classify" / "result.json").is_file():
        kind = (read_json(folder / "4_classify" / "result.json") or {}).get("type")
        if kind:
            metadata["tipo"] = kind
    if (folder / "6_extract" / "result.json").is_file() and (folder / "5_schema" / "schema.json").is_file():
        identity = set(read_json(folder / "5_schema" / "schema.json").get("required") or [])
        for key, value in (read_json(folder / "6_extract" / "result.json") or {}).items():
            if key in identity and isinstance(value, IDENTITY_TYPES) and value != "":
                metadata[key] = value
    return metadata


# Las métricas y la interpretación de una búsqueda de prueba.
def summarize_search(response: dict) -> dict:
    results = response.get("results") or []
    documents = {(r.get("metadata") or {}).get("nombre") for r in results} - {None}
    scores = [r["score"] for r in results if r.get("score") is not None]
    metricas = [
        {"label": "Resultados", "value": len(results)},
        {"label": "Documentos distintos", "value": len(documents)},
        {"label": "Mejor score", "value": round(max(scores), 3) if scores else "—"},
        {"label": "Créditos", "value": "1 por búsqueda (lista de precios; no se informa)"},
    ]
    interpretacion = []
    if results:
        interpretacion.append(f"Encontró {len(results)} {'fragmento' if len(results) == 1 else 'fragmentos'} de {len(documents)} {'documento' if len(documents) == 1 else 'documentos'}: " + ", ".join(sorted(documents)) + ".")
    else:
        interpretacion.append("No encontró nada parecido a la pregunta.")
    return {"metricas": metricas, "interpretacion": interpretacion}
