"""Pruebas de la carpeta-DB: crear, leer, listar y borrar corridas, y que no se pueda salir de la carpeta."""
import pytest

from app.core.runs.store import RunStore, mark_done, mark_running, slugify


# Convierte nombres de archivo en nombres de carpeta seguros.
def test_slugify():
    assert slugify("Clase 07 Clasificacion de imagenes.pdf") == "clase-07-clasificacion-de-imagenes"
    assert slugify("Presentación Ñandú.PDF") == "presentacion-nandu"
    assert slugify("###.pdf") == "documento"


# Una corrida nueva arranca con todos sus pasos en "pending" y se puede volver a leer.
def test_create_get_list_and_delete(tmp_path):
    store = RunStore(tmp_path, "documents")
    run = store.create("factura.pdf", ["upload", "parse"])
    assert run["steps"] == {"upload": {"state": "pending"}, "parse": {"state": "pending"}}

    mark_running(run, "upload")
    mark_done(run, "upload", file_id="dfl-1", credits=0)
    store.save(run)

    again = store.get(run["id"])
    assert again["steps"]["upload"]["state"] == "done"
    assert again["steps"]["upload"]["file_id"] == "dfl-1"
    assert [r["id"] for r in store.list_runs()] == [run["id"]]

    store.delete(run["id"])
    assert store.list_runs() == []


# No se puede pedir una corrida ni un archivo fuera de la carpeta de la corrida.
def test_rejects_paths_outside_the_run(tmp_path):
    store = RunStore(tmp_path, "documents")
    run = store.create("factura.pdf", ["upload"])
    (store.step_dir(run["id"], "1_upload") / "a.json").write_text("{}")

    assert store.file_path(run["id"], "1_upload/a.json").name == "a.json"
    with pytest.raises(LookupError):
        store.get("../../etc")
    with pytest.raises(LookupError):
        store.file_path(run["id"], "../../../.env")
    with pytest.raises(LookupError):
        store.file_path(run["id"], "1_upload/no-existe.json")


# Con reset=True la carpeta del paso queda vacía (para re-ejecutar un paso).
def test_step_dir_reset(tmp_path):
    store = RunStore(tmp_path, "documents")
    run = store.create("factura.pdf", ["upload"])
    (store.step_dir(run["id"], "2_parse") / "viejo.md").write_text("x")
    assert list(store.step_dir(run["id"], "2_parse", reset=True).iterdir()) == []
