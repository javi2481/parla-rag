"""Lo común a todas las llamadas a la API REST de ElevenLabs: la URL base y el manejo de errores."""
import logging

import httpx

from .errors import AudioError

API = "https://api.elevenlabs.io/v1"
log = logging.getLogger(__name__)


# Lee el campo "detail" de una respuesta de error de ElevenLabs (o {} si no viene).
def error_detail(res: httpx.Response) -> dict:
    try:
        detail = res.json().get("detail")
    except ValueError:
        return {}
    if isinstance(detail, dict):
        return detail
    return {}


# Si la respuesta no es 200, corta con un AudioError que explica qué pasó.
# `what` es el permiso usado (ej. "text_to_speech") y `fallback` el mensaje por defecto.
def raise_for_error(res: httpx.Response, what: str, fallback: str) -> None:
    if res.status_code == 200:
        return
    log.error("elevenlabs %s %s: %s", what, res.status_code, res.text[:300])

    if error_detail(res).get("status") == "missing_permissions":
        raise AudioError(
            f"La API key de ElevenLabs no tiene el permiso «{what}». "
            "Habilitalo en ElevenLabs → Developers → API Keys."
        )
    if res.status_code == 401:
        raise AudioError("La API key de ElevenLabs no es válida.")
    if res.status_code == 429:
        raise AudioError("ElevenLabs está ocupado o se agotó la cuota. Probá en unos minutos.")
    raise AudioError(fallback)
