import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import audio, config, invoice
from app.core.config import get_settings
from app.pipelines.invoice.client import make_client
from app.pipelines.invoice.pipeline import InvoicePipeline

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    client = make_client(s)
    app.state.invoice_pipeline = InvoicePipeline(client, s)
    yield
    await client.close()


app = FastAPI(title="Parla API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()], allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Credits", "X-Characters", "X-Cache"])
app.include_router(config.router)
app.include_router(invoice.router)
app.include_router(audio.router)

# En producción, FastAPI sirve el build del frontend (npm run build → frontend/dist).
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
