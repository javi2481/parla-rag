from fastapi import APIRouter

from app.pipelines.invoice.schema import INVOICE_FIELDS, MAX_BYTES, MAX_PAGES

from .deps import SettingsDep

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
def config(s: SettingsDep):
    return {
        "invoice": {"ready": s.invoice_ready, "fields": INVOICE_FIELDS, "maxBytes": MAX_BYTES, "maxPages": MAX_PAGES, "dailyLimit": s.invoice_daily_limit, "tier": s.extract_tier},
        "audio": {"ready": s.audio_ready, "ttsMaxChars": s.tts_max_chars, "ttsModel": s.elevenlabs_tts_model, "sttModel": s.elevenlabs_stt_model, "sttMaxSeconds": 180},
    }
