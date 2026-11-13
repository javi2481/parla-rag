from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.core.config import Settings, get_settings
from app.pipelines.invoice.pipeline import InvoicePipeline

SettingsDep = Annotated[Settings, Depends(get_settings)]


def invoice_pipeline(request: Request, s: SettingsDep) -> InvoicePipeline:
    if not s.invoice_ready:
        raise HTTPException(503, "Falta configurar LLAMA_CLOUD_API_KEY.")
    return request.app.state.invoice_pipeline


def audio_settings(s: SettingsDep) -> Settings:
    if not s.audio_ready:
        raise HTTPException(503, "Falta configurar ELEVENLABS_API_KEY.")
    return s
