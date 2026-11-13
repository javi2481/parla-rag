"""Texto → voz: limpieza del texto (menos caracteres = menos créditos), caché en disco y síntesis."""
from dataclasses import dataclass
from functools import lru_cache

import httpx
import regex as re

from app.core.config import Settings

from .cache import AudioCache
from .client import API, raise_for_error
from .errors import AudioError

# Mismos ajustes de voz que la grabación de referencia (s50 sim75).
VOICE_SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0, "use_speaker_boost": True, "speed": 1.0}
OUTPUT_FORMAT = "mp3_44100_64"


@dataclass
class Speech:
    audio: bytes
    credits: int | None  # créditos cobrados por ElevenLabs; 0 si vino de la caché
    cached: bool
    characters: int


def to_speech(text: str) -> str:
    """Quita markdown, links, emojis y viñetas: la voz lee prosa natural y no se pagan caracteres de más."""
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[*_`#>~|]+", "", t)
    t = re.sub(r"^\s*(?:[-•]|\d+[.)])\s+", "", t, flags=re.M)
    t = re.sub(r"\p{Extended_Pictographic}|️", "", t)
    t = re.sub(r"\s*\n+\s*", ". ", t)
    t = re.sub(r"([.!?])(?:\s*[.!?])+", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


@lru_cache
def _cache(directory: str, max_mb: int) -> AudioCache:
    return AudioCache(directory, max_mb)


async def synthesize(text: str, s: Settings) -> Speech:
    speech = to_speech(text)
    if not speech:
        raise AudioError("El texto quedó vacío después de limpiarlo.")
    cache = _cache(s.tts_cache_dir, s.tts_cache_max_mb)
    key = AudioCache.key(text=speech, model=s.elevenlabs_tts_model, voice=s.elevenlabs_voice_id, settings=VOICE_SETTINGS, fmt=OUTPUT_FORMAT)
    if (hit := cache.get(key)) is not None:
        return Speech(hit, 0, True, len(speech))
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"{API}/text-to-speech/{s.elevenlabs_voice_id}",
            params={"output_format": OUTPUT_FORMAT},
            headers={"xi-api-key": s.elevenlabs_api_key},
            json={"text": speech, "model_id": s.elevenlabs_tts_model, "voice_settings": VOICE_SETTINGS},
        )
    raise_for_error(res, "text_to_speech", "No se pudo generar el audio.")
    cache.put(key, res.content)
    cost = res.headers.get("character-cost")
    return Speech(res.content, int(cost) if cost and cost.isdigit() else None, False, len(speech))
