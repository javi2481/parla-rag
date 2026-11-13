# Plan completo · Parla como demo de clase

**Fecha:** 13/11/2026 · **Estado:** fases 0 y 1 terminadas · **Detalle técnico de los hallazgos:** [informe-fase-1.md](informe-fase-1.md)

---

## 1. Objetivo

Armar una **demo detallada para mostrar en clase** cómo funciona un pipeline de documentos con IA, paso por paso.
Se sube un documento y se avanza con un **wizard**: en cada paso se hace clic, se espera a que termine (aparece un tilde verde) y se ve **todo** lo que produjo ese paso, guardado, medido y explicado.

Después se aplica la misma metodología al pipeline de **audio** (ElevenLabs).

## 2. Reglas del proyecto

1. **Solo lo nativo.** No se implementa nada que LlamaCloud, LlamaIndex o LlamaParse no hagan de forma nativa. Nada de código innecesario.
2. **Extraer todo en cada paso.** Cada paso pide a la plataforma toda la información que ofrece, la **guarda**, la **mide** y la **interpreta**.
3. **Código simple, no "senior".** Fácil de leer, con un comentario `#` (o `//` en TypeScript) en español rioplatense arriba de cada función. Toda la documentación va en español.
4. **Cada pipeline vive en su carpeta.** Su configuración, su cliente, sus pasos y sus rutas van juntos. En `core/` solo queda lo compartido.
5. **Sin base de datos.** Todo se guarda en carpetas dentro de `backend/data/`, simulando una DB.

---

## 3. El flujo del wizard de documentos

```
 1 Subir → 2 Parse → 3 Split → 4 Classify → 5 Schema → 6 Extract → 7 Index → 8 Chat
             │  pjb-...  ↑          ↑                       ↑
             └───────────┴──────────┴───────────────────────┘
          el documento se parsea UNA vez y los demás pasos usan ese resultado
```

**Cómo se usa:**
- Cada paso se arranca con un botón. Mientras corre muestra el **estado real** del job (PENDING, RUNNING, COMPLETED), sin barras simuladas. Cuando termina aparece el **tilde verde**.
- Para pasar a un paso hay que terminar el anterior. Los pasos completados quedan como pestañas para volver a verlos y se pueden **re-ejecutar**, por ejemplo para comparar el schema manual con el automático.
- Arriba hay una **lista de corridas anteriores**. Se abren sin volver a llamar a LlamaCloud, así que conviene llevar 3 o 4 corridas ya hechas por si falla el wifi en clase.
- Cada corrida muestra el **total de créditos gastados**.

**Qué tiene el panel de cada paso:**
1. **Qué hace este paso:** una explicación corta del concepto, pensada para la clase.
2. **Qué se le pidió:** las opciones que se mandaron a LlamaCloud (`request.json`).
3. **El resultado:** la vista amigable y el dato crudo (`.md`, `.json`), con botón de descarga.
4. **Las métricas:** números calculados solo con lo que devolvió la API (páginas, confianza, créditos, tiempo…).
5. **La interpretación:** frases armadas con esos datos, como "la página 2 tiene la confianza más baja: conviene revisarla". No se usa un LLM extra.

### Detalle de cada paso

| # | Paso | Producto de LlamaCloud | Qué se pide (lo máximo) | Qué se guarda | Qué se mide e interpreta |
|---|---|---|---|---|---|
| 1 | **Subir** | `files.create` | — | El archivo original y la respuesta | Tipo, tamaño, `file_id` |
| 2 | **Parse** | `parsing.create` / `get` | Tier y versión fijos, corrección de fotos de celular, tablas, imágenes, formularios, confianza, número de página impreso, marcas de agua. `expand` con todo: markdown, text, items, metadata, forms, images, job_metadata, usage | `document.md`, `text.txt`, `items.json`, `metadata.json`, `forms.json`, `images/` | Páginas, palabras, tablas, imágenes, confianza por página y del documento (con la peor página), rotación, marca de agua, créditos, tiempo |
| 3 | **Split** | `split.create` / `get` | Entrada: el parse (`pjb-...`). Categorías editables (factura, ticket, recibo, nota de crédito, otro) y estrategia de corte | `segments.json` | Cantidad de segmentos, páginas y categoría de cada uno |
| 4 | **Classify** | `classify.create` / `get` | Entrada: el parse. Reglas editables (tipo más descripción) | `result.json`, con type, confidence y **reasoning** | Confianza, créditos y el **razonamiento del modelo**, tal cual |
| 5 | **Schema** | `extract.generate_schema`, `validate_schema`, `configurations` | **Manual:** el editor de campos. **Automático:** el agente propone los campos a partir del documento (y de una indicación opcional). En los dos casos se valida y se guarda como configuración con nombre | `schema.json`, `validation.json`, `configuration.json` | Cantidad de campos y tipos, origen (manual o agente) y diferencias entre los dos |
| 6 | **Extract** | `extract.create` / `get` | Entrada: el parse. `configuration_id` del paso 5, `cite_sources`, `advanced_citations`, `confidence_scores` | `result.json` (tal cual), `metadata.json` (por documento, página y fila), `boxes.json` | Campos encontrados y vacíos, confianza promedio, mínima y máxima, campos a revisar, citas sobre el documento, créditos |
| 7 | **Index** | `beta.directories`, `indexes`, `retrieval` | Directorio, archivo, índice con `store_attachments: ["screenshots", "items"]`. Búsqueda **híbrida** con rerank | `index.json`, `chunks.json` y `queries/` (cada búsqueda de prueba) | Cantidad de chunks, tokens por chunk, score y rerank de cada resultado, páginas de donde salió |
| 8 | **Chat** | `chat.create`, `chat.stream` | Una sesión atada al índice | `session.json` y `turns/` (todos los eventos de cada turno) | La respuesta, el **razonamiento**, las **búsquedas que hizo el agente** y lo que encontró, tokens, duración |

### Schema manual o automático (paso 5)

Los dos modos terminan en **el mismo editor de campos**. Cada campo tiene nombre, tipo (texto, número, fecha, sí/no, lista), una guía (la `description` que lee LlamaExtract) y si es obligatorio.

- **Manual:** arrancás con el editor vacío o cargás una **plantilla**. Por ejemplo, "Factura AR" son los 10 campos que hoy están fijos en el código, pero con tipos de verdad: los importes como números.
- **Automático:** `generate_schema` analiza el documento y propone los campos. La propuesta cae en el editor, donde la podés corregir.
- **Siempre:** se valida con `validate_schema` y se guarda en **`configurations` de LlamaCloud** con un nombre. Así queda como plantilla reutilizable, sin una carpeta nuestra.

---

## 4. Dónde queda cada cosa

### Backend

```
backend/app/
├── core/
│   ├── settings.py · limits.py          (ya existen)
│   └── runs/                            el motor del wizard, lo reutilizan documentos y audio
│       ├── store.py                     la carpeta-DB: crear, leer, listar y borrar corridas
│       └── models.py                    Run y StepState (locked / pending / running / done / failed)
└── pipelines/documents/
    ├── README.md · settings.py · client.py · router.py
    ├── pipeline.py                      la lista ordenada de pasos (empezá a leer por acá)
    ├── schemas.py                       el editor de campos ↔ JSON Schema, y configurations
    └── steps/                           un archivo por paso; cada uno tiene:
        ├── s1_upload.py                   EXPLICACION (texto fijo para la clase)
        ├── s2_parse.py                    start()     arranca el job en LlamaCloud
        ├── s3_split.py                    check()     consulta el estado y, si terminó, guarda todo
        ├── s4_classify.py                 metrics()   calcula las métricas con lo guardado
        ├── s5_schema.py                   interpret() arma las frases de interpretación
        ├── s6_extract.py
        ├── s7_index.py
        └── s8_chat.py
```

### La carpeta-DB

```
backend/data/
├── samples/                             documentos de prueba (van al repo)
├── audio/cache/                         audios ya pagados
└── documents/runs/
    └── 2026-11-13_1530_factura-ejemplo/
        ├── run.json                     estado de cada paso, IDs de LlamaCloud, créditos, tiempos
        ├── 1_upload/    original.pdf · request.json · response.json
        ├── 2_parse/     request.json · response.json · document.md · text.txt · items.json
        │                metadata.json · forms.json · images/ · metrics.json
        ├── 3_split/     … · segments.json · metrics.json
        ├── 4_classify/  … · result.json · metrics.json
        ├── 5_schema/    schema.json · validation.json · configuration.json
        ├── 6_extract/   … · result.json · metadata.json · boxes.json · metrics.json
        ├── 7_index/     index.json · chunks.json · queries/
        └── 8_chat/      session.json · turns/
```

Cada paso guarda siempre `request.json` (qué se pidió) y `response.json` (la respuesta completa de LlamaCloud). Los demás archivos son partes de esa respuesta separadas, para verlas y descargarlas fácil.

### Rutas HTTP

| Ruta | Qué hace |
|---|---|
| `GET /api/documents/runs` | Lista las corridas |
| `POST /api/documents/runs` | Sube el archivo y crea la corrida (paso 1) |
| `GET /api/documents/runs/{id}` | El estado de todos los pasos |
| `POST /api/documents/runs/{id}/steps/{paso}` | Arranca un paso con sus opciones |
| `GET /api/documents/runs/{id}/steps/{paso}` | Consulta el paso: estado y, si terminó, resultado, métricas e interpretación |
| `GET /api/documents/runs/{id}/files/{ruta}` | Descarga un archivo guardado (el `.md`, el `.json`…) |
| `DELETE /api/documents/runs/{id}` | Borra la corrida: la carpeta y los recursos en LlamaCloud |
| `GET`/`POST /api/documents/schemas` | Lista y guarda plantillas (en `configurations`) |
| `POST /api/documents/schemas/generate` · `/validate` | Schema automático y validación |
| `POST /api/documents/runs/{id}/chat` | Un turno de chat. Reenvía en vivo los eventos de LlamaCloud y al final los guarda |

### Frontend

```
frontend/src/
├── components/wizard/                   lo reutilizan documentos y audio
│   ├── Stepper.tsx                      la barra de pasos con candado, spinner y tilde
│   ├── StepPanel.tsx                    explicación · pedido · resultado · métricas · interpretación
│   ├── JsonView.tsx · MarkdownView.tsx  visores de datos crudos
│   └── RunList.tsx                      las corridas anteriores
└── pipelines/documents/
    ├── DocumentsWizard.tsx              reemplaza a InvoiceExtractor.tsx
    ├── api.ts
    ├── SchemaEditor.tsx                 el editor de campos (manual y automático)
    └── steps/                           un panel por paso: UploadStep … ChatStep
```

---

## 5. Las fases

> **Cambio respecto de lo que hablamos:** propongo hacer el **wizard antes que el schema**. El schema es el paso 5 del wizard. Si lo hiciéramos primero sobre la pantalla actual, habría que reescribirlo después, y eso es código innecesario. Por eso las fases quedan reordenadas.

### ✅ Fase 0 · Reorganización (terminada, commit `41e0666`)
Cada pipeline quedó autocontenido en su carpeta, con un README por pipeline y un comentario en rioplatense arriba de cada función. No cambió el comportamiento: los 25 tests pasan.

### ✅ Fase 1 · Informe (terminado, commit `ea47134`)
El relevamiento completo de la API de LlamaCloud y 16 hallazgos sobre el código actual. Ver [informe-fase-1.md](informe-fase-1.md).

### Fase 2 · Verificación con llamadas reales y motor de corridas
**Primero se verifica.** Antes de escribir los pasos se prueban a mano, con la factura de ejemplo, las cuatro dudas del informe:
1. si el índice nuevo deja listar todos los chunks;
2. qué valores acepta `images_to_save` y si las capturas sirven para dibujar las cajas;
3. si Split devuelve `usage`;
4. cuántos créditos cuesta una corrida completa.

*Esto gasta algunos créditos reales. Te aviso antes de cada llamada.*

**Después se construye:**
- `core/runs/` con la carpeta-DB y el estado de los pasos.
- El wizard base en el frontend: el stepper, el panel de paso, los visores y la lista de corridas.
- Los pasos **1 Subir** y **2 Parse** completos, con todo lo que ofrece Parse.

**Se elimina:** `jobs.py`, la barra de progreso simulada y el cleanup automático.
**Hallazgos que resuelve:** #5, #7, #8, #9, #10 y #12.
**Listo cuando:** se sube la factura de ejemplo, se corre Parse, aparece el tilde y se ven el `.md`, las páginas, la confianza, los créditos y la interpretación. Además, la corrida sobrevive a reiniciar el servidor.

### Fase 3 · Split, Classify, Schema y Extract
- Los pasos **3 Split** y **4 Classify**, encadenados al parse (`pjb-...`), con categorías y reglas editables.
- El paso **5 Schema**, manual o automático: el editor, `generate_schema`, `validate_schema` y las plantillas en `configurations`. Se crea la plantilla "Factura AR".
- El paso **6 Extract** con la configuración guardada, las citas avanzadas y toda la metadata. Las cajas se dibujan sobre el documento.

**Se elimina:** `schema.py` (los campos fijos), `clean_amount`, `EMPTY_WORDS`, `normalize_result`, `invoiceCsv` e `invoiceMarkdown`, junto con sus tests. Si en la fase 2 las capturas de página alcanzan, también `PdfPreview` y `pdfjs`.
**Hallazgos que resuelve:** #1, #2, #3, #4, #6, #13, #14 y #16.
**Listo cuando:** la misma factura se extrae una vez con el schema manual y otra con el automático, y se pueden comparar las dos corridas.

### Fase 4 · Index y Chat
- El paso **7 Index**: directorio, índice con capturas e items, y una caja de **búsqueda de prueba** que muestra los chunks recuperados con su score.
- El paso **8 Chat**: el chat en vivo con el documento, mostrando el razonamiento y las búsquedas del agente. Cada turno queda guardado.

**Listo cuando:** se le pregunta "¿cuál es el total y de qué fecha es?" y se ve la respuesta junto con los chunks que usó el agente para responder.

### Fase 5 · Audio con la misma metodología
- **Primero un relevamiento** de la API de ElevenLabs, igual que hicimos con LlamaCloud, aplicando la misma regla de usar solo lo nativo. Hoy hay código nuestro que probablemente sobre: la limpieza de texto `to_speech` y la de transcripción `clean_transcript`. ElevenLabs puede tener normalización de texto y opciones de Scribe que lo reemplacen; eso se confirma en el relevamiento.
- **Después**, el wizard de audio reutilizando `core/runs/` y `components/wizard/`:
  - **TTS:** texto → voz (manual: elegís la voz y los ajustes; automático: a definir según lo que ofrezca ElevenLabs) → síntesis → resultado y métricas.
  - **STT:** audio → transcripción (con tiempos, hablantes y todo lo que dé Scribe) → resultado y métricas.

**Listo cuando:** los dos flujos de audio se ven y se usan igual que el de documentos.

### Fase 6 · Cierre para la clase
- Revisar todos los README y comentarios.
- Dejar 3 o 4 corridas de ejemplo listas en `data/`.
- Escribir un guion corto para la demo: qué mostrar en cada paso y qué preguntar al chat.
- Correr todo con Docker, de punta a punta.

---

## 6. Roadmap (después de la clase)

- **Pasar la carpeta-DB a `agent_data`.** Es la base JSON nativa de LlamaCloud, con búsqueda, filtros y agregaciones. Hoy elegimos la carpeta para que la demo funcione sin conexión y los archivos se puedan abrir a mano.
- **Verify** (`alpha.verify`): detectar si un documento fue adulterado. Lo sumamos cuando salga de alpha.
- **Webhooks:** que LlamaCloud avise cuando termina un job, en lugar de consultar. Solo sirve con el servidor publicado en internet.
- **Batches:** procesar muchos documentos de una vez.

## 7. Lo que necesito de vos

1. **¿Estás de acuerdo con el nuevo orden de las fases** (el wizard antes que el schema)?
2. **Las llamadas de verificación de la fase 2 gastan créditos reales.** ¿Me das el OK para hacerlas con la factura de ejemplo?
3. **¿Tenés otros documentos de prueba** (un ticket, una foto sacada con el celular, un PDF con varias facturas)? Para mostrar Split y Classify sirve tener un PDF que traiga más de un documento adentro.
