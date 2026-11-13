# Parla

**Documentos que hablan, voces que escriben.**

Parla junta en una sola app tres tareas que suelen pedir tres herramientas distintas: leer documentos, convertir texto en voz y pasar audios a texto. Todo con IA, en español y con el gasto en créditos bajo control.

| | Qué hace | Con qué |
| --- | --- | --- |
| 📄 **Documentos** | Subís un documento y lo recorrés en un **wizard paso por paso**: en cada paso ves todo lo que devolvió LlamaCloud, cuánto costó y qué significa. Hoy: Subir y Parse (Markdown, tablas en Excel, gráficos convertidos en datos, confianza por página). | LlamaCloud · LlamaParse |
| 🔊 **Texto a voz** | Pegás un texto y lo escuchás con tu **voz clonada**. Cada audio muestra lo que costó, y lo repetido sale de la caché sin volver a cobrarse. | ElevenLabs Flash v2.5 |
| 🎙️ **Voz a texto** | Grabás o subís un audio y obtenés la transcripción **sin muletillas, tartamudeos ni repeticiones**, lista para copiar. | ElevenLabs Scribe |

### Por qué está bueno

- **Se ve de dónde sale cada dato**: las cajas de color unen cada campo extraído con su lugar en la factura.
- **Gasta lo justo**: usa el modelo de voz que cuesta la mitad por carácter, quita lo que no hace falta leer y guarda en disco todo lo ya generado.
- **Pipeline prolijo**: un archivo por paso y cada corrida guardada en una carpeta, con lo que se pidió y lo que respondió LlamaCloud.
- **Privado**: las API keys viven solo en el servidor. Al borrar una corrida se borra también en LlamaCloud.
- **Un comando**: `docker compose up` y queda andando en `localhost:8000`.

**Stack:** Python · FastAPI · LlamaCloud SDK · ElevenLabs · React · Vite · Tailwind · Docker

## Estructura

Cada pipeline vive entero en su carpeta: configuración, cliente del proveedor, pasos y rutas HTTP.
Para entender uno, leé su `README.md` y después su `pipeline.py`.

```
backend/
├── app/
│   ├── main.py                 arma la app y conecta los pipelines (nada más)
│   ├── core/                   lo compartido: configuración, límites por IP y runs/ (la carpeta-DB del wizard)
│   └── pipelines/
│       ├── documents/          ── DOCUMENTOS (LlamaCloud)          → ver su README.md
│       │   ├── settings.py     API key, tier y versión de Parse, máximos
│       │   ├── client.py       cliente de LlamaCloud
│       │   ├── pipeline.py     el orden de los pasos del wizard
│       │   ├── router.py       /api/documents/runs/...
│       │   └── steps/          s1_upload · s2_parse (siguen Split, Classify, Schema, Extract…)
│       └── audio/              ── AUDIO (ElevenLabs)               → ver su README.md
│           ├── settings.py     API key, voz, modelos, caché, límites
│           ├── client.py       URL y errores de ElevenLabs
│           ├── tts.py          texto → voz (con caché)
│           ├── stt.py          voz → texto (Scribe + limpieza)
│           ├── cache.py · clean_transcript.py
│           └── router.py       /api/audio/...
├── data/                       la "base de datos" en carpetas
│   ├── samples/                documentos de prueba, incluidos los de BYMA (sí van al repo)
│   ├── documents/runs/         las corridas del wizard (no van al repo)
│   └── audio/cache/            audios ya pagados (no van al repo)
└── tests/                      misma forma que app/: pipelines/documents · pipelines/audio

frontend/src/
├── App.tsx                     pestañas
├── components/                 Brand, Dropzone, ui/ (shadcn) y wizard/ (stepper, panel de paso, visores)
├── lib/                        llamadas al backend
└── pipelines/                  misma forma que el backend
    ├── documents/              DocumentsWizard, api.ts y steps/ (un panel por paso)
    └── audio/                  TextToSpeech, SpeechToText, AudioPlayer, ListenButton, api.ts
```

### Pipeline de documentos

Un wizard: `Subir → Parse → …`, con cada paso guardado, medido e interpretado. El plan completo está en
[docs/plan.md](docs/plan.md) y el detalle de cada paso en
[backend/app/pipelines/documents/README.md](backend/app/pipelines/documents/README.md).

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

- Herramienta interna: sin captcha ni Supabase. Los límites son en memoria y por IP (`DOCUMENTS_DAILY_LIMIT`, `AUDIO_LIMIT_PER_10_MIN`) y se reinician con el servidor.
- **Ahorro de créditos en ElevenLabs:**
  - Modelo por defecto `eleven_flash_v2_5`: la mitad de créditos por carácter que `eleven_v4` (medido: 11 contra 23 créditos para la misma frase). Para máxima calidad: `ELEVENLABS_TTS_MODEL=eleven_v4`.
  - Antes de enviar se quitan markdown, links, emojis y viñetas (no se pagan esos caracteres).
  - Caché en disco (`backend/data/audio/cache`, volumen `parla-data` en Docker): el mismo texto con el mismo modelo y la misma voz nunca se cobra dos veces, aunque se reinicie el servidor.
  - Las grabaciones se cortan solas a los 3 minutos (Scribe cobra por minuto de audio).
- Si la cuenta de LlamaCloud fuera de la región EU: `LLAMA_CLOUD_BASE_URL=https://api.cloud.eu.llamaindex.ai`.
