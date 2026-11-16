# Plan completo · Parla RAG como demo de clase

**Escrito:** 13/11/2026 · **Actualizado:** 15/11/2026 · **Estado de cada fase:** [estado.md](estado.md) · **Detalle técnico de la API:** [informe-fase-1.md](informe-fase-1.md)

> El 15/11/2026 Parla se separó en dos proyectos. Este plan es el de **documentos y bibliotecas**. La fase 5 (audio con ElevenLabs) sigue en **parla-audio**.

---

## 1. Objetivo

Armar una **demo detallada para mostrar en clase** cómo funciona un pipeline de documentos con IA, paso por paso.
Se sube un documento y se avanza con un **wizard**: en cada paso se hace clic, se espera a que termine (aparece un tilde verde) y se ve **todo** lo que produjo ese paso, guardado, medido y explicado.

Los documentos que se relacionan entre sí se juntan en una **biblioteca**: comparten un índice y se puede **chatear con todos a la vez**.

La misma metodología se aplica al **audio** (ElevenLabs) en el proyecto **parla-audio**. Sumar su transcripción a una biblioteca queda pendiente: ver [estado.md](estado.md#integración-con-parla-audio).

## 2. Reglas del proyecto

1. **Solo lo nativo.** No se implementa nada que LlamaCloud, LlamaIndex o LlamaParse no hagan de forma nativa. Nada de código innecesario. El framework LlamaIndex y sus integraciones oficiales (Voyage AI, DeepSeek) cuentan como nativos.
2. **Extraer todo en cada paso.** Cada paso pide a la plataforma toda la información que ofrece, la **guarda**, la **mide** y la **interpreta**.
3. **Código simple, no "senior".** Fácil de leer, con un comentario `#` (o `//` en TypeScript) en español rioplatense arriba de cada función. Toda la documentación va en español.
4. **Cada pipeline vive en su carpeta.** Su configuración, su cliente, sus pasos y sus rutas van juntos. En `core/` solo queda lo compartido.
5. **Sin base de datos.** Todo se guarda en carpetas dentro de `backend/data/`, simulando una DB.

## 3. Los documentos de la demo

Están en `backend/data/samples/byma/`. Son documentos públicos de BYMA (Bolsas y Mercados Argentinos) sobre los resultados del 3er trimestre de 2026, bajados de su [página de relación con inversores](https://www.byma.com.ar/relacion-con-inversores/informacion-financiera). Los tres hablan de lo mismo, así que sirven para una **biblioteca** y para un chat que cruce las fuentes.

| Archivo | Tamaño | Qué es | Qué muestra en clase |
|---|---|---|---|
| `BYMA - EEFF 30-09-2026 - VF.pdf` | 86 páginas · 3,4 MB | Estados financieros consolidados: balance, resultados, notas, informe del auditor | **Split** para separar las secciones; tablas largas que siguen de una página a otra; **Extract solo sobre una sección** |
| `BYMA Comunicado de Prensa - 3T26.pdf` | 10 páginas · 0,3 MB | Comunicado de resultados | **Schema automático**: el agente propone los campos (ingresos, resultado neto, EBITDA…) |
| `Presentacion_de_Resultados-3T26.pdf` | 15 páginas · 0,7 MB | Diapositivas con mucho gráfico y poco texto | **Parse con gráficos e imágenes**, donde más se nota el parse con IA |

También queda `backend/data/samples/factura_ejemplo.pdf`, una factura simple de una página. El MP3 de la presentación (~9 min) está en **parla-audio**.

## 4. Créditos

Los créditos son de la cuenta de **LlamaCloud**, la plataforma de la empresa LlamaIndex. **LlamaParse** es el nombre de sus productos de documentos (Parse, Extract, Split, Classify…). No son dos saldos distintos: todos los productos descuentan del mismo saldo.

- **Saldo al 13/11:** 29.443 de 30.000 al empezar; después de las dos pruebas de Parse (795 créditos), unos 28.648.
- **Cuánto cuesta cada cosa:** el costo depende del producto, del tier y de la cantidad de páginas. Cada job devuelve lo que cobró (`usage`), así que no hace falta adivinar. En la fase 2 se mide el costo real con el comunicado (10 páginas) y con eso se calcula el resto antes de procesar el de 86.
- **Cómo se ahorra con los documentos grandes**, sin código nuestro:
  - Cada documento se **parsea una sola vez**. Split, Classify y Extract usan ese parse (`pjb-...`) y no vuelven a leer el documento.
  - **Split** ubica las secciones y **Extract corre solo sobre las páginas que interesan** (`target_pages`), por ejemplo el estado de resultados y no las 86 páginas.
  - Se elige el **tier** según el documento: uno económico para el texto corrido y `agentic` para la presentación con gráficos.
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
5. **La interpretación:** frases armadas con esos datos, como "la página 2 tiene la confianza más baja: conviene revisarla". No se usa un LLM extra.

### Detalle de cada paso

| # | Paso | Producto de LlamaCloud | Qué se pide (lo máximo) | Qué se guarda | Qué se mide e interpreta |
|---|---|---|---|---|---|
| 1 | **Subir** | `files.create` | — | El archivo original y la respuesta | Tipo, tamaño, páginas, `file_id` |
| 2 | **Parse** | `parsing.create` / `get` | Tier y versión fijos, **sin límite de páginas** (Split rechaza los parses limitados), corrección de fotos de celular, tablas (incluso las que siguen en otra página), gráficos, imágenes, formularios, confianza, número de página impreso, marcas de agua. `expand` con todo y las 3 salidas extra (`stripped_md`, `concatenated_stripped_txt`, `word_bbox`) | `document.md`, `text.txt`, `items.json`, `metadata.json`, `forms.json`, `images/` | Páginas, palabras, tablas, imágenes, gráficos, confianza por página y del documento (con la peor página), rotación, marca de agua, créditos, tiempo |
| 3 | **Split** | `split.create` / `get` | Entrada: el parse (`pjb-...`). Categorías editables (por ejemplo, para los EEFF: balance, estado de resultados, flujo de efectivo, notas, informe del auditor) y estrategia de corte | `segments.json` | Cantidad de segmentos, rango de páginas y categoría de cada uno |
| 4 | **Classify** | `classify.create` / `get` | Entrada: el parse. Reglas editables (tipo más descripción), por ejemplo: estados financieros, comunicado, presentación, factura | `result.json`, con type, confidence y **reasoning** | Confianza, créditos y el **razonamiento del modelo**, tal cual |
| 5 | **Schema** | `extract.generate_schema`, `validate_schema`, `configurations` | **Manual:** el editor de campos. **Automático:** el agente propone los campos a partir del documento (y de una indicación opcional). En los dos casos se valida y se guarda como configuración con nombre | `schema.json`, `validation.json`, `configuration.json` | Cantidad de campos y tipos, origen (manual o agente) y diferencias entre los dos |
| 6 | **Extract** | `extract.create` / `get` | Entrada: el parse. `configuration_id` del paso 5, **páginas elegidas a partir de un segmento del Split**, `cite_sources`, `advanced_citations`, `confidence_scores` | `result.json` (tal cual), `metadata.json`, `fields.json` (cada campo con valor, confianza y citas), `boxes.json` | Campos encontrados y vacíos, confianza promedio, mínima y máxima, campos a revisar, citas sobre el documento, créditos |
| 7 | **Biblioteca** *(pendiente como paso del wizard; hoy se hace desde la pestaña Bibliotecas)* | motor local: el parse del paso 2 · LlamaCloud: `beta.directories.files.add`, `indexes.sync` | Elegir una biblioteca (o crear una) y sumar el documento a su índice | La copia del Markdown por página en la biblioteca | — (el detalle se ve en la biblioteca) |

### Schema manual o automático (paso 5)

Los dos modos terminan en **el mismo editor de campos**. Cada campo tiene nombre, tipo (texto, número, fecha, sí/no, lista), una guía (la `description` que lee LlamaExtract) y si es obligatorio.

- **Manual:** arrancás con el editor vacío o cargás una **plantilla**. Por ejemplo, "Factura AR" son los 10 campos que hoy están fijos en el código, pero con tipos de verdad: los importes como números.
- **Automático:** `generate_schema` analiza el documento y propone los campos. La propuesta cae en el editor, donde la podés corregir.
- **Siempre:** se valida con `validate_schema` y se guarda en **`configurations` de LlamaCloud** con un nombre. Así queda como plantilla reutilizable, sin una carpeta nuestra.

---

## 6. Bibliotecas: un índice compartido y el chat

Una **biblioteca** junta documentos que se relacionan entre sí. Por ejemplo, "BYMA 3T26" con los EEFF, el comunicado y la presentación. Hay **dos motores** con las mismas funciones y las mismas respuestas, así la pantalla es una sola. Cada biblioteca recuerda con qué motor se creó; las nuevas usan `LIBRARY_ENGINE`.

### Motor local (el que se usa): LlamaIndex + Voyage AI + DeepSeek

El índice de LlamaCloud necesita un plan pago (con el plan gratis responde 403), así que la biblioteca se arma en nuestro servidor con el **framework LlamaIndex** y dos integraciones oficiales:

```
Biblioteca "BYMA 3T26"
 ├── EEFF · Comunicado · Presentación    corridas del wizard: se usa su parse, NO se vuelve a parsear
 │      ↓ una página = un Document de LlamaIndex, con su número y la metadata de identidad
 ├── index/        VectorStoreIndex con embeddings voyage-4, guardado en la carpeta
 ├── búsqueda      voyage-4 trae 3 candidatos por resultado → rerank-2.5 los ordena
 └── chat          CondensePlusContextChatEngine: reescribe la pregunta (si hay historial),
                   busca como arriba y deepseek-flash responde citando documento y página
```

- **Agregar** una corrida copia a la biblioteca el Markdown de cada página de su parse, con la metadata: el tipo de Classify y los campos **obligatorios** del schema de Extract (los de identidad). Así queda auditable qué texto se indexó.
- **Sacar** un documento lo deja afuera en la próxima sincronización; su copia queda para auditar.
- **Sincronizar** vuelve a armar el índice entero y guarda el anterior en el historial. Es local y responde en el momento.
- **Buscar** acepta filtros por metadata (solo igualdad) y guarda cada búsqueda con sus resultados.
- **Chatear:** las instrucciones piden responder solo con los fragmentos, decir que el dato no está cuando no está, citar *(documento, pág. N)* y copiar los números tal cual. Los eventos son los mismos que los del chat de LlamaCloud (`tool_call`, `tool_result`, `text_delta`, `stop`).
- **Qué se mide:** páginas indexadas y chunks; de cada búsqueda, el score vectorial y el del reranker; de cada turno, la consulta real, las páginas que leyó el modelo, el prompt completo y los tokens (con la instrumentación nativa de LlamaIndex).

### Motor de LlamaCloud (escrito, bloqueado por el plan)

En LlamaCloud una biblioteca es **un directorio con su índice**; todo es nativo:

```
Biblioteca "BYMA 3T26"
 ├── EEFF 30-09-2026.pdf          ┐
 ├── Comunicado de prensa.pdf     ├── directorio de LlamaCloud ──→ índice ──→ búsqueda ──→ chat
 └── Presentación 3T26.pdf        ┘   (files.add / files.delete)   (sync)    (retrieve)   (stream)
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
    ├── README.md · settings.py · client.py · errors.py
    ├── pipeline.py                      la lista ordenada de pasos (empezá a leer por acá)
    ├── router.py                        /api/documents/runs/...
    ├── steps/                           un archivo por paso; cada uno tiene:
    │   ├── s1_upload.py                   EXPLICACION  el texto para la clase
    │   ├── s2_parse.py                    start()      arranca el job en LlamaCloud
    │   ├── s3_split.py                    check()      consulta el estado y, si terminó, guarda todo
    │   ├── s4_classify.py                 summarize()  métricas e interpretación con lo guardado
    │   ├── s5_schema.py                   DEFAULTS     las opciones con las que arranca el editor
    │   ├── s6_extract.py
    │   └── jobs.py                        lo común a los pasos con job
    ├── library_router.py                /api/documents/libraries/... (elige el motor de cada biblioteca)
    ├── local_library.py                 motor local: LlamaIndex + Voyage AI + DeepSeek
    └── library.py                       motor de LlamaCloud: directorio, índice, búsqueda y chat
```

### La carpeta-DB

```
backend/data/
├── samples/                             documentos de prueba (van al repo)
│   ├── factura_ejemplo.pdf
│   └── byma/                            EEFF, comunicado y presentación
├── nltk/                                datos de NLTK para LlamaIndex (se bajan solos, con permisos privados)
├── verificacion/                        datos crudos de las verificaciones
└── documents/
    ├── runs/
    │   └── 2026-11-13_172417_byma-comunicado-de-prensa-3t26/
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
        └── 2026-11-14_192312_byma-3t26/
            ├── run.json                 nombre, motor, modelos, documentos con su metadata, estado del sync
            ├── documents/<corrida>.json el Markdown de cada página que se indexó, con su metadata
            ├── index/                   el índice de LlamaIndex (docstore, vectores)
            ├── syncs/<fecha>/           las métricas de cada sincronización
            ├── searches/<fecha>.json    cada búsqueda de prueba con sus resultados
            ├── chats/local/turno_N.json cada turno: pregunta, respuesta, búsquedas, páginas, prompts, tokens y eventos
            └── historial/               los índices anteriores
```

Cada paso guarda siempre `request.json` (qué se pidió) y `response.json` (la respuesta completa de LlamaCloud). Los demás archivos son partes de esa respuesta separadas, para verlas y descargarlas fácil.

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
| `POST /api/documents/libraries/{id}/chat` | Un turno de chat: los eventos llegan en vivo (Server-Sent Events) y al final se guardan |

### Frontend

```
frontend/src/
├── App.tsx                              las pestañas Documentos y Bibliotecas
├── components/wizard/                   Stepper · StepPanel · JsonView · MarkdownView · RunList · RowsEditor · PageBoxes
└── pipelines/documents/
    ├── DocumentsWizard.tsx · api.ts
    ├── steps/                           UploadStep · ParseStep · SplitStep · ClassifyStep · SchemaStep · ExtractStep
    └── libraries/                       LibrariesView · LibrarySearch · LibraryChat · api.ts
```

---

## 8. Las fases

> **Cambio de orden:** el wizard va antes que el schema. El schema es el paso 5 del wizard; si lo hiciéramos primero sobre la pantalla actual, habría que reescribirlo después.

### ✅ Fase 0 · Reorganización (commit `41e0666`)
Cada pipeline quedó autocontenido en su carpeta, con un README por pipeline y un comentario en rioplatense arriba de cada función. No cambió el comportamiento: los 25 tests pasan.

### ✅ Fase 1 · Informe (commit `ea47134`)
El relevamiento completo de la API de LlamaCloud y 16 hallazgos sobre el código actual. Ver [informe-fase-1.md](informe-fase-1.md).

### Fase 2 · Verificación, motor de corridas, Subir y Parse · ✅ terminada

**Primero se verifica** con llamadas reales: se prueba a mano con el **comunicado** (10 páginas, barato) y se guarda lo que devuelve cada producto.
1. El **costo real** de Parse, Split, Classify y Extract, y con eso la estimación para los EEFF de 86 páginas.
2. Si el índice nuevo deja **listar todos los chunks**, o solo los que devuelve una búsqueda.
3. Qué valores acepta `images_to_save` y si las capturas de página sirven para dibujar las cajas de las citas.
4. Si Split devuelve `usage`.

*Te aviso antes de cada llamada que gaste créditos.*

**Después se construye:**
- `core/runs/` con la carpeta-DB y el estado de los pasos.
- El wizard base en el frontend: el stepper, el panel de paso, los visores y la lista de corridas.
- Los pasos **1 Subir** y **2 Parse** completos, con todo lo que ofrece Parse. Los límites de archivo se adaptan a los documentos grandes. No hay límite de páginas: Split rechaza los parses con `max_pages`.

**Se elimina:** `jobs.py`, la barra de progreso simulada, el cleanup automático y el conteo de páginas con pypdf.
**Hallazgos que resuelve:** #5, #7, #8, #9, #10 y #12.
**Listo cuando:** se suben el comunicado y la presentación, se corre Parse, aparece el tilde y se ven el `.md`, las páginas, los gráficos, la confianza, los créditos y la interpretación. Además, la corrida sobrevive a reiniciar el servidor.

### ✅ Fase 3 · Split, Classify, Schema y Extract · terminada (probada en los EEFF y en el comunicado; ver la bitácora)
- Los pasos **3 Split** y **4 Classify**, encadenados al parse (`pjb-...`), con categorías y reglas editables.
- El paso **5 Schema**, manual o automático: el editor, `generate_schema`, `validate_schema` y las plantillas en `configurations`. Se crea la plantilla "Factura AR".
- El paso **6 Extract** con la configuración guardada, las citas avanzadas y toda la metadata, **sobre las páginas de un segmento del Split**. Las cajas se dibujan sobre el documento.
- **Cajas sobre el archivo subido, sea PDF o imagen.** Se dibujan sobre las capturas de página de Parse, que están en la misma escala que las citas. Se muestran las de Parse (ítems, tablas, gráficos) y las de Extract (de dónde salió cada campo), para ver qué identificó LlamaCloud en el archivo.
- **Un campo de identidad en el schema** (`emisor`), con una guía que dice que BYMA, Bolsas y Mercados Argentinos S.A. y "la Sociedad" son lo mismo. Así cada documento devuelve el mismo valor.

**Se elimina:** `schema.py` (los campos fijos), `clean_amount`, `EMPTY_WORDS`, `normalize_result`, `invoiceCsv` e `invoiceMarkdown`, junto con sus tests. Si en la fase 2 las capturas de página alcanzan, también `PdfPreview` y `pdfjs`.
**Hallazgos que resuelve:** #1, #2, #3, #4, #6, #13, #14 y #16.
**Listo cuando:** con los EEFF, Split encuentra el estado de resultados y Extract saca sus datos solo de esas páginas. Y el comunicado se extrae una vez con schema manual y otra con automático, para comparar.

### 🟡 Fase 4 · Bibliotecas: índice compartido, búsqueda y chat · casi terminada
- ✅ Crear bibliotecas y **agregar o sacar** documentos con la sincronización del índice, desde la pestaña Bibliotecas.
- ✅ La **búsqueda de prueba** con los chunks, su score, su documento y sus páginas.
- ✅ El **chat** sobre toda la biblioteca, mostrando las búsquedas y las páginas que usó. Cada turno queda guardado.
- ✅ **Motor local** (LlamaIndex + Voyage AI + DeepSeek), porque el índice de LlamaCloud necesita un plan pago. Chat probado de punta a punta con la factura.
- 🔒 **Motor de LlamaCloud** escrito y probado con el cliente falso; bloqueado por el plan (403).
- ⏳ **Sincronizar "BYMA 3T26"**: bloqueado por el límite de Voyage sin medio de pago (3 pedidos y 10.000 tokens por minuto).
- ⏳ **Procesar en lote** (`batches`): necesita el plan pago.
- ⏳ **Paso 7 del wizard** ("Biblioteca"): un botón al final del wizard para sumar el documento.

**Listo cuando:** con la biblioteca "BYMA 3T26" (EEFF, comunicado y presentación), al preguntar *"¿el resultado neto del comunicado coincide con el de los estados financieros?"*, el chat responde citando los dos documentos y se ve qué buscó en cada uno. Además, se saca un documento, se sincroniza, y el chat ya no lo usa.

### ➡️ Fase 5 · Audio
Se fue al proyecto **parla-audio** el 15/11/2026, con su relevamiento de ElevenLabs. Lo que queda de este lado es **sumar la transcripción a una biblioteca**: ver [estado.md](estado.md#integración-con-parla-audio).

### Fase 6 · Cierre para la clase
- Revisar todos los README y comentarios.
- Dejar listas las corridas y la biblioteca "BYMA 3T26" (sincronizada) en `data/`.
- Escribir un guion corto para la demo: qué mostrar en cada paso y qué preguntarle al chat.
- Correr todo con Docker, de punta a punta.

---

## 9. Roadmap (después de la clase)

- **Pasar la carpeta-DB a `agent_data`.** Es la base JSON nativa de LlamaCloud, con búsqueda, filtros y agregaciones. Hoy elegimos la carpeta para que la demo funcione sin conexión y los archivos se puedan abrir a mano.
- **Verify** (`alpha.verify`): detectar si un documento fue adulterado. Lo sumamos cuando salga de alpha.
- **Evals contra la alucinación** (se decide después de tener todo funcionando de punta a punta). Medir si las respuestas del chat y de Extract son fieles a los documentos. **Con el motor local ahora es directo:** Ragas tiene integración con el framework LlamaIndex y cada turno guardado ya trae pregunta, respuesta y fragmentos.
  - **Primera opción: [Ragas](https://docs.ragas.io/).** Tiene integración directa con el **framework** LlamaIndex (`ragas.integrations.llama_index`, sobre un query engine), pero no encontré una integración con **LlamaCloud**. Para el motor de LlamaCloud habría que armarle a Ragas el dataset con lo que guardamos de cada turno de chat: pregunta, respuesta y los fragmentos que usó (`tool_result`). Métricas: *faithfulness* (si la respuesta se apoya en los fragmentos), *context precision* y *context recall*. Ragas usa un LLM como juez, así que tiene costo propio.
  - **Además:** un set de respuestas verificadas a mano para BYMA 3T26 (las 8 cifras de Extract, la página 5 de la presentación y preguntas de identidad como "¿qué dice la Sociedad…?").
- **Webhooks:** que LlamaCloud avise cuando termina un job o un lote, en lugar de consultar. Solo sirve con el servidor publicado en internet.
- **Índice de LlamaCloud** cuando haya un plan pago: el motor ya está escrito; comparar calidad, velocidad y costo contra el local.
- **Probar `deepseek-v4-pro`** para el chat y compararlo con `deepseek-flash`.
