"""Punto de entrada de la API. Acá solo se arma la app y se conectan los pipelines.

La lógica de cada pipeline vive en su carpeta, dentro de app/pipelines/.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.settings import get_core_settings
from app.pipelines.documents import library_router as libraries
from app.pipelines.documents import router as documents
from app.pipelines.documents.client import make_client
from app.pipelines.documents.settings import DocumentsSettings, get_documents_settings

logging.basicConfig(level=logging.INFO)


# Lo que pasa al arrancar y al apagar el servidor: se crea el cliente de LlamaCloud
# y al final se cierra su conexión.
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.documents_client = make_client(get_documents_settings())
    yield
    await app.state.documents_client.close()


app = FastAPI(title="Parla RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_core_settings().cors_origin_list(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(libraries.router)


# GET /api/config: le cuenta al frontend qué pipelines están listos y con qué opciones.
@app.get("/api/config", tags=["config"])
def config(
    documents_settings: Annotated[DocumentsSettings, Depends(get_documents_settings)],
):
    return {"documents": documents.public_config(documents_settings)}


# En producción, FastAPI también sirve el frontend compilado (npm run build → frontend/dist).
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
