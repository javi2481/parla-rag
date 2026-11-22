"""El wizard: la lista ordenada de pasos sobre UN documento. Empezá a leer por acá.

    1 Subir      steps/step1_upload.py
    2 Parse      steps/step2_parse.py
    3 Split      steps/step3_split.py
    4 Classify   steps/step4_classify.py
    5 Schema     steps/step5_schema.py
    6 Extract    steps/step6_extract.py

Después, el documento se puede sumar a una biblioteca (ver ../libraries/).

Cada paso es un módulo con NAME, FOLDER, TITLE, REQUIRES y EXPLICACION. REQUIRES es el paso que tiene que
estar terminado antes (Split, Classify y Schema usan el parse; Extract usa el schema). El paso 1 corre al subir el archivo;
los demás tienen start() para arrancar el job en LlamaCloud y check() para consultarlo
(Schema no tiene check(): responde en el momento). Los que se configuran en el wizard tienen DEFAULTS.
"""
import logging

from llama_cloud import AsyncLlamaCloud

from app.core.runs.store import RunStore, read_json
from app.pipelines.documents.settings import DocumentsSettings

from .steps import (
    step1_upload,
    step2_parse,
    step3_split,
    step4_classify,
    step5_schema,
    step6_extract,
)

log = logging.getLogger(__name__)

STEPS = [step1_upload, step2_parse, step3_split, step4_classify, step5_schema, step6_extract]
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
            "locked": not requirement_done(run, step),  # se desbloquea cuando termina el paso que necesita
            "requires_title": get_step(step.REQUIRES).TITLE if step.REQUIRES else None,
            **state,
            "request": read_if_exists(folder / "request.json"),
            "defaults": getattr(step, "DEFAULTS", None),
            "metricas": summary.get("metricas", []),
            "interpretacion": summary.get("interpretacion", []),
            "files": store.list_files(run["id"], step.FOLDER),
        })

    total_credits = 0
    for state in run["steps"].values():
        total_credits += state.get("credits") or 0

    return {"id": run["id"], "name": run["name"], "created_at": run["created_at"],
            "total_credits": total_credits, "steps": steps}


# ¿Ya terminó el paso que este necesita? (el paso 1 no necesita ninguno)
def requirement_done(run: dict, step) -> bool:
    return step.REQUIRES is None or step_state(run, step.REQUIRES)["state"] == "done"


# Arranca un paso. Solo se puede si terminó el paso que necesita y si este no está corriendo.
# `options` son las opciones elegidas en el wizard (categorías, reglas, schema, páginas…).
async def start_step(client: AsyncLlamaCloud, store: RunStore, settings: DocumentsSettings, run: dict, name: str,
                     options: dict | None = None) -> None:
    step = get_step(name)
    if step.REQUIRES is None:
        raise ValueError("El paso Subir corre solo al subir el archivo.")
    if not requirement_done(run, step):
        raise ValueError(f"Primero tiene que terminar el paso {get_step(step.REQUIRES).TITLE}.")
    if step_state(run, name)["state"] == "running":
        raise ValueError("Este paso ya está corriendo.")
    previous = dict(step_state(run, name))
    await step.start(client, store, run, settings, options)
    remember(run, name, previous)
    reset_following(store, run, name)


# Guarda en run["historial"] el estado anterior de un paso (con su job_id), para que quede auditado
# y para poder borrar ese job en LlamaCloud cuando se borre la corrida.
def remember(run: dict, name: str, state: dict) -> None:
    if state.get("state") != "pending":
        run.setdefault("historial", []).append({"step": name, **state})


# Cuando un paso se corre de nuevo, los que lo necesitan quedan desactualizados (usaban el resultado anterior),
# y también los que necesitan a esos (repetir Parse alcanza a Split, Classify, Schema y Extract; repetir Split, a nadie).
# Vuelven a pendiente y su carpeta pasa al historial, así no se mezcla lo viejo con lo nuevo.
def reset_following(store: RunStore, run: dict, name: str) -> None:
    for dependent in STEPS:
        if dependent.REQUIRES != name:
            continue
        if step_state(run, dependent.NAME)["state"] != "pending":
            store.archive(run["id"], dependent.FOLDER)
            remember(run, dependent.NAME, run["steps"][dependent.NAME])
            run["steps"][dependent.NAME] = {"state": "pending"}
        reset_following(store, run, dependent.NAME)
    store.save(run)


# Consulta un paso que está corriendo (si no está corriendo, no hace nada).
async def check_step(client: AsyncLlamaCloud, store: RunStore, run: dict, name: str) -> None:
    step = get_step(name)
    if hasattr(step, "check"):
        await step.check(client, store, run)


# Borra en LlamaCloud lo que creó la corrida: los jobs de cada paso y el archivo subido.
# Las configuraciones no se borran: son plantillas que pueden usar otras corridas.
# Si algo falla, solo se anota en el log.
async def delete_remote(client: AsyncLlamaCloud, run: dict) -> None:
    deleters = {"parse": client.parsing.delete, "split": client.split.delete,
                "classify": client.classify.delete, "extract": client.extract.delete}
    jobs = [(name, state.get("job_id")) for name, state in run["steps"].items()]
    jobs += [(old["step"], old.get("job_id")) for old in run.get("historial", [])]
    for name, job_id in jobs:
        delete = deleters.get(name)
        if not job_id or not delete:
            continue
        try:
            await delete(job_id)
        except Exception as e:  # noqa: BLE001 -- a propósito: si falla un borrado, se avisa y se sigue con el resto
            log.warning("No se pudo borrar en LlamaCloud el job %s de la corrida %s: %s", job_id, run["id"], e)
    file_id = run["steps"]["upload"].get("file_id")
    if file_id:
        try:
            await client.files.delete(file_id)
        except Exception as e:  # noqa: BLE001 -- a propósito: si falla un borrado, se avisa y se sigue con el resto
            log.warning("No se pudo borrar en LlamaCloud el archivo de la corrida %s: %s", run["id"], e)
