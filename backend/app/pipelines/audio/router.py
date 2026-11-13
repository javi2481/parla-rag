"""Rutas HTTP del pipeline de audio: /api/audio/...

Son finas a propósito: validan el pedido, llaman a tts.py o stt.py y traducen los errores a códigos HTTP.
"""
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, Field

from app.core.limits import RateLimiter, client_ip

from .errors import AudioError
from .settings import AudioSettings, get_audio_settings
from .stt import transcribe_and_clean
from .tts import synthesize

router = APIRouter(prefix="/api/audio", tags=["audio"])

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB


# Devuelve la configuración de audio. Si falta la API key, responde 503.
def ready_settings(settings: Annotated[AudioSettings, Depends(get_audio_settings)]) -> AudioSettings:
    if not settings.ready:
        raise HTTPException(503, "Falta configurar ELEVENLABS_API_KEY.")
    return settings


ReadySettings = Annotated[AudioSettings, Depends(ready_settings)]


# Crea (una sola vez) el limitador de pedidos de audio cada 10 minutos.
@lru_cache
def limiter() -> RateLimiter:
    limit = get_audio_settings().audio_limit_per_10_min
    return RateLimiter(limit, 10 * 60, "Demasiadas solicitudes de audio. Esperá unos minutos.")


# Configuración pública que necesita el frontend (nunca incluye la API key).
def public_config(settings: AudioSettings) -> dict:
    return {
        "ready": settings.ready,
        "ttsMaxChars": settings.tts_max_chars,
        "ttsModel": settings.elevenlabs_tts_model,
        "sttModel": settings.elevenlabs_stt_model,
        "sttMaxSeconds": settings.stt_max_seconds,
    }


class TtsIn(BaseModel):
    text: str = Field(min_length=1)


# POST /api/audio/tts: convierte un texto en voz y devuelve el MP3.
# En los encabezados X-Characters, X-Cache y X-Credits va lo que costó.
@router.post("/tts", response_class=Response)
async def tts(body: TtsIn, request: Request, settings: ReadySettings):
    text = body.text.strip()
    if not text or len(text) > settings.tts_max_chars:
        raise HTTPException(422, f"El texto debe tener entre 1 y {settings.tts_max_chars} caracteres.")
    limiter().check(client_ip(request))

    try:
        speech = await synthesize(text, settings)
    except AudioError as e:
        raise HTTPException(502, str(e)) from e

    headers = {
        "X-Characters": str(speech.characters),
        "X-Cache": "hit" if speech.cached else "miss",
    }
    if speech.credits is not None:
        headers["X-Credits"] = str(speech.credits)
    return Response(speech.audio, media_type="audio/mpeg", headers=headers)


# POST /api/audio/transcribe: recibe un audio y devuelve la transcripción cruda y la limpia.
@router.post("/transcribe")
async def transcribe(
    request: Request,
    settings: ReadySettings,
    file: Annotated[UploadFile, File()],
    lang: Annotated[Literal["es", "en"], Form()] = "es",
):
    if file.content_type and not file.content_type.startswith(("audio/", "video/webm")):
        raise HTTPException(415, "Subí un archivo de audio.")

    # Se lee un byte de más para detectar si el audio supera el máximo.
    audio = await file.read(MAX_AUDIO_BYTES + 1)
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "El audio debe pesar hasta 10 MB.")
    limiter().check(client_ip(request))

    try:
        return await transcribe_and_clean(audio, file.content_type, lang, settings)
    except AudioError as e:
        raise HTTPException(502, str(e)) from e
