# Plan completo · Parla RAG como demo de clase

**Escrito:** 13/11/2026 · **Actualizado:** 21/11/2026 (el chat como página principal) · **Estado de cada fase:** [estado.md](estado.md) · **Detalle técnico de la API:** [informe-fase-1.md](informe-fase-1.md)

> El 15/11/2026 Parla se separó en dos proyectos. Este plan es el de **documentos y bibliotecas**. La fase 5 (audio con ElevenLabs) sigue en **parla-audio**.

---

## 1. Objetivo

Armar una **demo detallada para mostrar en clase** cómo funciona un pipeline de documentos con IA, paso por paso.
Se sube un documento y se avanza con un **wizard**: en cada paso se hace clic, se espera a que termine (aparece un tilde verde) y se ve **todo** lo que produjo ese paso, guardado, medido y explicado.

Los documentos que se relacionan entre sí se juntan en una **biblioteca**: comparten un índice y se puede **chatear con todos a la vez**.

La misma metodología se aplica al **audio** (ElevenLabs) en el proyecto **parla-audio**. Sumar su transcripción a una biblioteca queda pendiente: ver [estado.md](estado.md#integración-con-parla-audio).

## 2. Reglas del proyecto

1. **Solo lo nativo.** No se implementa nada que LlamaCloud, LlamaIndex o LlamaParse no hagan de forma nativa. Nada de código innecesario. El framework LlamaIndex y sus integraciones oficiales (Voyage AI, OpenAI) cuentan como nativos.
2. **Extraer todo en cada paso.** Cada paso pide a la plataforma toda la información que ofrece, la **guarda**, la **mide** y la **interpreta**.
3. **Código simple, no "senior".** Fácil de leer, con un comentario `#` (o `//` en TypeScript) en español rioplatense arriba de cada función. Toda la documentación va en español.
4. **Cada pipeline vive en su carpeta.** Su configuración, su cliente, sus pasos y sus rutas van juntos. En `core/` solo queda lo compartido.
5. **Sin base de datos.** Todo se guarda en carpetas dentro de `backend/data/`, simulando una DB.

## 3. Los documentos de la demo

Están en `backend/data/samples/aprendizaje-automatico-ii/`: el material teórico de la materia **Aprendizaje Automático II**, una carpeta por clase. Las 13 clases cuentan una historia de punta a punta (redes neuronales → PLN → visión por computadora → multimodales → sesgo), así que sirven para una **biblioteca** y para un chat que cruce clases.

| Qué | Cantidad | Qué muestra en clase |
|---|---|---|
| **PDF de las diapositivas** | 14 (la presentación de la materia y las 13 clases), **410 páginas** | **Parse con gráficos, tablas, código y fórmulas**: diapositivas con poco texto y mucha imagen, donde más se nota el parse con IA |
| **Notebooks** (`.ipynb`) | 32 | No se parsean: LlamaParse no acepta `.ipynb` ([lista oficial](https://developers.llamaindex.ai/llamaparse/general/supported_document_types/)) y la teoría está en los PDF. Si hicieran falta, el lector nativo `IPYNBReader` de LlamaIndex las carga sin LlamaCloud |


## 4. Créditos

Los créditos son de la cuenta de **LlamaCloud**, la plataforma de la empresa LlamaIndex. **LlamaParse** es el nombre de sus productos de documentos (Parse, Extract, Split, Classify…). No son dos saldos distintos: todos los productos descuentan del mismo saldo.

- **Cuánto cuesta cada cosa:** depende del producto, del tier y de la cantidad de páginas. Cada job devuelve lo que cobró (`usage`), así que no hace falta adivinar. Antes de un lote grande se parsea un documento chico para medir el costo real por página.
- **Lo medido con este corpus:** Parse agentic con todas las opciones, **17,7 créditos por página** en promedio (entre 15 y 25). Las 410 páginas costaron **7.250 créditos**. El detalle está en el registro de créditos de la [bitácora](bitacora.md).
- **Cómo se ahorra**, sin código nuestro:
  - Cada documento se **parsea una sola vez**. Split, Classify, Extract y las bibliotecas usan ese parse (`pjb-...`) y no vuelven a leer el documento.
  - **Split** ubica las secciones y **Extract corre solo sobre las páginas que interesan** (`target_pages`).
  - Se elige el **tier** según el documento: uno económico para el texto corrido y `agentic` para las diapositivas con gráficos.
- Cada corrida y cada biblioteca muestran el **total gastado**.

---

## 5. El wizard de un documento

```
 1 Subir → 2 Parse → 3 Split → 4 Classify → 5 Schema → 6 Extract → 7 Biblioteca
             │  pjb-...  ↑          ↑                       ↑          (sumar al índice)
             └───────────┴──────────┴───────────────────────┘
          el documento se parsea UNA vez y los demás pasos usan ese resultado
```

**Cómo se usa:**
- Cada paso se arranca con un botón. Mientras corre muestra el **estado real** del job (PENDING, RUNNING, COMPLETED), sin barras simuladas. Cuando termina aparece el **tilde verde**.
- Para pasar a un paso hay que terminar el anterior. Los pasos completados quedan como pestañas para volver a verlos y se pueden **re-ejecutar**, por ejemplo para comparar el schema manual con el automático.
- Hay una **lista de corridas anteriores**. Se abren sin volver a llamar a LlamaCloud, así que conviene llevar las corridas ya hechas por si falla el wifi en clase.

**Qué tiene el panel de cada paso:**
1. **Qué hace este paso:** una explicación corta del concepto, pensada para la clase.
2. **Qué se le pidió:** las opciones que se mandaron a LlamaCloud (`request.json`).
3. **El resultado:** la vista amigable y el dato crudo (`.md`, `.json`), con botón de descarga.
4. **Las métricas:** números calculados solo con lo que devolvió la API (páginas, confianza, créditos, tiempo…).
5. **La interpretación:** frases armadas con esos datos, como "la página 6 tiene la confianza más baja: conviene revisarla". No se usa un LLM extra.

### Detalle de cada paso

| # | Paso | Producto de LlamaCloud | Qué se pide (lo máximo) | Qué se guarda | Qué se mide e interpreta |
|---|---|---|---|---|---|
| 1 | **Subir** | `files.create` | — | El archivo original y la respuesta | Tipo, tamaño, páginas, `file_id` |
| 2 | **Parse** | `parsing.create` / `get` | Tier y versión fijos, **sin límite de páginas** (Split rechaza los parses limitados), corrección de fotos de celular, tablas (incluso las que siguen en otra página), gráficos, imágenes, formularios, confianza, número de página impreso, marcas de agua. `expand` con todo y las 3 salidas extra (`stripped_md`, `concatenated_stripped_txt`, `word_bbox`) | `document.md`, `text.txt`, `items.json`, `metadata.json`, `forms.json`, `images/` | Páginas, palabras, tablas, imágenes, gráficos, confianza por página y del documento (con la peor página), rotación, marca de agua, créditos, tiempo |
| 3 | **Split** | `split.create` / `get` | Entrada: el parse (`pjb-...`). Categorías editables (por ejemplo, para una clase: teoría, ejemplos, código, bibliografía) y estrategia de corte | `segments.json` | Cantidad de segmentos, rango de páginas y categoría de cada uno |
| 4 | **Classify** | `classify.create` / `get` | Entrada: el parse. Reglas editables (tipo más descripción) | `result.json`, con type, confidence y **reasoning** | Confianza, créditos y el **razonamiento del modelo**, tal cual |
| 5 | **Schema** | `extract.generate_schema`, `validate_schema`, `configurations` | **Manual:** el editor de campos. **Automático:** el agente propone los campos a partir del documento (y de una indicación opcional). En los dos casos se valida y se guarda como configuración con nombre | `schema.json`, `validation.json`, `configuration.json` | Cantidad de campos y tipos, origen (manual o agente) y diferencias entre los dos |
| 6 | **Extract** | `extract.create` / `get` | Entrada: el parse. `configuration_id` del paso 5, **páginas elegidas a partir de un segmento del Split**, `cite_sources`, `advanced_citations`, `confidence_scores` | `result.json` (tal cual), `metadata.json`, `fields.json` (cada campo con valor, confianza y citas), `boxes.json` | Campos encontrados y vacíos, confianza promedio, mínima y máxima, campos a revisar, citas sobre el documento, créditos |
| 7 | **Biblioteca** | motor local: el parse del paso 2 · LlamaCloud: `beta.directories.files.add`, `indexes.sync` | Elegir una biblioteca (o crear una) y sumar el documento a su índice | La copia del Markdown por página en la biblioteca | — (el detalle se ve en la biblioteca) |

### Schema manual o automático (paso 5)

Los dos modos terminan en **el mismo editor de campos**. Cada campo tiene nombre, tipo (texto, número, fecha, sí/no, lista), una guía (la `description` que lee LlamaExtract) y si es obligatorio.

- **Manual:** arrancás con el editor vacío o cargás una **plantilla** ("Factura AR" o "Resultados trimestrales").
- **Automático:** `generate_schema` analiza el documento y propone los campos. La propuesta cae en el editor, donde la podés corregir.
- **Siempre:** se valida con `validate_schema` y se guarda en **`configurations` de LlamaCloud** con un nombre. Así queda como plantilla reutilizable, sin una carpeta nuestra.

---

## 6. Bibliotecas: un índice compartido y el chat

Una **biblioteca** junta documentos que se relacionan entre sí. Por ejemplo, "Aprendizaje Automático II" con las 14 clases. Hay **dos motores** con las mismas funciones y las mismas respuestas, así la pantalla es una sola. Cada biblioteca recuerda con qué motor se creó; las nuevas usan `LIBRARY_ENGINE`.

### Motor local (el que se usa): LlamaIndex + Voyage AI + OpenAI

El índice de LlamaCloud necesita un plan pago (con el plan gratis responde 403), así que la biblioteca se arma en nuestro servidor con el **framework LlamaIndex** y dos integraciones oficiales:

```
Biblioteca "Aprendizaje Automático II"
 ├── Clase 01 · Clase 02 · … · Clase 13   corridas del wizard: se usa su parse, NO se vuelve a parsear
 │      ↓ una página = un Document de LlamaIndex, con su número y la metadata de identidad
 ├── index/        VectorStoreIndex con embeddings voyage-4, guardado en la carpeta
 ├── búsqueda      voyage-4 trae 3 candidatos por resultado → rerank-2.5 los ordena
 └── chat          CondensePlusContextChatEngine: reescribe la pregunta (si hay historial),
                   busca como arriba y gpt-5-nano responde citando documento y página
```

- **Agregar** una corrida copia a la biblioteca el Markdown de cada página de su parse, con la metadata: el tipo de Classify y los campos **obligatorios** del schema de Extract (los de identidad). Así queda auditable qué texto se indexó.
- **Sacar** un documento lo deja afuera en la próxima sincronización; su copia queda para auditar.
- **Sincronizar** vuelve a armar el índice entero y guarda el anterior en el historial. Es local y responde en el momento (las 410 páginas tardan 6 s).
- **Buscar** acepta filtros por metadata (solo igualdad) y guarda cada búsqueda con sus resultados. El chat, la búsqueda de prueba y los evals usan la misma búsqueda (`make_retriever`): `default` por defecto, MMR nativo opcional (se midió y no mejoró la cobertura de clases).
- **Conversaciones:** cada una es una carpeta `chats/local/<conversación>/` con sus turnos; cerrarla solo la oculta. El chat recibe `conversation_id` y filtros por `tipo` (unidad) y `nombre` (clase).
- **Chatear:** las instrucciones piden responder solo con los fragmentos, decir que el dato no está cuando no está, citar *(documento, pág. N)* y copiar los números tal cual. Los eventos son los mismos que los del chat de LlamaCloud (`tool_call`, `tool_result`, `text_delta`, `stop`).
- **El modelo:** `gpt-5-nano`, el más barato de OpenAI, con `reasoning_effort=minimal` para que razone poco (el razonamiento se cobra como tokens de salida).
- **Qué se mide:** páginas indexadas y chunks; de cada búsqueda, el score vectorial y el del reranker; de cada turno, la consulta real, las páginas que leyó el modelo, el prompt completo, los tokens y el costo estimado en dólares (con la instrumentación nativa de LlamaIndex y la lista de precios de `settings.py`).

### Motor de LlamaCloud (escrito, bloqueado por el plan)

En LlamaCloud una biblioteca es **un directorio con su índice**; todo es nativo:

```
Biblioteca "Aprendizaje Automático II"
 ├── 01 Introducción a Redes Neuronales.pdf   ┐
 ├── 02 Perceptrón Multicapa y Deep Learning.pdf ├── directorio ──→ índice ──→ búsqueda ──→ chat
 └── …                                         ┘  (files.add)     (sync)    (retrieve)   (stream)
```

- **Crear** una biblioteca y **agregar o sacar** documentos (con el mismo `file_id` de la corrida; `unique_id` es la corrida). Después `indexes.sync` actualiza el índice. El índice parsea con **nuestra** configuración completa (`product_config_id`).
- **Procesar en lote** (`batches`): correr el mismo trabajo sobre **todos los documentos de la biblioteca a la vez**. Pendiente: necesita el mismo plan.
- **Buscar:** `retrieval.retrieve`, búsqueda híbrida con rerank y `custom_filters`.
- **Chatear:** `chat.create` y `chat.stream`, con el razonamiento del agente y las búsquedas que hizo.
- **Precios publicados:** 2 créditos por página indexada, 1 por búsqueda y 100 por turno de chat.

## 7. Dónde queda cada cosa

### Backend

```
backend/app/
├── main.py                              arma la app y conecta las rutas
├── core/
│   ├── settings.py · limits.py          configuración general y límites por IP
│   └── runs/store.py                    la carpeta-DB: crear, leer, listar, archivar y borrar corridas y bibliotecas
└── pipelines/documents/
    ├── README.md · settings.py · errors.py
    ├── llamacloud_client.py             crea el cliente de LlamaCloud
    ├── route_dependencies.py            lo que comparten las rutas (cliente, carpeta-DB, errores de LlamaCloud)
    ├── number_format.py                 números con formato argentino para las métricas
    ├── wizard/                          los 6 pasos sobre UN documento
    │   ├── wizard_flow.py                 la lista ordenada de pasos (empezá a leer por acá)
    │   ├── wizard_routes.py               /api/documents/runs/...
    │   └── steps/                         un archivo por paso; cada uno tiene:
    │       ├── step1_upload.py              EXPLICACION  el texto para la clase
    │       ├── step2_parse.py               start()      arranca el job en LlamaCloud
    │       ├── step3_split.py               check()      consulta el estado y, si terminó, guarda todo
    │       ├── step4_classify.py            summarize()  métricas e interpretación con lo guardado
    │       ├── step5_schema.py              DEFAULTS     las opciones con las que arranca el editor
    │       ├── step6_extract.py
    │       └── llamacloud_jobs.py           lo común a los pasos con job
    └── libraries/                       el RAG: varios documentos, búsqueda y chat
        ├── library_routes.py              /api/documents/libraries/... (elige el motor de cada biblioteca)
        ├── document_metadata.py           metadata de identidad y resumen de búsqueda (los dos motores)
        ├── llamacloud_engine.py           motor de LlamaCloud: directorio, índice, búsqueda y chat
        └── local/                         motor local: LlamaIndex + Voyage AI + OpenAI
            ├── local_engine.py              la puerta de entrada que usa la ruta
            ├── ai_models.py                 embeddings, reranker, modelo de lenguaje y NLTK
            ├── index_builder.py             páginas → chunks → índice
            ├── retrieval.py                 vectores / MMR / híbrida (BM25) + reranker + filtros
            ├── chat_engine.py               prompts, chat de contexto, agente y turno del chat
            ├── turn_recorder.py             qué buscó, llamadas al modelo, tokens y costo
            ├── conversations.py             las pestañas del chat
            └── rag_evals.py                 evals de búsqueda y respuestas (nativos de LlamaIndex)
```

### La carpeta-DB

```
backend/data/
├── samples/                             documentos de prueba (solo el set de evals va al repo)
│   └── aprendizaje-automatico-ii/       una carpeta por clase (PDF y notebooks) y evals/preguntas.json
├── nltk/                                datos de NLTK para LlamaIndex (se bajan solos, con permisos privados)
├── verificacion/                        datos crudos de las verificaciones
└── documents/
    ├── runs/
    │   └── 2026-11-21_130904_02-perceptron-multicapa-y-deep-learning/
    │       ├── run.json                 estado de cada paso, IDs de LlamaCloud, créditos, tiempos e historial
    │       ├── 1_upload/    original.pdf · request.json · response.json · metrics.json
    │       ├── 2_parse/     request.json · configuration.json · response.json · document.md · text.txt
    │       │                items.json · metadata.json · forms.json · tables.xlsx · images/ · archivos/ · metrics.json
    │       ├── 3_split/     request.json · configuration.json · response.json · segments.json · metrics.json
    │       ├── 4_classify/  request.json · configuration.json · response.json · result.json · metrics.json
    │       ├── 5_schema/    request.json · generated.json · schema.json · validation.json · configuration.json
    │       ├── 6_extract/   request.json · response.json · result.json · metadata.json · fields.json · boxes.json
    │       └── historial/   las ejecuciones anteriores de cada paso
    └── libraries/
        └── 2026-11-21_133046_aprendizaje-automatico-ii/
            ├── run.json                 nombre, motor, modelos, documentos con su metadata, estado del sync
            ├── documents/<corrida>.json el Markdown de cada página que se indexó, con su metadata
            ├── index/                   el índice de LlamaIndex (docstore, vectores)
            ├── syncs/<fecha>/           las métricas de cada sincronización
            ├── searches/<fecha>.json    cada búsqueda de prueba con sus resultados
            ├── chats/local/turno_N.json cada turno: pregunta, respuesta, búsquedas, páginas, prompts, tokens y eventos
            ├── evals/<fecha>/           cada corrida de evals: request, resultados y métricas
            └── historial/               los índices anteriores
```

Cada paso guarda siempre `request.json` (qué se pidió) y `response.json` (la respuesta completa de LlamaCloud). Los demás archivos son partes de esa respuesta separadas, para verlas y descargarlas fácil. **Todo en UTF-8:** en Windows, Python usa cp1252 si no se lo dice, y falla con caracteres como "○" (ver la bitácora del 21/11).

### Rutas HTTP

| Ruta | Qué hace |
|---|---|
| `GET /api/config` | Qué está listo y con qué opciones (nunca las claves) |
| `GET` / `POST /api/documents/runs` | Lista las corridas · sube un archivo y crea la corrida |
| `GET` / `DELETE /api/documents/runs/{id}` | El estado de todos los pasos · borra la corrida (la carpeta y todo en LlamaCloud) |
| `POST` / `GET /api/documents/runs/{id}/steps/{paso}` | Arranca un paso con sus opciones · consulta su estado y, si terminó, resultado, métricas e interpretación |
| `GET /api/documents/runs/{id}/files/{ruta}` | Descarga un archivo guardado |
| `GET` / `POST /api/documents/libraries` | Lista y crea bibliotecas |
| `GET` / `DELETE /api/documents/libraries/{id}` | La biblioteca con sus documentos, búsquedas y turnos · la borra |
| `POST /api/documents/libraries/{id}/documents` · `DELETE …/documents/{corrida}` | Suma o saca una corrida del wizard |
| `POST` / `GET /api/documents/libraries/{id}/sync` | Arranca y consulta la sincronización del índice |
| `POST /api/documents/libraries/{id}/search` | Búsqueda de prueba (`query`, `top_k`, `filters`) |
| `POST /api/documents/libraries/{id}/chat` | Un turno de chat (`prompt`, `conversation_id`, `filters`): los eventos llegan en vivo (Server-Sent Events) y al final se guardan |
| `GET` / `POST /api/documents/libraries/{id}/conversations` | Las conversaciones abiertas (las pestañas del chat) · crea una vacía |
| `GET /api/documents/libraries/{id}/conversations/{c}` · `POST …/{c}/close` | Una conversación con sus turnos · la cierra (no borra nada) |
| `POST /api/documents/libraries/{id}/evals` | Corre los evals con un set de preguntas (`conjunto`, `candidatos`, `respuestas`, `top_k`, `modo`) |

### Frontend

```
frontend/src/
├── App.tsx                              las pestañas Chat (la principal), Documentos y Bibliotecas
├── components/wizard/                   Stepper · StepPanel · JsonView · MarkdownView · RunList · RowsEditor · PageBoxes
└── pipelines/documents/
    ├── DocumentsWizard.tsx · api.ts
    ├── steps/                           UploadStep · ParseStep · SplitStep · ClassifyStep · SchemaStep · ExtractStep
    ├── chat/                            ChatPage · ProjectJourney · ConversationTabs · ChatThread · ChatFilters
    │                                    AnswerSources · BehindTheScenes · explicaciones.ts (los textos fijos)
    └── libraries/                       LibrariesView · LibrarySearch · LibraryChat · LibraryEvals · api.ts
```

---

## 8. Las fases

| Fase | Qué | Estado |
|---|---|---|
| 0 | Reorganización: cada pipeline en su carpeta, con su README | ✅ |
| 1 | Informe: relevamiento de la API de LlamaCloud y 16 hallazgos ([informe-fase-1.md](informe-fase-1.md)) | ✅ |
| 2 | Motor de corridas (carpeta-DB), wizard base, Subir y Parse | ✅ |
| 3 | Split, Classify, Schema (manual o automático) y Extract, con las cajas sobre las capturas | ✅ |
| 4 | Bibliotecas: índice compartido, búsqueda, chat, evals y paso 7 del wizard | ✅ con el motor local · 🔒 el de LlamaCloud necesita plan pago |
| 5 | Audio | ➡️ En **parla-audio** |
| 6 | Cierre para la clase: el chat como página principal, guion de la demo, Docker | 🟡 Página principal y guion hechos; falta Docker y la revisión final (ver [estado.md](estado.md)) |

**Listo cuando (fase 4, con el corpus nuevo):** en la biblioteca "Aprendizaje Automático II", una pregunta que cruza clases (por ejemplo, *"¿qué tienen en común ResNet y U-Net?"*) se responde citando las dos clases, y se ve qué buscó en cada una.

---

## 9. Roadmap (después de la clase)

- **Pasar la carpeta-DB a `agent_data`.** Es la base JSON nativa de LlamaCloud, con búsqueda, filtros y agregaciones. Hoy elegimos la carpeta para que la demo funcione sin conexión y los archivos se puedan abrir a mano.
- **Verify** (`alpha.verify`): detectar si un documento fue adulterado. Lo sumamos cuando salga de alpha.
- **Evals más exigentes:** el set ya tiene preguntas parafraseadas y que cruzan clases. [Ragas](https://docs.ragas.io/) queda solo si lo nativo de LlamaIndex no alcanza (sumaría *context precision* y *context recall*; tiene integración con LlamaIndex).
- **Notebooks de las clases** con `IPYNBReader` (lector nativo de LlamaIndex), si se quiere que el chat responda sobre el código de las prácticas.
- **Webhooks:** que LlamaCloud avise cuando termina un job o un lote, en lugar de consultar. Solo sirve con el servidor publicado en internet.
- **Índice de LlamaCloud** cuando haya un plan pago: el motor ya está escrito; comparar calidad, velocidad y costo contra el local.
- **Comparar modelos de OpenAI** para el chat (`gpt-5-nano` contra uno más grande), con los mismos evals.
