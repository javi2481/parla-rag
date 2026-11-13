"""Texto a voz: limpia el texto, busca en la caché y, si no está, lo genera con ElevenLabs.

Limpiar el texto ahorra plata: ElevenLabs cobra por carácter.
"""
from dataclasses import dataclass
from functools import lru_cache

import httpx
import regex as re

from .cache import AudioCache
from .client import API, raise_for_error
from .errors import AudioError
from .settings import AudioSettings

# Los mismos ajustes de voz que la grabación de referencia.
VOICE_SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0, "use_speaker_boost": True, "speed": 1.0}
OUTPUT_FORMAT = "mp3_44100_64"


@dataclass
class Speech:
    audio: bytes         # el MP3
    credits: int | None  # créditos que cobró ElevenLabs (0 si vino de la caché)
    cached: bool         # True si salió de la caché
    characters: int      # caracteres que se mandaron a sintetizar


# Saca markdown, links, emojis y viñetas para que la voz lea prosa natural
# y no se paguen caracteres de más.
def to_speech(text: str) -> str:
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)          # [texto](link) → texto
    t = re.sub(r"https?://\S+", "", t)                          # URLs sueltas
    t = re.sub(r"[*_`#>~|]+", "", t)                            # símbolos de markdown
    t = re.sub(r"^\s*(?:[-•]|\d+[.)])\s+", "", t, flags=re.M)   # viñetas y listas numeradas
    t = re.sub(r"\p{Extended_Pictographic}|️", "", t)           # emojis
    t = re.sub(r"\s*\n+\s*", ". ", t)                           # saltos de línea → punto
    t = re.sub(r"([.!?])(?:\s*[.!?])+", r"\1", t)               # "!!" o ". ." → uno solo
    t = re.sub(r"\s{2,}", " ", t)                               # espacios de más
    return t.strip()


# Crea (una sola vez) la caché de audios.
@lru_cache
def get_cache(directory: str, max_mb: int) -> AudioCache:
    return AudioCache(directory, max_mb)


# Lee de la respuesta de ElevenLabs cuántos créditos cobró (None si no lo dice).
def credits_charged(res: httpx.Response) -> int | None:
    cost = res.headers.get("character-cost")
    if cost and cost.isdigit():
        return int(cost)
    return None


# Convierte un texto en voz con la voz clonada. Si ya se generó antes, lo devuelve de la caché.
async def synthesize(text: str, settings: AudioSettings) -> Speech:
    speech_text = to_speech(text)
    if not speech_text:
        raise AudioError("El texto quedó vacío después de limpiarlo.")

    cache = get_cache(settings.tts_cache_dir, settings.tts_cache_max_mb)
    key = AudioCache.key(
        text=speech_text,
        model=settings.elevenlabs_tts_model,
        voice=settings.elevenlabs_voice_id,
        settings=VOICE_SETTINGS,
        fmt=OUTPUT_FORMAT,
    )
    cached_audio = cache.get(key)
    if cached_audio is not None:
        return Speech(cached_audio, 0, True, len(speech_text))

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"{API}/text-to-speech/{settings.elevenlabs_voice_id}",
            params={"output_format": OUTPUT_FORMAT},
            headers={"xi-api-key": settings.elevenlabs_api_key},
            json={"text": speech_text, "model_id": settings.elevenlabs_tts_model, "voice_settings": VOICE_SETTINGS},
        )
    raise_for_error(res, "text_to_speech", "No se pudo generar el audio.")

    cache.put(key, res.content)
    return Speech(res.content, credits_charged(res), False, len(speech_text))
