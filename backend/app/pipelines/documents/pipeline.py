"""El pipeline de documentos: la lista ordenada de pasos del wizard. Empezá a leer por acá.

    1 Subir      steps/s1_upload.py
    2 Parse      steps/s2_parse.py
    3 Split      steps/s3_split.py
    4 Classify   steps/s4_classify.py
    5 Schema     steps/s5_schema.py
    6 Extract    steps/s6_extract.py

(Biblioteca se suma en la fase 4.)

Cada paso es un módulo con NAME, FOLDER, TITLE y EXPLICACION. El paso 1 corre al subir el archivo;
los demás tienen start() para arrancar el job en LlamaCloud y check() para consultarlo
(Schema no tiene check(): responde en el momento). Los que se configuran en el wizard tienen DEFAULTS.
"""
import logging

from llama_cloud import AsyncLlamaCloud

from app.core.runs.store import RunStore, read_json

from .settings import DocumentsSettings
from .steps import s1_upload, s2_parse, s3_split, s4_classify, s5_schema, s6_extract

log = logging.getLogger(__name__)

STEPS = [s1_upload, s2_parse, s3_split, s4_classify, s5_schema, s6_extract]
STEP_NAMES = [step.NAME for step in STEPS]


# Busca el módulo de un paso por su nombre. Si no existe, lanza LookupError.
def get_step(name: str):
    for step in STEPS:
        if step.NAME == name:
            return step
    raise LookupError("Ese paso no existe.")


# Lee un JSON guardado por un paso, o devuelve None si todavía no existe.
def read_if_exists(path):
    if path.is_file():
        return read_json(path)
    return None


# Devuelve el estado de un paso. Las corridas viejas no tienen los pasos nuevos: se agregan como pendientes.
def step_state(run: dict, name: str) -> dict:
    return run["steps"].setdefault(name, {"state": "pending"})


# Arma todo lo que el wizard necesita mostrar de una corrida: cada paso con su número, título,
# explicación, estado, si está bloqueado, lo que se pidió, las métricas, la interpretación y los archivos.
def describe_run(store: RunStore, run: dict) -> dict:
    steps = []
    previous_done = True
    for number, step in enumerate(STEPS, start=1):
        state = step_state(run, step.NAME)
        folder = store.run_dir(run["id"]) / step.FOLDER
        summary = read_if_exists(folder / "metrics.json") or {}
        steps.append({
            "number": number,
            "name": step.NAME,
            "title": step.TITLE,
            "explicacion": step.EXPLICACION,
            "folder": step.FOLDER,
            "locked": not previous_done,  # un paso se desbloquea cuando termina el anterior
            **state,
            "request": read_if_exists(folder / "request.json"),
            "defaults": getattr(step, "DEFAULTS", None),
            "metricas": summary.get("metricas", []),
            "interpretacion": summary.get("interpretacion", []),
            "files": store.list_files(run["id"], step.FOLDER),
        })
        previous_done = state["state"] == "done"

    total_credits = 0
    for state in run["steps"].values():
        total_credits += state.get("credits") or 0

    return {"id": run["id"], "name": run["name"], "created_at": run["created_at"],
            "total_credits": total_credits, "steps": steps}


# Arranca un paso. Solo se puede si el anterior terminó y si este no está corriendo.
# `options` son las opciones elegidas en el wizard (categorías, reglas, schema, páginas…).
async def start_step(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, run: dict, name: str,
                     options: dict | None = None) -> None:
    step = get_step(name)
    index = STEP_NAMES.index(name)
    if index == 0:
        raise ValueError("El paso Subir corre solo al subir el archivo.")
    if step_state(run, STEP_NAMES[index - 1])["state"] != "done":
        raise ValueError("Primero tiene que terminar el paso anterior.")
    if step_state(run, name)["state"] == "running":
        raise ValueError("Este paso ya está corriendo.")
    await step.start(client, store, run, settings, options)


# Consulta un paso que está corriendo (si no está corriendo, no hace nada).
async def check_step(client: AsyncLlamaCloud, store: RunStore, run: dict, name: str) -> None:
    step = get_step(name)
    if hasattr(step, "check"):
        await step.check(client, store, run)


# Borra en LlamaCloud lo que creó la corrida (el archivo y los jobs). Si algo falla, solo se anota en el log.
async def delete_remote(client: AsyncLlamaCloud, run: dict) -> None:
    file_id = run["steps"]["upload"].get("file_id")
    parse_job_id = run["steps"]["parse"].get("job_id")
    try:
        if parse_job_id:
            await client.parsing.delete(parse_job_id)
        if file_id:
            await client.files.delete(file_id)
    except Exception as e:
        log.warning("No se pudo borrar en LlamaCloud la corrida %s: %s", run["id"], e)
