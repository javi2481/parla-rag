# Parla RAG

**Documentos que se leen solos, y una conversación con todos a la vez.**

Una demo para clase, pensada para quedar como **plantilla**. Muestra paso por paso cómo funciona un pipeline de documentos con IA y un RAG (búsqueda y chat sobre varios documentos):

| | Qué hace | Con qué |
| --- | --- | --- |
| 📄 **Documentos** | Subís un documento y lo recorrés en un **wizard**: `Subir → Parse → Split → Classify → Schema → Extract`. En cada paso ves todo lo que devolvió la plataforma, cuánto costó y qué significa. Las **cajas de color** muestran sobre la página de dónde salió cada dato. | LlamaCloud (LlamaParse) |
| 📚 **Bibliotecas** | Juntás documentos relacionados en un **índice compartido**, probás la **búsqueda** y **chateás** con todos a la vez. Cada respuesta cita documento y página, y se ve qué se buscó. | LlamaIndex · Voyage AI · DeepSeek |

> Parla empezó como un solo proyecto con documentos y audio. El 15/11/2026 se separó: el audio (ElevenLabs) sigue en **parla-audio**.

## Estado

| Fase | Estado |
|---|---|
| 0 · Reorganización · 1 · Informe de la API | ✅ |
| 2 · Motor de corridas, Subir y Parse | ✅ probado con LlamaCloud real |
| 3 · Split, Classify, Schema y Extract | ✅ probado en los EEFF y el comunicado de BYMA |
| 4 · Bibliotecas: índice, búsqueda y chat | 🟡 funciona y el chat está probado; falta sincronizar "BYMA 3T26" (hay que cargar un medio de pago en Voyage) |
| 6 · Cierre para la clase | ⏳ |

**Todo el detalle (lo hecho, lo pendiente en orden y el roadmap): [docs/estado.md](docs/estado.md).**

## La documentación

| Archivo | Qué tiene |
|---|---|
| [docs/estado.md](docs/estado.md) | **Empezá por acá.** Hecho, pendiente, roadmap, datos locales y claves |
| [docs/plan.md](docs/plan.md) | El diseño completo: el wizard, las bibliotecas, la carpeta-DB, las rutas y las fases |
| [docs/bitacora.md](docs/bitacora.md) | Cada prueba, hallazgo y decisión, y el **registro de créditos** de cada llamada paga |
| [docs/informe-fase-1.md](docs/informe-fase-1.md) | El relevamiento de la API de LlamaCloud |
| [docs/verificacion-1-parse.md](docs/verificacion-1-parse.md) · [docs/verificacion-2-fase3.md](docs/verificacion-2-fase3.md) | Las verificaciones con llamadas reales |
| [backend/app/pipelines/documents/README.md](backend/app/pipelines/documents/README.md) | Cómo está hecho el pipeline por dentro: los pasos, los archivos y las bibliotecas |
| [CLAUDE.md](CLAUDE.md) | Las reglas del proyecto (también las lee Claude Code) |

## Las reglas del proyecto

1. **Solo lo nativo.** No se implementa nada que LlamaCloud, LlamaIndex o LlamaParse no hagan de forma nativa. Nada de código innecesario.
2. **Traer todo en cada paso:** pedir toda la información que ofrece la plataforma, **guardarla**, **medirla** e **interpretarla** solo con datos de la API.
3. **El parse es el corazón:** se parsea **una vez**, completo, y los demás pasos usan ese parse.
4. **Código simple**, con un comentario en español rioplatense arriba de cada función.
5. **Sin base de datos:** todo se guarda en carpetas dentro de `backend/data/`.
6. **Registrar todo para auditar:** la bitácora y el registro de créditos.

## Cómo funciona

### El wizard

```
 1 Subir → 2 Parse → 3 Split → 4 Classify → 5 Schema → 6 Extract
             │  pjb-...  ↑          ↑                       ↑
             └───────────┴──────────┴───────────────────────┘
          el documento se parsea UNA vez y los demás pasos usan ese resultado
```

Cada paso muestra: qué hace (para la clase), qué se le pidió a LlamaCloud, el resultado (con descarga), las métricas y la interpretación. Repetir un paso no borra nada: lo anterior pasa al historial.

### Las bibliotecas

```
Biblioteca "BYMA 3T26"
 ├── EEFF · Comunicado · Presentación     corridas del wizard: se usa su parse, no se vuelve a parsear
 │      ↓ una página = un documento de LlamaIndex, con su metadata de identidad
 ├── índice       embeddings voyage-4, guardado en la carpeta de la biblioteca
 ├── búsqueda     voyage-4 trae candidatos → rerank-2.5 los ordena
 └── chat         DeepSeek responde solo con esas páginas, citando documento y página
```

El índice de LlamaCloud (v2) necesita un plan pago, así que hoy se usa el **motor local** con el framework LlamaIndex. El motor de LlamaCloud también está escrito (`LIBRARY_ENGINE=llamacloud`) para cuando haya plan.

## Los documentos de ejemplo

En `backend/data/samples/byma/`: documentos públicos de BYMA (Bolsas y Mercados Argentinos) sobre el 3er trimestre de 2026.

| Archivo | Qué es | Qué muestra |
|---|---|---|
| `BYMA - EEFF 30-09-2026 - VF.pdf` | Estados financieros, 86 páginas | Split de secciones, tablas largas, Extract sobre una sola sección |
| `BYMA Comunicado de Prensa - 3T26.pdf` | Comunicado, 10 páginas | Schema manual contra automático |
| `Presentacion_de_Resultados-3T26.pdf` | Diapositivas, 15 páginas | Parse de gráficos con IA |

Y `backend/data/samples/factura_ejemplo.pdf`, una factura de una página.

## Estructura

```
backend/
├── app/
│   ├── main.py                     arma la app y conecta las rutas (nada más)
│   ├── core/                       lo compartido: configuración, límites por IP y runs/ (la carpeta-DB)
│   └── pipelines/documents/        ── todo el pipeline                    → ver su README.md
│       ├── settings.py             claves, tier y versión de Parse, motor y modelos de las bibliotecas
│       ├── client.py               cliente de LlamaCloud
│       ├── pipeline.py             el orden de los pasos (empezá a leer por acá)
│       ├── router.py               /api/documents/runs/...
│       ├── steps/                  s1_upload · s2_parse · s3_split · s4_classify · s5_schema · s6_extract · jobs
│       ├── library_router.py       /api/documents/libraries/...
│       ├── local_library.py        bibliotecas con LlamaIndex + Voyage AI + DeepSeek (el motor que se usa)
│       └── library.py              bibliotecas con el índice de LlamaCloud (necesita plan pago)
├── data/                           la "base de datos" en carpetas
│   ├── samples/                    documentos de ejemplo (sí van al repo)
│   ├── documents/runs/             las corridas del wizard (no van al repo)
│   ├── documents/libraries/        las bibliotecas, con su índice y sus chats (no van al repo)
│   └── nltk/                       datos que usa LlamaIndex para cortar oraciones (se bajan solos)
└── tests/                          misma forma que app/

frontend/src/
├── App.tsx                         las pestañas Documentos y Bibliotecas
├── components/                     Brand, Dropzone, ui/ (shadcn) y wizard/ (stepper, panel de paso, visores, cajas)
├── lib/                            llamadas al backend
└── pipelines/documents/            DocumentsWizard, steps/ (un panel por paso) y libraries/ (bibliotecas, búsqueda, chat)
```

## Configuración

```bash
cd backend
cp .env.example .env      # completar LLAMA_CLOUD_API_KEY, VOYAGE_API_KEY y DEEPSEEK_API_KEY
uv sync
```

| Clave | Para qué |
|---|---|
| `LLAMA_CLOUD_API_KEY` | El wizard ([cloud.llamaindex.ai](https://cloud.llamaindex.ai)) |
| `VOYAGE_API_KEY` | Embeddings y reranker de las bibliotecas ([dashboard.voyageai.com](https://dashboard.voyageai.com)). **Cargá un medio de pago**: sin tarjeta permite solo 3 pedidos y 10.000 tokens por minuto. Los 200 millones de tokens gratis se mantienen |
| `DEEPSEEK_API_KEY` | El chat de las bibliotecas ([platform.deepseek.com](https://platform.deepseek.com)) |

Si la cuenta de LlamaCloud es de la región EU: `LLAMA_CLOUD_BASE_URL=https://api.cloud.eu.llamaindex.ai`.

## Desarrollo

```bash
# terminal 1
cd backend && uv run uvicorn app.main:app --reload --port 8000
# terminal 2 (el proxy de Vite manda /api al backend)
cd frontend && npm install && npm run dev      # http://localhost:5173
```

## Docker

Un solo contenedor: compila el frontend y lo sirve FastAPI junto con la API.

```bash
docker compose up --build -d     # http://localhost:8000
docker compose logs -f
docker compose down
```

Las claves se leen de `backend/.env` al arrancar y nunca entran en la imagen. Los datos quedan en el volumen `parla-rag-data`.

## Producción (un solo proceso)

```bash
cd frontend && npm run build                   # genera frontend/dist
cd ../backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Tests

```bash
cd backend && uv run pytest        # 17 tests, con clientes falsos: sin red ni créditos
```

## Costos (medidos)

| Qué | Costo |
|---|---|
| Parse agentic con todas las opciones | 15 créditos por página (más en páginas con muchos gráficos: 21 a 39) |
| Split | no lo informa; la lista de precios dice 3 por página |
| Classify sobre un parse ya hecho | 0 |
| Extract agentic con citas y confianza | 15 créditos por página |
| Índice de la biblioteca (local) | 0 créditos de LlamaCloud; tokens de Voyage (gratis hasta 200 millones) |
| Una pregunta al chat (local) | 0 créditos de LlamaCloud; unos USD 0,003 de DeepSeek |

**Stack:** Python · FastAPI · LlamaCloud SDK · LlamaIndex · Voyage AI · DeepSeek · React · Vite · Tailwind · Docker
