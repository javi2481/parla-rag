"""Voz → texto: transcripción con ElevenLabs Scribe + limpieza de la transcripción."""

import httpx

from app.core.config import Settings

from .clean_transcript import clean_transcript
from .client import API, raise_for_error



def _extension(mime: str) -> str:
    if "mp4" in mime or "m4a" in mime:
        return "m4a"
    for key, ext in (("ogg", "ogg"), ("mpeg", "mp3"), ("wav", "wav")):
        if key in mime:
            return ext
    return "webm"


async def transcribe(audio: bytes, mime: str | None, lang: str, s: Settings) -> str:
    mime = (mime or "audio/webm").split(";")[0]
    files = {"file": (f"audio.{_extension(mime)}", audio, mime)}
    data = {"model_id": s.elevenlabs_stt_model, "tag_audio_events": "false", "language_code": "eng" if lang == "en" else "spa"}
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(f"{API}/speech-to-text", headers={"xi-api-key": s.elevenlabs_api_key}, files=files, data=data)
    raise_for_error(res, "speech_to_text", "No se pudo transcribir el audio.")
    text = res.json().get("text")
    return text.strip()[:5000] if isinstance(text, str) else ""


async def transcribe_and_clean(audio: bytes, mime: str | None, lang: str, s: Settings) -> dict[str, str]:
    raw = await transcribe(audio, mime, lang, s)
    return {"raw": raw, "text": clean_transcript(raw)}
