from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llama_cloud_api_key: str = ""
    llama_cloud_base_url: str = "https://api.cloud.llamaindex.ai"
    # Tier de LlamaExtract: cost_effective (8 cr/pág) · agentic (25) · agentic_plus (60) · turbo (35)
    extract_tier: str = "agentic"
    # Versión del extractor: "latest" o fija ("2.5") para resultados reproducibles.
    extract_version: str = "latest"

    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "ZjGTaa77PsTCKjCfcbjG"  # Javier (clonada, es-AR)
    # Flash v2.5 cuesta la mitad por carácter que v4/multilingual_v2 y es más rápido.
    # Para máxima calidad: eleven_v4 o eleven_multilingual_v2 (el doble de créditos).
    elevenlabs_tts_model: str = "eleven_flash_v2_5"
    tts_cache_dir: str = ".cache/tts"
    tts_cache_max_mb: int = 200
    elevenlabs_stt_model: str = "scribe_v2"

    invoice_daily_limit: int = 50
    audio_limit_per_10_min: int = 30
    tts_max_chars: int = 2500

    cors_origins: str = "http://localhost:5173"

    @property
    def invoice_ready(self) -> bool:
        return bool(self.llama_cloud_api_key)

    @property
    def audio_ready(self) -> bool:
        return bool(self.elevenlabs_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
