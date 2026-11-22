"""Las conversaciones del chat (las pestañas): cada una es una carpeta con su historial.

    libraries/<id>/chats/local/<conversación>/
        conversacion.json   id, cuándo se creó y si está cerrada
        turno_1.json …      cada pregunta con su respuesta y todo lo que pasó en el medio

El id es la fecha y hora en que se creó, como las corridas. Cerrar una conversación solo la oculta: no se borra nada.
"""
from pathlib import Path

from llama_index.core.llms import ChatMessage

from app.core.runs.store import RunStore, now, read_json, stamp, write_json

# Dónde viven las conversaciones dentro de la carpeta de la biblioteca.
CONVERSATIONS = "chats/local"


# Crea una conversación vacía. Si ya hay una creada en el mismo segundo, se le suma un número al id.
def create_conversation(store: RunStore, library: dict) -> dict:
    base = conversation_id = stamp()
    root = store.run_dir(library["id"]) / CONVERSATIONS
    for n in range(2, 100):
        if not (root / conversation_id).exists():
            break
        conversation_id = f"{base}_{n}"
    conversation = {"id": conversation_id, "creada": now(), "cerrada": False}
    write_json(store.step_dir(library["id"], f"{CONVERSATIONS}/{conversation_id}") / "conversacion.json", conversation)
    return conversation


# La carpeta de una conversación. Si no existe (o el id trae algo raro, como "../"), da LookupError.
def conversation_folder(store: RunStore, library: dict, conversation_id: str) -> Path:
    folder = store.run_dir(library["id"]) / CONVERSATIONS / conversation_id
    if "/" in conversation_id or "\\" in conversation_id or ".." in conversation_id or not (folder / "conversacion.json").is_file():
        raise LookupError("La conversación no existe.")
    return folder


# Los turnos guardados de una carpeta, en orden (turno_1, turno_2...).
def saved_turns(folder: Path) -> list[dict]:
    return [read_json(path) for path in sorted(folder.glob("turno_*.json"), key=lambda p: int(p.stem.split("_")[1]))]


# Lo que muestra una pestaña: el id, el título (las primeras 6 palabras de la primera pregunta) y cuántos turnos tiene.
def conversation_summary(folder: Path) -> dict:
    conversation = read_json(folder / "conversacion.json")
    turns = saved_turns(folder)
    title = " ".join(turns[0]["prompt"].split()[:6]) if turns else "Conversación nueva"
    return {"id": conversation["id"], "titulo": title, "creada": conversation["creada"], "turnos": len(turns),
            "cerrada": conversation["cerrada"]}


# Las conversaciones abiertas de una biblioteca, de la más vieja a la más nueva (el orden de las pestañas).
# Los turnos sueltos de antes (chats/local/turno_N.json) no son una conversación y no aparecen.
def list_conversations(store: RunStore, library: dict) -> list[dict]:
    root = store.run_dir(library["id"]) / CONVERSATIONS
    folders = sorted(path.parent for path in root.glob("*/conversacion.json"))
    return [summary for summary in map(conversation_summary, folders) if not summary["cerrada"]]


# Cierra una conversación: queda en disco, pero ya no aparece en las pestañas.
def close_conversation(store: RunStore, library: dict, conversation_id: str) -> dict:
    folder = conversation_folder(store, library, conversation_id)
    conversation = read_json(folder / "conversacion.json")
    conversation["cerrada"] = True
    write_json(folder / "conversacion.json", conversation)
    return conversation_summary(folder)


# Las preguntas y respuestas anteriores de una conversación, para que el modelo entienda preguntas como "¿y el trimestre anterior?".
# Lee solo los turnos de esa carpeta: cada conversación tiene su propio historial.
def chat_history(folder: Path) -> list[ChatMessage]:
    history = []
    for turn in saved_turns(folder):
        if turn.get("answer"):
            history += [ChatMessage(role="user", content=turn["prompt"]), ChatMessage(role="assistant", content=turn["answer"])]
    return history
