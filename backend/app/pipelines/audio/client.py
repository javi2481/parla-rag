"""Constantes y manejo de errores comunes a las llamadas REST de ElevenLabs."""
import logging

import httpx

from .errors import AudioError

API = "https://api.elevenlabs.io/v1"
log = logging.getLogger(__name__)


def raise_for_error(res: httpx.Response, what: str, fallback: str) -> None:
    if res.status_code == 200:
        return
    log.error("elevenlabs %s %s: %s", what, res.status_code, res.text[:300])
    try:
        detail = res.json().get("detail") or {}
    except ValueError:
        detail = {}
    if isinstance(detail, dict) and detail.get("status") == "missing_permissions":
        raise AudioError(f"La API key de ElevenLabs no tiene el permiso «{what}». Habilitalo en ElevenLabs → Developers → API Keys.")
    if res.status_code == 401:
        raise AudioError("La API key de ElevenLabs no es válida.")
    if res.status_code == 429:
        raise AudioError("ElevenLabs está ocupado o se agotó la cuota. Probá en unos minutos.")
    raise AudioError(fallback)
