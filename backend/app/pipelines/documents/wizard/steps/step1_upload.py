"""Paso 1 · Subir: manda el archivo a LlamaCloud Files y guarda una copia en la corrida.

No se valida el tipo de archivo: LlamaParse acepta PDF, imágenes, Word, Excel, PowerPoint, HTML y más,
y si no puede leer algo lo dice en el paso Parse. Acá solo se controla el tamaño.
"""
import re
from pathlib import Path

from llama_cloud import AsyncLlamaCloud

from app.core.runs.store import RunStore, mark_done, mark_running, write_json

from app.pipelines.documents.errors import DocumentError

NAME = "upload"
FOLDER = "1_upload"
TITLE = "Subir"
# El paso que tiene que estar terminado antes de correr este: ninguno, es el primero.
REQUIRES = None
EXPLICACION = (
    "El archivo se sube a LlamaCloud Files, el almacenamiento de la plataforma. "
    "LlamaCloud le asigna un ID que usan todos los pasos siguientes. "
    "Todavía no se leyó nada: subir no cuesta créditos."
)


# Revisa que el archivo no esté vacío ni supere el máximo permitido.
def check_size(data: bytes, max_mb: int) -> None:
    if not data:
        raise DocumentError("El archivo está vacío.")
    if len(data) > max_mb * 1024 * 1024:
        raise DocumentError(f"El archivo supera los {max_mb} MB.")


# Arma las métricas y la interpretación del paso.
def summarize(filename: str, mime: str, size: int, file_id: str) -> dict:
    size_mb = size / (1024 * 1024)
    return {
        "metricas": [
            {"label": "Archivo", "value": filename},
            {"label": "Tipo", "value": mime},
            {"label": "Tamaño", "value": f"{size_mb:.2f} MB"},
            {"label": "ID en LlamaCloud", "value": file_id},
        ],
        "interpretacion": [
            f"El archivo quedó guardado en LlamaCloud con el ID {file_id}.",
            "El paso siguiente, Parse, lo va a leer y convertir en texto estructurado.",
        ],
    }


# Sube el archivo, guarda la copia original y la respuesta de LlamaCloud, y marca el paso como terminado.
async def run_step(client: AsyncLlamaCloud, store: RunStore, run: dict, filename: str, mime: str, data: bytes) -> None:
    folder = store.step_dir(run["id"], FOLDER)
    mark_running(run, NAME)

    (folder / f"original{suffix_of(filename)}").write_bytes(data)
    request = {"filename": filename, "content_type": mime, "size_bytes": len(data), "purpose": "parse"}
    write_json(folder / "request.json", request)

    file = await client.files.create(file=(filename, data, mime), purpose="parse")
    write_json(folder / "response.json", file.model_dump())
    write_json(folder / "metrics.json", summarize(filename, mime, len(data), file.id))

    mark_done(run, NAME, file_id=file.id, credits=0)
    store.save(run)


# Devuelve la extensión del archivo en minúsculas (".pdf"), solo con letras y números, o "" si no tiene.
def suffix_of(filename: str) -> str:
    extension = re.sub(r"[^a-z0-9]", "", Path(filename).suffix.lower())[:10]
    if not extension:
        return ""
    return "." + extension
