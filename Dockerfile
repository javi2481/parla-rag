# syntax=docker/dockerfile:1

# ── 1 · Build del frontend (React + Vite) ──────────────────────────────
FROM node:22.12-alpine AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ── 2 · Backend (FastAPI) que también sirve el frontend compilado ──────
FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
RUN pip install --no-cache-dir "uv==0.12.2"
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/app ./app
# Los documentos de ejemplo y el set de preguntas de los evals (en un volumen nuevo, Docker los copia la primera vez).
COPY backend/data/samples ./data/samples
COPY --from=frontend /web/dist /app/frontend/dist

RUN useradd --create-home --uid 1000 appuser && mkdir -p data && chown -R appuser data
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/config', timeout=4)"
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
