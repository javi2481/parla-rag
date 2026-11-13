from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.limits import RateLimiter, client_ip
from app.pipelines.audio.errors import AudioError
from app.pipelines.audio.stt import transcribe_and_clean
from app.pipelines.audio.tts import synthesize

from .deps import audio_settings

router = APIRouter(prefix="/api/audio", tags=["audio"])
MAX_AUDIO_BYTES = 10 * 1024 * 1024
AudioSettings = Annotated[Settings, Depends(audio_settings)]


@lru_cache
def _limiter() -> RateLimiter:
    return RateLimiter(get_settings().audio_limit_per_10_min, 600, "Demasiadas solicitudes de audio. Esperá unos minutos.")


class TtsIn(BaseModel):
    text: str = Field(min_length=1)


@router.post("/tts", response_class=Response)
async def tts(body: TtsIn, request: Request, s: AudioSettings):
    text = body.text.strip()
    if not text or len(text) > s.tts_max_chars:
        raise HTTPException(422, f"El texto debe tener entre 1 y {s.tts_max_chars} caracteres.")
    _limiter().check(client_ip(request))
    try:
        speech = await synthesize(text, s)
    except AudioError as e:
        raise HTTPException(502, str(e)) from e
    headers = {"X-Characters": str(speech.characters), "X-Cache": "hit" if speech.cached else "miss"}
    if speech.credits is not None:
        headers["X-Credits"] = str(speech.credits)
    return Response(speech.audio, media_type="audio/mpeg", headers=headers)


@router.post("/transcribe")
async def transcribe(
    request: Request,
    s: AudioSettings,
    file: Annotated[UploadFile, File()],
    lang: Annotated[Literal["es", "en"], Form()] = "es",
):
    if file.content_type and not file.content_type.startswith(("audio/", "video/webm")):
        raise HTTPException(415, "Subí un archivo de audio.")
    audio = await file.read(MAX_AUDIO_BYTES + 1)
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "El audio debe pesar hasta 10 MB.")
    _limiter().check(client_ip(request))
    try:
        return await transcribe_and_clean(audio, file.content_type, lang, s)
    except AudioError as e:
        raise HTTPException(502, str(e)) from e
