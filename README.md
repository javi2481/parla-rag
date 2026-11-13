# Parla

**Documentos que hablan, voces que escriben.**

Parla junta en una sola app tres tareas que suelen pedir tres herramientas distintas: leer facturas, convertir texto en voz y pasar audios a texto. Todo con IA, en español y con el gasto en créditos bajo control.

| | Qué hace | Con qué |
| --- | --- | --- |
| 🧾 **Facturas** | Soltás un PDF o una foto y en unos segundos tenés fecha, proveedor, CUIT, importes e IVA, **marcados sobre el documento** y con un nivel de confianza por campo. Exportás a CSV o Markdown, o escuchás el resumen. | LlamaCloud · LlamaExtract |
| 🔊 **Texto a voz** | Pegás un texto y lo escuchás con tu **voz clonada**. Cada audio muestra lo que costó, y lo repetido sale de la caché sin volver a cobrarse. | ElevenLabs Flash v2.5 |
| 🎙️ **Voz a texto** | Grabás o subís un audio y obtenés la transcripción **sin muletillas, tartamudeos ni repeticiones**, lista para copiar. | ElevenLabs Scribe |

### Por qué está bueno

- **Se ve de dónde sale cada dato**: las cajas de color unen cada campo extraído con su lugar en la factura.
- **Gasta lo justo**: usa el modelo de voz que cuesta la mitad por carácter, quita lo que no hace falta leer y guarda en disco todo lo ya generado.
- **Pipeline prolijo**: validar → subir → extraer → post-procesar → limpiar, con un archivo por paso.
- **Privado**: las API keys viven solo en el servidor y los archivos se borran de LlamaCloud al terminar.
- **Un comando**: `docker compose up` y queda andando en `localhost:8000`.

**Stack:** Python · FastAPI · LlamaCloud SDK · ElevenLabs · React · Vite · Tailwind · Docker

## Estructura

```
backend/
├── app/
│   ├── main.py                     arma la app y conecta las rutas
│   ├── core/                       config (.env) y límites en memoria
│   ├── api/                        rutas HTTP finas: config · invoice · audio
│   └── pipelines/
│       ├── invoice/                ── PIPELINE DE FACTURAS (LlamaCloud SDK `llama-cloud`)
│       │   ├── pipeline.py         orquestador: encadena los pasos en orden
│       │   ├── schema.py           campos, JSON Schema con guías por campo, config de Extract
│       │   ├── client.py           cliente AsyncLlamaCloud
│       │   ├── jobs.py             tickets opacos → jobs del proveedor
│       │   └── steps/
│       │       ├── validate.py     1 · tipo real, tamaño, páginas (local, sin costo)
│       │       ├── upload.py       2 · Files API (purpose="extract")
│       │       ├── extract.py      3 · Extract v2: crear job + consultar estado
│       │       ├── postprocess.py  4 · limpia importes, cajas de citas, confianza
│       │       └── cleanup.py      5 · borra archivo y job en LlamaCloud
│       └── audio/                  ── PIPELINES DE AUDIO (ElevenLabs)
│           ├── client.py           URL base y errores de ElevenLabs (permisos, cuota)
│           ├── cache.py            caché en disco de audios ya pagados
│           ├── tts.py              texto → limpieza → voz clonada (MP3, con caché)
│           ├── stt.py              audio → Scribe → clean_transcript
│           └── clean_transcript.py muletillas, tartamudeos, [tos]
├── tests/                          misma estructura: invoice/ · audio/ · api/
└── doc/                            PDFs de prueba

frontend/src/
├── App.tsx                         pestañas
├── components/ui/                  shadcn (button, slider, tabs, textarea)
└── features/
    ├── invoice-extractor/          InvoiceExtractor, PdfPreview, lib/
    └── audio/                      ListenButton, AudioPlayer, TextToSpeech, SpeechToText, lib/
```

### Pipeline de facturas

`validate → upload → extract (polling) → postprocess → cleanup`

- **Extract v2**, tier configurable (`EXTRACT_TIER`, por defecto `agentic`), con `cite_sources` (cajas por campo) y `confidence_scores` (la UI marca «revisar» los campos con menos de 70%).
- Las guías de cada campo están en su `description` dentro de `schema.py`, como recomienda la documentación de LlamaExtract. Para ajustar qué se extrae, se toca ese archivo.
- Si el archivo no es válido, nunca llega a LlamaCloud y no gasta créditos.
- Para sumar un paso (por ejemplo, **Classify** para rechazar lo que no es factura antes de extraer), se agrega `steps/classify.py` y se llama desde `pipeline.py`.

## Docker (recomendado)

Un solo contenedor: compila el frontend y lo sirve FastAPI junto con la API.

```bash
docker compose up --build -d     # http://localhost:8000
docker compose logs -f           # ver logs
docker compose down              # parar
```

Las API keys se leen de `backend/.env` al arrancar (`env_file`) y nunca se copian a la imagen.

## Configuración

```bash
cd backend
cp .env.example .env      # completar LLAMA_CLOUD_API_KEY y ELEVENLABS_API_KEY
uv sync
```

## Desarrollo

```bash
# terminal 1
cd backend && uv run uvicorn app.main:app --reload --port 8000
# terminal 2 (el proxy de Vite manda /api al backend)
cd frontend && npm install && npm run dev      # http://localhost:5173
```

## Producción (un solo proceso)

```bash
cd frontend && npm run build                   # genera frontend/dist
cd ../backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI sirve `frontend/dist` en `/` y la API en `/api`.

## Tests

```bash
cd backend && uv run pytest
```

## Notas

- Herramienta interna: sin captcha ni Supabase. Los límites son en memoria y por IP (`INVOICE_DAILY_LIMIT`, `AUDIO_LIMIT_PER_10_MIN`) y se reinician con el servidor.
- **Ahorro de créditos en ElevenLabs:**
  - Modelo por defecto `eleven_flash_v2_5`: la mitad de créditos por carácter que `eleven_v4` (medido: 11 contra 23 créditos para la misma frase). Para máxima calidad: `ELEVENLABS_TTS_MODEL=eleven_v4`.
  - Antes de enviar se quitan markdown, links, emojis y viñetas (no se pagan esos caracteres).
  - Caché en disco (`backend/.cache/tts`, volumen `tts-cache` en Docker): el mismo texto con el mismo modelo y la misma voz nunca se cobra dos veces, aunque se reinicie el servidor.
  - El resumen hablado de una factura dice solo proveedor, número, fecha, total e IVA.
  - Las grabaciones se cortan solas a los 3 minutos (Scribe cobra por minuto de audio).
- Las exportaciones CSV/MD se generan en el navegador: se neutralizan las fórmulas de planilla y se escapa la tabla Markdown.
- Si la cuenta de LlamaCloud fuera de la región EU: `LLAMA_CLOUD_BASE_URL=https://api.cloud.eu.llamaindex.ai`.
