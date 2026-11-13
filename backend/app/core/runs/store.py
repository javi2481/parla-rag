"""La "base de datos" en carpetas: cada corrida es una carpeta con un run.json y una subcarpeta por paso.

    data/<pipeline>/runs/<id de la corrida>/
        run.json            nombre, fecha y estado de cada paso
        1_upload/           lo que guardó el paso 1
        2_parse/            lo que guardó el paso 2
        ...

El run.json es un diccionario simple, así se puede abrir y leer a mano:

    {
      "id": "2026-11-13_1530_byma-comunicado",
      "name": "BYMA Comunicado de Prensa - 3T26.pdf",
      "created_at": "2026-11-13T15:30:00",
      "steps": {
        "upload": {"state": "done", "started_at": "...", "finished_at": "...", "credits": 0, ...},
        "parse":  {"state": "pending"}
      }
    }

Estados de un paso: "pending" (sin arrancar), "running" (corriendo), "done" (terminó bien) y "failed" (falló).

La misma carpeta-DB sirve para otras cosas con `kind`: por ejemplo las bibliotecas de documentos
viven en data/documents/libraries/<id>/ con el mismo run.json.
"""
import json
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path

# Los IDs de corrida solo pueden tener minúsculas, números, guiones y guiones bajos.
# Así nadie puede pedir una ruta como "../../.env".
RUN_ID_PATTERN = re.compile(r"^[a-z0-9_-]{1,100}$")


# Devuelve la fecha y hora actual en formato ISO, sin microsegundos.
def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# Convierte un nombre de archivo en un texto apto para carpeta: "BYMA Comunicado.pdf" → "byma-comunicado".
def slugify(name: str) -> str:
    without_extension = Path(name).stem
    ascii_text = unicodedata.normalize("NFKD", without_extension).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:50] or "documento"


# Guarda un objeto como JSON legible (con sangría y acentos sin escapar).
def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str))


# Lee un archivo JSON.
def read_json(path: Path) -> object:
    return json.loads(path.read_text())


class RunStore:
    # Prepara la carpeta de corridas de un pipeline, por ejemplo data/documents/runs/.
    # `kind` cambia la subcarpeta: "libraries" guarda las bibliotecas en data/documents/libraries/.
    def __init__(self, data_dir: str | Path, pipeline: str, kind: str = "runs"):
        self.root = Path(data_dir) / pipeline / kind

    # Crea una corrida nueva para un archivo, con todos sus pasos en "pending".
    def create(self, name: str, step_names: list[str]) -> dict:
        moment = datetime.now()
        run_id = f"{moment:%Y-%m-%d_%H%M%S}_{slugify(name)}"
        steps = {}
        for step_name in step_names:
            steps[step_name] = {"state": "pending"}
        run = {"id": run_id, "name": name, "created_at": now(), "steps": steps}
        self.run_dir(run_id).mkdir(parents=True, exist_ok=False)
        self.save(run)
        return run

    # Devuelve todas las corridas, de la más nueva a la más vieja.
    def list_runs(self) -> list[dict]:
        if not self.root.is_dir():
            return []
        runs = []
        for folder in sorted(self.root.iterdir(), reverse=True):
            run_file = folder / "run.json"
            if run_file.is_file():
                runs.append(read_json(run_file))
        return runs

    # Devuelve una corrida. Si no existe, lanza LookupError.
    def get(self, run_id: str) -> dict:
        run_file = self.run_dir(run_id) / "run.json"
        if not run_file.is_file():
            raise LookupError("La corrida no existe.")
        return read_json(run_file)

    # Guarda el run.json de una corrida.
    def save(self, run: dict) -> None:
        write_json(self.run_dir(run["id"]) / "run.json", run)

    # Borra la carpeta entera de una corrida.
    def delete(self, run_id: str) -> None:
        shutil.rmtree(self.run_dir(run_id), ignore_errors=True)

    # Devuelve la carpeta de una corrida. Rechaza los IDs con caracteres raros.
    def run_dir(self, run_id: str) -> Path:
        if not RUN_ID_PATTERN.match(run_id):
            raise LookupError("La corrida no existe.")
        return self.root / run_id

    # Devuelve (y crea si hace falta) la carpeta de un paso, por ejemplo "2_parse".
    # Con reset=True arranca vacía: lo de la ejecución anterior no se borra, se mueve al historial.
    def step_dir(self, run_id: str, folder: str, reset: bool = False) -> Path:
        path = self.run_dir(run_id) / folder
        if reset:
            self.archive(run_id, folder)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Mueve la carpeta de un paso a historial/<carpeta>_<fecha>, para poder auditar las ejecuciones anteriores.
    # Si la carpeta no existe o está vacía, no hace nada.
    def archive(self, run_id: str, folder: str) -> None:
        path = self.run_dir(run_id) / folder
        if not path.is_dir() or not any(path.iterdir()):
            return
        history = self.run_dir(run_id) / "historial"
        history.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
        path.rename(history / f"{folder}_{stamp}")

    # Lista los archivos que guardó un paso, con su ruta relativa a la corrida y su tamaño.
    def list_files(self, run_id: str, folder: str) -> list[dict]:
        run_path = self.run_dir(run_id)
        step_path = run_path / folder
        if not step_path.is_dir():
            return []
        files = []
        for path in sorted(step_path.rglob("*")):
            if path.is_file():
                files.append({"path": str(path.relative_to(run_path)), "size": path.stat().st_size})
        return files

    # Devuelve la ruta de un archivo de la corrida, verificando que no se salga de su carpeta.
    def file_path(self, run_id: str, relative: str) -> Path:
        run_path = self.run_dir(run_id).resolve()
        path = (run_path / relative).resolve()
        if run_path not in path.parents or not path.is_file():
            raise LookupError("El archivo no existe.")
        return path


# Marca un paso como "running" y anota cuándo arrancó. Borra lo de una ejecución anterior.
def mark_running(run: dict, step_name: str, **extra: object) -> None:
    run["steps"][step_name] = {"state": "running", "started_at": now(), **extra}


# Marca un paso como "done" y anota cuándo terminó, más los datos extra (créditos, etc.).
def mark_done(run: dict, step_name: str, **extra: object) -> None:
    step = run["steps"][step_name]
    step.update({"state": "done", "finished_at": now(), **extra})


# Marca un paso como "failed" con el mensaje de error para mostrar.
def mark_failed(run: dict, step_name: str, error: str) -> None:
    step = run["steps"][step_name]
    step.update({"state": "failed", "finished_at": now(), "error": error})
