"""Lo que comparten las rutas del wizard y las de las bibliotecas: la configuración, el cliente de LlamaCloud,
la carpeta-DB de las corridas y cómo se muestra un error de LlamaCloud.

FastAPI arma cada una de estas cosas en cada pedido (Depends), así las rutas no las crean a mano.
"""
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from llama_cloud import APIError, AsyncLlamaCloud

from app.core.runs.store import RunStore
from app.core.settings import CoreSettings, get_core_settings
from app.pipelines.documents.settings import DocumentsSettings, get_documents_settings

log = logging.getLogger(__name__)

SettingsDep = Annotated[DocumentsSettings, Depends(get_documents_settings)]


# Devuelve el cliente de LlamaCloud creado al arrancar la app. Si falta la API key, responde 503.
def get_client(request: Request, settings: SettingsDep) -> AsyncLlamaCloud:
    if not settings.ready:
        raise HTTPException(503, "Falta configurar LLAMA_CLOUD_API_KEY.")
    return request.app.state.documents_client


# Devuelve la carpeta-DB de las corridas del wizard (data/documents/runs/).
def get_store(core: Annotated[CoreSettings, Depends(get_core_settings)]) -> RunStore:
    return RunStore(core.data_dir, "documents")


ClientDep = Annotated[AsyncLlamaCloud, Depends(get_client)]
StoreDep = Annotated[RunStore, Depends(get_store)]


# Convierte un error de LlamaCloud en un 502 con un mensaje entendible.
def llama_cloud_error(e: APIError) -> HTTPException:
    log.error("LlamaCloud: %s", e)
    return HTTPException(502, f"LlamaCloud respondió con un error: {e.message}")
