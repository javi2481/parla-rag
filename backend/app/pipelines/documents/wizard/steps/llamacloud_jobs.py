"""Lo que comparten los pasos que trabajan con un job de LlamaCloud (Split, Classify y Extract).

Todos siguen el mismo ciclo: se crea el job, se consulta cada tanto y, cuando termina, se guarda la respuesta.
"""
from app.core.runs.store import RunStore, mark_failed

# Estados de un job que todavía no terminó. Split los informa en minúscula; el resto, en mayúscula.
WAITING_STATES = {"PENDING", "RUNNING", "PROCESSING"}

# Debajo de esta confianza, un resultado se marca para revisar (la misma regla que en Parse).
LOW_CONFIDENCE = 0.8


# Devuelve el ID del parse del paso 2: Split, Classify y Extract trabajan sobre él, sin volver a mandar el documento.
def parse_job_id(run: dict) -> str:
    return run["steps"]["parse"]["job_id"]


# Lee las opciones que mandó el usuario. Si no mandó, usa las de por defecto.
def option(options: dict | None, key: str, default):
    if options and options.get(key) not in (None, "", []):
        return options[key]
    return default


# Consulta un job que está corriendo.
# Devuelve la respuesta completa (como diccionario) si terminó bien; si sigue corriendo o falló, devuelve None
# y deja anotado el estado en la corrida.
async def poll(store: RunStore, run: dict, name: str, get_job) -> dict | None:
    step = run["steps"][name]
    if step["state"] != "running":
        return None

    job = await get_job(step["job_id"])
    status = str(job.status).upper()
    step["job_status"] = status
    if status in WAITING_STATES:
        store.save(run)
        return None
    if status != "COMPLETED":
        error = getattr(job, "error_message", None) or f"LlamaCloud terminó con estado {status}."
        mark_failed(run, name, error)
        store.save(run)
        return None
    return job.model_dump()
