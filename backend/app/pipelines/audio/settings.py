"""Configuración del pipeline de audio (ElevenLabs). Se lee de backend/.env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AudioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "ZjGTaa77PsTCKjCfcbjG"  # Javier (voz clonada, es-AR)

    # Flash v2.5 cuesta la mitad por carácter que v4 / multilingual_v2 y es más rápido.
    # Para máxima calidad: eleven_v4 o eleven_multilingual_v2 (el doble de créditos).
    elevenlabs_tts_model: str = "eleven_flash_v2_5"
    elevenlabs_stt_model: str = "scribe_v2"

    # Caché en disco de los audios generados: el mismo texto nunca se paga dos veces.
    tts_cache_dir: str = "data/audio/cache"
    tts_cache_max_mb: int = 200

    tts_max_chars: int = 2500          # largo máximo del texto a convertir en voz
    stt_max_seconds: int = 180         # largo máximo de una grabación (Scribe cobra por minuto)
    audio_limit_per_10_min: int = 30   # pedidos por IP cada 10 minutos (0 = sin límite)

    # Dice si el pipeline está listo para usarse (o sea, si hay API key).
    @property
    def ready(self) -> bool:
        return bool(self.elevenlabs_api_key)


# Lee la configuración una sola vez y la reutiliza.
@lru_cache
def get_audio_settings() -> AudioSettings:
    return AudioSettings()
