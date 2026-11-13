"""Voz a texto: transcribe el audio con ElevenLabs Scribe y después limpia la transcripción."""
import httpx

from .clean_transcript import clean_transcript
from .client import API, raise_for_error
from .settings import AudioSettings

MAX_TRANSCRIPT_LENGTH = 5000


# Elige la extensión del archivo según el tipo MIME del audio (ej. "audio/mpeg" → "mp3").
def audio_extension(mime: str) -> str:
    if "mp4" in mime or "m4a" in mime:
        return "m4a"
    if "ogg" in mime:
        return "ogg"
    if "mpeg" in mime:
        return "mp3"
    if "wav" in mime:
        return "wav"
    return "webm"  # lo que graba el navegador


# Manda el audio a Scribe y devuelve el texto tal cual lo transcribió.
async def transcribe(audio: bytes, mime: str | None, lang: str, settings: AudioSettings) -> str:
    # "audio/webm;codecs=opus" → "audio/webm"
    mime = (mime or "audio/webm").split(";")[0]
    language_code = "eng" if lang == "en" else "spa"

    files = {"file": (f"audio.{audio_extension(mime)}", audio, mime)}
    data = {"model_id": settings.elevenlabs_stt_model, "tag_audio_events": "false", "language_code": language_code}

    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(
            f"{API}/speech-to-text",
            headers={"xi-api-key": settings.elevenlabs_api_key},
            files=files,
            data=data,
        )
    raise_for_error(res, "speech_to_text", "No se pudo transcribir el audio.")

    text = res.json().get("text")
    if not isinstance(text, str):
        return ""
    return text.strip()[:MAX_TRANSCRIPT_LENGTH]


# Transcribe y limpia. Devuelve las dos versiones: la cruda y la limpia.
async def transcribe_and_clean(audio: bytes, mime: str | None, lang: str, settings: AudioSettings) -> dict[str, str]:
    raw = await transcribe(audio, mime, lang, settings)
    return {"raw": raw, "text": clean_transcript(raw)}
