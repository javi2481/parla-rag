# Plan completo · Parla como demo de clase

**Fecha:** 13/11/2026 · **Estado:** fases 0 y 1 terminadas · **Detalle técnico de los hallazgos:** [informe-fase-1.md](informe-fase-1.md)

---

## 1. Objetivo

Armar una **demo detallada para mostrar en clase** cómo funciona un pipeline de documentos con IA, paso por paso.
Se sube un documento y se avanza con un **wizard**: en cada paso se hace clic, se espera a que termine (aparece un tilde verde) y se ve **todo** lo que produjo ese paso, guardado, medido y explicado.

Los documentos que se relacionan entre sí se juntan en una **biblioteca**: comparten un índice y se puede **chatear con todos a la vez**.

Después se aplica la misma metodología al pipeline de **audio** (ElevenLabs), y su transcripción también se puede sumar a la biblioteca.

## 2. Reglas del proyecto

1. **Solo lo nativo.** No se implementa nada que LlamaCloud, LlamaIndex o LlamaParse no hagan de forma nativa. Nada de código innecesario.
2. **Extraer todo en cada paso.** Cada paso pide a la plataforma toda la información que ofrece, la **guarda**, la **mide** y la **interpreta**.
3. **Código simple, no "senior".** Fácil de leer, con un comentario `#` (o `//` en TypeScript) en español rioplatense arriba de cada función. Toda la documentación va en español.
4. **Cada pipeline vive en su carpeta.** Su configuración, su cliente, sus pasos y sus rutas van juntos. En `core/` solo queda lo compartido.
5. **Sin base de datos.** Todo se guarda en carpetas dentro de `backend/data/`, simulando una DB.

## 3. Los documentos de la demo

Están en `backend/data/samples/byma/`. Son documentos públicos de BYMA (Bolsas y Mercados Argentinos) sobre los resultados del 3er trimestre de 2026, bajados de su [página de relación con inversores](https://www.byma.com.ar/relacion-con-inversores/informacion-financiera). Los cuatro hablan de lo mismo, así que sirven para una **biblioteca** y para un chat que cruce las fuentes.

| Archivo | Tamaño | Qué es | Qué muestra en clase |
|---|---|---|---|
| `BYMA - EEFF 30-09-2026 - VF.pdf` | 86 páginas · 3,4 MB | Estados financieros consolidados: balance, resultados, notas, informe del auditor | **Split** para separar las secciones; tablas largas que siguen de una página a otra; **Extract solo sobre una sección** |
| `BYMA Comunicado de Prensa - 3T26.pdf` | 10 páginas · 0,3 MB | Comunicado de resultados | **Schema automático**: el agente propone los campos (ingresos, resultado neto, EBITDA…) |
| `Presentacion_de_Resultados-3T26.pdf` | 15 páginas · 0,7 MB | Diapositivas con mucho gráfico y poco texto | **Parse con gráficos e imágenes**, donde más se nota el parse con IA |
| `Presentacion_Resultados_3T2026.mp3` | ~10 min · 8,6 MB | El audio de la presentación de resultados | **Transcripción** con hablantes y tiempos, sumada a la biblioteca |

También queda `backend/data/samples/factura_ejemplo.pdf`, una factura simple de una página.

## 4. Créditos

Los créditos son de la cuenta de **LlamaCloud**, la plataforma de la empresa LlamaIndex. **LlamaParse** es el nombre de sus productos de documentos (Parse, Extract, Split, Classify…). No son dos saldos distintos: todos los productos descuentan del mismo saldo.

- **Saldo al 13/11:** 29.443 de 30.000.
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
| 2 | **Parse** | `parsing.create` / `get` | Tier y versión fijos, rango de páginas (`page_ranges`), corrección de fotos de celular, tablas (incluso las que siguen en otra página), gráficos, imágenes, formularios, confianza, número de página impreso, marcas de agua. `expand` con todo: markdown, text, items, metadata, forms, images, job_metadata, usage | `document.md`, `text.txt`, `items.json`, `metadata.json`, `forms.json`, `images/` | Páginas, palabras, tablas, imágenes, gráficos, confianza por página y del documento (con la peor página), rotación, marca de agua, créditos, tiempo |
| 3 | **Split** | `split.create` / `get` | Entrada: el parse (`pjb-...`). Categorías editables (por ejemplo, para los EEFF: balance, estado de resultados, flujo de efectivo, notas, informe del auditor) y estrategia de corte | `segments.json` | Cantidad de segmentos, rango de páginas y categoría de cada uno |
| 4 | **Classify** | `classify.create` / `get` | Entrada: el parse. Reglas editables (tipo más descripción), por ejemplo: estados financieros, comunicado, presentación, factura | `result.json`, con type, confidence y **reasoning** | Confianza, créditos y el **razonamiento del modelo**, tal cual |
| 5 | **Schema** | `extract.generate_schema`, `validate_schema`, `configurations` | **Manual:** el editor de campos. **Automático:** el agente propone los campos a partir del documento (y de una indicación opcional). En los dos casos se valida y se guarda como configuración con nombre | `schema.json`, `validation.json`, `configuration.json` | Cantidad de campos y tipos, origen (manual o agente) y diferencias entre los dos |
| 6 | **Extract** | `extract.create` / `get` | Entrada: el parse. `configuration_id` del paso 5, **páginas elegidas a partir de un segmento del Split**, `cite_sources`, `advanced_citations`, `confidence_scores` | `result.json` (tal cual), `metadata.json` (por documento, página y fila), `boxes.json` | Campos encontrados y vacíos, confianza promedio, mínima y máxima, campos a revisar, citas sobre el documento, créditos |
| 7 | **Biblioteca** | `beta.directories.files.add`, `indexes.sync` | Elegir una biblioteca (o crear una) y sumar el documento a su índice | El vínculo con la biblioteca en `run.json` | — (el detalle se ve en la biblioteca) |

### Schema manual o automático (paso 5)

Los dos modos terminan en **el mismo editor de campos**. Cada campo tiene nombre, tipo (texto, número, fecha, sí/no, lista), una guía (la `description` que lee LlamaExtract) y si es obligatorio.

- **Manual:** arrancás con el editor vacío o cargás una **plantilla**. Por ejemplo, "Factura AR" son los 10 campos que hoy están fijos en el código, pero con tipos de verdad: los importes como números.
- **Automático:** `generate_schema` analiza el documento y propone los campos. La propuesta cae en el editor, donde la podés corregir.
- **Siempre:** se valida con `validate_schema` y se guarda en **`configurations` de LlamaCloud** con un nombre. Así queda como plantilla reutilizable, sin una carpeta nuestra.

---

## 6. Bibliotecas: un índice compartido y el chat

Una **biblioteca** junta documentos que se relacionan entre sí. Por ejemplo, "BYMA 3T26" con los EEFF, el comunicado, la presentación y la transcripción del audio. En LlamaCloud es **un directorio con su índice**; todo es nativo.

```
Biblioteca "BYMA 3T26"
 ├── EEFF 30-09-2026.pdf          ┐
 ├── Comunicado de prensa.pdf     ├── directorio de LlamaCloud ──→ índice ──→ búsqueda ──→ chat
 ├── Presentación 3T26.pdf        │   (files.add / files.delete)   (sync)    (retrieve)   (stream)
 └── Transcripción del audio      ┘
```

**Qué se puede hacer:**
- **Crear** una biblioteca y **agregar o sacar** documentos. Después `indexes.sync` actualiza el índice: solo vuelve a procesar lo que cambió.
- **Procesar en lote** (`batches`): correr el mismo trabajo (parse, extract o classify, con una configuración guardada) sobre **todos los documentos de la biblioteca a la vez**. Es la forma nativa de manejar varios PDFs grandes. El wizard sirve para mostrar un documento paso por paso; el lote sirve para procesar el resto de una vez.
- **Buscar:** una caja de **búsqueda de prueba** (`retrieval.retrieve`, búsqueda híbrida con rerank). Muestra los chunks recuperados con su score, de qué documento y de qué páginas salieron.
- **Chatear:** una sesión de chat atada al índice (`chat.create` y `chat.stream`). Se ven en vivo la respuesta, el **razonamiento** del agente y las **búsquedas que hizo** con lo que encontró. Ejemplo para la clase: *"¿el resultado neto del comunicado coincide con el de los estados financieros?"*.

**Qué se mide:** cantidad de documentos, chunks y tokens; de cada búsqueda, el score y el rerank; de cada turno de chat, los tokens, la duración, las herramientas usadas y qué documentos citó.

---

## 7. Dónde queda cada cosa

### Backend

```
backend/app/
├── core/
│   ├── settings.py · limits.py          (ya existen)
│   └── runs/                            el motor del wizard, lo reutilizan documentos y audio
│       ├── store.py                     la carpeta-DB: crear, leer, listar y borrar
│       └── models.py                    Run y StepState (locked / pending / running / done / failed)
└── pipelines/documents/
    ├── README.md · settings.py · client.py · router.py
    ├── pipeline.py                      la lista ordenada de pasos (empezá a leer por acá)
    ├── schemas.py                       el editor de campos ↔ JSON Schema, y configurations
    ├── libraries.py                     bibliotecas: directorio, índice, lote, búsqueda y chat
    └── steps/                           un archivo por paso; cada uno tiene:
        ├── s1_upload.py                   EXPLICACION (texto fijo para la clase)
        ├── s2_parse.py                    start()     arranca el job en LlamaCloud
        ├── s3_split.py                    check()     consulta el estado y, si terminó, guarda todo
        ├── s4_classify.py                 metrics()   calcula las métricas con lo guardado
        ├── s5_schema.py                   interpret() arma las frases de interpretación
        ├── s6_extract.py
        └── s7_library.py
```

### La carpeta-DB

```
backend/data/
├── samples/                             documentos de prueba (van al repo)
│   ├── factura_ejemplo.pdf
│   └── byma/                            EEFF, comunicado, presentación y audio
├── audio/cache/                         audios ya pagados
└── documents/
    ├── runs/
    │   └── 2026-11-13_1530_byma-comunicado/
    │       ├── run.json                 estado de cada paso, IDs de LlamaCloud, créditos, tiempos, biblioteca
    │       ├── 1_upload/    original.pdf · request.json · response.json
    │       ├── 2_parse/     request.json · response.json · document.md · text.txt · items.json
    │       │                metadata.json · forms.json · images/ · metrics.json
    │       ├── 3_split/     … · segments.json · metrics.json
    │       ├── 4_classify/  … · result.json · metrics.json
    │       ├── 5_schema/    schema.json · validation.json · configuration.json
    │       └── 6_extract/   … · result.json · metadata.json · boxes.json · metrics.json
    └── libraries/
        └── byma-3t26/
            ├── library.json             nombre, documentos, IDs del directorio y del índice, créditos
            ├── batches/                 cada lote: qué se corrió y el resultado de cada archivo
            ├── queries/                 cada búsqueda de prueba con sus chunks
            └── chats/                   cada sesión con todos los eventos de cada turno
```

Cada paso guarda siempre `request.json` (qué se pidió) y `response.json` (la respuesta completa de LlamaCloud). Los demás archivos son partes de esa respuesta separadas, para verlas y descargarlas fácil.

### Rutas HTTP

| Ruta | Qué hace |
|---|---|
| `GET` / `POST /api/documents/runs` | Lista las corridas · sube un archivo y crea la corrida |
| `GET` / `DELETE /api/documents/runs/{id}` | El estado de todos los pasos · borra la corrida (la carpeta y los recursos en LlamaCloud) |
| `POST` / `GET /api/documents/runs/{id}/steps/{paso}` | Arranca un paso con sus opciones · consulta su estado y, si terminó, resultado, métricas e interpretación |
| `GET /api/documents/runs/{id}/files/{ruta}` | Descarga un archivo guardado (el `.md`, el `.json`…) |
| `GET` / `POST /api/documents/schemas` | Lista y guarda plantillas (en `configurations`) |
| `POST /api/documents/schemas/generate` · `/validate` | Schema automático y validación |
| `GET` / `POST /api/documents/libraries` | Lista y crea bibliotecas |
| `POST` / `DELETE /api/documents/libraries/{id}/documents/{run}` | Suma o saca un documento (y sincroniza el índice) |
| `POST /api/documents/libraries/{id}/batches` | Corre un lote sobre todos los documentos |
| `POST /api/documents/libraries/{id}/search` | Búsqueda de prueba |
| `POST /api/documents/libraries/{id}/chat` | Un turno de chat. Reenvía en vivo los eventos de LlamaCloud y al final los guarda |

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
    ├── steps/                           un panel por paso: UploadStep … LibraryStep
    └── library/                         LibraryView (documentos, lote, búsqueda) y LibraryChat
```

---

## 8. Las fases

> **Cambio de orden:** el wizard va antes que el schema. El schema es el paso 5 del wizard; si lo hiciéramos primero sobre la pantalla actual, habría que reescribirlo después.

### ✅ Fase 0 · Reorganización (commit `41e0666`)
Cada pipeline quedó autocontenido en su carpeta, con un README por pipeline y un comentario en rioplatense arriba de cada función. No cambió el comportamiento: los 25 tests pasan.

### ✅ Fase 1 · Informe (commit `ea47134`)
El relevamiento completo de la API de LlamaCloud y 16 hallazgos sobre el código actual. Ver [informe-fase-1.md](informe-fase-1.md).

### Fase 2 · Verificación, motor de corridas, Subir y Parse

**Primero se verifica** con llamadas reales: se prueba a mano con el **comunicado** (10 páginas, barato) y se guarda lo que devuelve cada producto.
1. El **costo real** de Parse, Split, Classify y Extract, y con eso la estimación para los EEFF de 86 páginas.
2. Si el índice nuevo deja **listar todos los chunks**, o solo los que devuelve una búsqueda.
3. Qué valores acepta `images_to_save` y si las capturas de página sirven para dibujar las cajas de las citas.
4. Si Split devuelve `usage`.

*Te aviso antes de cada llamada que gaste créditos.*

**Después se construye:**
- `core/runs/` con la carpeta-DB y el estado de los pasos.
- El wizard base en el frontend: el stepper, el panel de paso, los visores y la lista de corridas.
- Los pasos **1 Subir** y **2 Parse** completos, con todo lo que ofrece Parse. Los límites de archivo se adaptan a los documentos grandes y el de páginas se maneja con `page_ranges`.

**Se elimina:** `jobs.py`, la barra de progreso simulada, el cleanup automático y el conteo de páginas con pypdf.
**Hallazgos que resuelve:** #5, #7, #8, #9, #10 y #12.
**Listo cuando:** se suben el comunicado y la presentación, se corre Parse, aparece el tilde y se ven el `.md`, las páginas, los gráficos, la confianza, los créditos y la interpretación. Además, la corrida sobrevive a reiniciar el servidor.

### Fase 3 · Split, Classify, Schema y Extract
- Los pasos **3 Split** y **4 Classify**, encadenados al parse (`pjb-...`), con categorías y reglas editables.
- El paso **5 Schema**, manual o automático: el editor, `generate_schema`, `validate_schema` y las plantillas en `configurations`. Se crea la plantilla "Factura AR".
- El paso **6 Extract** con la configuración guardada, las citas avanzadas y toda la metadata, **sobre las páginas de un segmento del Split**. Las cajas se dibujan sobre el documento.

**Se elimina:** `schema.py` (los campos fijos), `clean_amount`, `EMPTY_WORDS`, `normalize_result`, `invoiceCsv` e `invoiceMarkdown`, junto con sus tests. Si en la fase 2 las capturas de página alcanzan, también `PdfPreview` y `pdfjs`.
**Hallazgos que resuelve:** #1, #2, #3, #4, #6, #13, #14 y #16.
**Listo cuando:** con los EEFF, Split encuentra el estado de resultados y Extract saca sus datos solo de esas páginas. Y el comunicado se extrae una vez con schema manual y otra con automático, para comparar.

### Fase 4 · Bibliotecas: índice compartido, lote, búsqueda y chat
- Crear bibliotecas, y **agregar o sacar** documentos con la sincronización del índice. Es el paso **7** del wizard y también se puede hacer desde la vista de la biblioteca.
- **Procesar en lote** (`batches`) todos los documentos de una biblioteca con una configuración guardada.
- La **búsqueda de prueba** con los chunks, su score, su documento y sus páginas.
- El **chat** sobre toda la biblioteca, mostrando el razonamiento y las búsquedas del agente. Cada turno queda guardado.

**Listo cuando:** con la biblioteca "BYMA 3T26" (EEFF, comunicado y presentación), al preguntar *"¿el resultado neto del comunicado coincide con el de los estados financieros?"*, el chat responde citando los dos documentos y se ve qué buscó en cada uno. Además, se saca un documento, se sincroniza, y el chat ya no lo usa.

### Fase 5 · Audio con la misma metodología
- **Primero, el relevamiento** de la API de ElevenLabs, igual que con LlamaCloud y con la misma regla de lo nativo. Hoy hay código nuestro que probablemente sobre: la limpieza de texto `to_speech` y la de transcripción `clean_transcript`. ElevenLabs puede tener normalización de texto y opciones de Scribe que lo reemplacen; eso se confirma en el relevamiento.
- **Después**, el wizard de audio reutilizando `core/runs/` y `components/wizard/`:
  - **STT:** audio → transcripción con tiempos, hablantes y todo lo que dé Scribe → resultado y métricas → **sumar la transcripción a una biblioteca**. Se revisa el tope actual de 3 minutos, que hoy aplica a las grabaciones con el micrófono: el MP3 dura unos 10 minutos.
  - **TTS:** texto → voz (manual: elegís la voz y los ajustes; automático: a definir según lo que ofrezca ElevenLabs) → síntesis → resultado y métricas.

**Listo cuando:** el MP3 de la presentación queda transcripto y sumado a "BYMA 3T26", y el chat puede responder con lo que **se dijo** en la presentación y con lo que está **escrito** en los PDFs.

### Fase 6 · Cierre para la clase
- Revisar todos los README y comentarios.
- Dejar listas las corridas y la biblioteca "BYMA 3T26" en `data/`.
- Escribir un guion corto para la demo: qué mostrar en cada paso y qué preguntarle al chat.
- Correr todo con Docker, de punta a punta.

---

## 9. Roadmap (después de la clase)

- **Pasar la carpeta-DB a `agent_data`.** Es la base JSON nativa de LlamaCloud, con búsqueda, filtros y agregaciones. Hoy elegimos la carpeta para que la demo funcione sin conexión y los archivos se puedan abrir a mano.
- **Verify** (`alpha.verify`): detectar si un documento fue adulterado. Lo sumamos cuando salga de alpha.
- **Webhooks:** que LlamaCloud avise cuando termina un job o un lote, en lugar de consultar. Solo sirve con el servidor publicado en internet.
