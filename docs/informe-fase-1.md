# Informe · Fase 1: mejoras al pipeline de documentos

**Fecha:** 13/11/2026 · **Base:** commit `41e0666` (fase 0, reorganización) · **SDK:** `llama-cloud` 2.19.0

## Criterios

1. **Solo lo nativo.** No implementamos nada que LlamaCloud, LlamaIndex o LlamaParse no hagan de forma nativa. Si la plataforma lo resuelve, se usa la plataforma.
2. **Todo lo posible en cada paso.** Cada paso pide a LlamaCloud la mayor cantidad de información que ofrece, la **guarda**, la **mide** y la **interpreta** para mostrarla en clase.
3. **Código simple** y documentado en español.

---

## 1. Lo que ofrece cada producto (y lo que hoy no usamos)

Relevamiento hecho sobre los tipos del SDK, que se generan a partir de la API reference.

### Parse (`parsing`): hoy no lo usamos directamente

Extract parsea por dentro, pero ese resultado no lo guardamos. Parse es el paso que más información da.

| Qué se puede pedir (`expand`) | Qué trae |
|---|---|
| `markdown` / `markdown_full` | El Markdown por página, con encabezado, pie y números de línea |
| `text` / `text_full` | El texto plano por página |
| `items` | La estructura de cada página (títulos, tablas, párrafos) **con cajas**, más las revisiones (texto tachado o corregido) |
| `metadata` | Por página: confianza, orientación original, número de página impreso, marca de agua, si se activó el *auto mode*, si se optimizó el costo. Para todo el documento: confianza total y la página peor puntuada |
| `forms` | Los formularios detectados, con su tipo |
| `images_content_metadata` | Las imágenes extraídas, con categoría, caja y URL de descarga |
| `job_metadata`, `usage` | Detalles del procesamiento y **créditos cobrados** |

Opciones útiles al crear el job: `tier` (fast, cost_effective, agentic, agentic_plus), `version` (fecha fija para que los resultados sean reproducibles), `agentic_options.custom_prompt`, `input_options.image.camera_photo_correction` (corrige fotos sacadas con el celular), `output_options` (tablas como Markdown o como planilla, `granular_bboxes`, `images_to_save`, número de página impreso, manejo de marcas de agua), `processing_options` (OCR por idioma, extracción agresiva de tablas, gráficos, formularios, `confidence_score_effort`, `cost_optimizer`) y `page_ranges.max_pages`.

### Split (`split`): no lo usamos

- **Entrada:** el parse ya hecho (`pjb-...`), así no se vuelve a leer el documento.
- **Configuración:** las `categories` y la `splitting_strategy` (instrucciones propias, mínimo de páginas por segmento, si permite "sin categoría").
- **Salida:** `result.segments`, los segmentos con su categoría y su rango de páginas.

### Classify (`classify`): no lo usamos

- **Entrada:** el parse ya hecho (`pjb-...`).
- **Configuración:** las `rules`, cada una con un tipo y una descripción.
- **Salida:** `type`, `confidence` y **`reasoning`**, la explicación del modelo de por qué eligió ese tipo. Sirve directo para la interpretación.
- **Costo:** `usage.credits` y `usage.parse_credits`.

### Extract (`extract`): lo usamos a medias

| Lo que hay | Hoy |
|---|---|
| `file_input` acepta el parse ya hecho (`pjb-...`) | ❌ Le pasamos el archivo, así que **vuelve a parsear** |
| `configuration_id`: una configuración guardada (las plantillas de schema) | ❌ El schema está escrito en el código |
| `generate_schema` y `validate_schema` | ❌ (es la fase 2) |
| `cite_sources` y `confidence_scores` | ✅ |
| `advanced_citations` | ❌ |
| `field_metadata.page_metadata` y `row_metadata` (metadata por página y por fila) | ❌ Solo leemos `document_metadata` |
| `extraction_target` (`per_doc`, por página, por fila) | Solo `per_doc` |
| `usage` (créditos de extract y de parse) | ❌ No lo mostramos |
| `extract_metadata.parse_job_id` | ❌ |

### Configurations (`configurations`): no lo usamos

Guarda configuraciones con nombre para cualquier producto: crear o actualizar, listar, borrar y versiones. **Ahí van las plantillas de schema** (manuales o generadas por el agente), en lugar de una carpeta nuestra.

### Index y retrieval (`beta.directories`, `indexes`, `retrieval`): no lo usamos

- **Cómo se arma:** se crea un directorio, se sube el archivo y se crea el índice. Con `store_attachments: ["screenshots", "items"]` guarda además capturas de cada página e items con cajas.
- **Cómo se busca:** `retrieval.retrieve` hace búsqueda **híbrida** (vector más texto completo) con rerank. Cada resultado trae `content`, `score`, `rerank_score`, el rango de páginas, la posición del chunk y la cantidad de tokens.
- **Otras operaciones:** `find` (buscar por nombre de archivo), `grep` (buscar con regex en el texto parseado) y `read` (leer el texto).

### Chat (`chat`): no lo usamos y es **fundamental**

- **Cómo funciona:** se crea una sesión atada al índice y `chat.stream` devuelve los eventos de cada turno.
- **Qué eventos trae:** el texto de la respuesta, el **razonamiento** (`thinking`), las **llamadas a herramientas** (`tool_call`: qué búsquedas hizo el agente) con su resultado (`tool_result`, a veces con la captura de la página).
- **Métricas:** duración, tokens de entrada y salida, cantidad de turnos (`job_metadata`).
- **Para la clase:** se puede mostrar **cómo piensa y busca** el agente antes de responder, no solo la respuesta.

---

## 2. Hallazgos sobre el código actual

Prioridad: 🔴 alta (contradice los criterios o pierde información) · 🟡 media · 🟢 baja.

### Backend

| # | Prio | Dónde | Hallazgo | Propuesta |
|---|---|---|---|---|
| 1 | 🔴 | `steps/extract.py` | Extract recibe el archivo y parsea de nuevo. No queda un parse reutilizable y se pagan dos parseos si sumamos los otros pasos. | Parsear una vez (paso Parse) y pasarle el `pjb-...` a Split, Classify y Extract. |
| 2 | 🔴 | `steps/postprocess.py` → `clean_amount`, `EMPTY_WORDS` | Es limpieza hecha a mano: asteriscos de los importes y "null" escrito como texto. La plataforma lo resuelve. | **Eliminar.** Usar tipos de verdad en el schema (`number` para importes, `null` permitido) y la guía de cada campo en su `description`. |
| 3 | 🔴 | `schema.py` | El schema está escrito en el código: 10 campos fijos, todos de texto. | Fase 2: el editor de campos y `generate_schema`, todo guardado en `configurations`. |
| 4 | 🔴 | `steps/postprocess.py` → `normalize_result` | Descarta todo lo que no esté en los 10 campos fijos. Con un schema dinámico se pierde información. | **Eliminar.** Guardar `extract_result` tal cual lo devuelve LlamaExtract. |
| 5 | 🔴 | `steps/cleanup.py` | Borra el archivo y el job apenas termina. No queda nada para mostrar ni para indexar. | Borrar solo con el botón "Eliminar corrida". |
| 6 | 🟡 | `steps/postprocess.py` → `field_confidence`, `citation_boxes` | Leen solo `document_metadata` y recortan con topes inventados (20 citas, 200 cajas). | Guardar la metadata completa (`document_metadata`, `page_metadata`, `row_metadata`). Solo queda nuestra la conversión de cajas a fracciones, que hace falta para dibujarlas. Activar `advanced_citations`. |
| 7 | 🟡 | `steps/validate.py` → `pdf_page_count` (pypdf) | Contamos las páginas nosotros para rechazar los PDFs largos. | Usar `page_ranges.max_pages` de Parse, que es nativo, y sacar la dependencia `pypdf`. Solo queda la validación mínima de tipo y tamaño, para no gastar en archivos que no son documentos. |
| 8 | 🟡 | `settings.py` | `extract_version="latest"`: el resultado puede cambiar de una clase a la otra. | Fijar la versión (Parse ya publica `2026-10-16`, `2026-09-28`, …; `parsing.list_versions` dice cuáles hay) y mostrarla en la UI. |
| 9 | 🟡 | `jobs.py` | Los tickets viven en memoria y se pierden al reiniciar. | Reemplazarlo por las corridas en `data/documents/runs/`. |
| 10 | 🟡 | Todos los pasos | No se guarda ni se muestra lo que cuesta cada paso. | Guardar `usage` de cada job y mostrar los créditos en cada panel, más el total de la corrida. |
| 11 | 🟢 | `router.py` | El límite diario por IP tiene sentido en producción, no tanto en una demo local. | Dejarlo, pero desactivado por defecto en la demo (`DOCUMENTS_DAILY_LIMIT=0`). |

### Frontend

| # | Prio | Dónde | Hallazgo | Propuesta |
|---|---|---|---|---|
| 12 | 🔴 | `InvoiceExtractor.tsx` → barra de progreso | La barra es **simulada**: una curva de tiempo con etapas inventadas ("Lectura", "Validación"). No dice qué está pasando de verdad. | Reemplazarla por el estado real de cada job en el wizard (PENDING, RUNNING, COMPLETED). |
| 13 | 🟡 | `invoice.ts` → `invoiceCsv`, `invoiceMarkdown` | Arman CSV y Markdown en el navegador. | Descargar los archivos que ya guardó cada paso: el `.md` del parse y el `.json` del extract. Menos código. |
| 14 | 🟡 | `PdfPreview.tsx` (pdfjs) | Dibuja el PDF en el navegador con una librería de 335 KB. | Probar si las capturas de página de Parse o del índice alcanzan (`images_to_save`, `store_attachments: ["screenshots"]`) y, si alcanzan, sacar `pdfjs`. **Hay que verificarlo.** |
| 15 | 🟢 | `invoice.ts` → `invoiceSpeech` | El resumen hablado se arma con 5 campos fijos. | Se revisa en la fase de audio. |

### Tests

| # | Prio | Hallazgo | Propuesta |
|---|---|---|---|
| 16 | 🟡 | La mitad de los tests prueba la limpieza hecha a mano, que se va a eliminar (#2, #4). | Borrarlos junto con ese código. Probar lo que sigue siendo nuestro: las corridas en carpeta, la conversión de cajas, las rutas y el orden de los pasos con un cliente falso. |

---

## 3. Cómo se aplica "extraer todo, guardar, medir, interpretar"

Cada paso del wizard guarda **la respuesta completa de LlamaCloud** (`response.json`) y, aparte, sus archivos principales: el `.md`, los segmentos, el resultado. Las métricas salen solo de esos datos, sin llamadas extra:

| Paso | Qué se guarda | Qué se mide | Qué se interpreta |
|---|---|---|---|
| Parse | markdown, text, items, metadata, forms, imágenes, usage | Páginas, palabras, tablas, imágenes, confianza por página, créditos, tiempo | "La página 2 tiene la confianza más baja (0,71): conviene revisarla". También se señala si hubo marca de agua o si se rotó la página. |
| Split | segments | Cantidad de segmentos y páginas de cada uno | Qué partes encontró y de qué tipo es cada una |
| Classify | type, confidence, reasoning, usage | Confianza y créditos | El `reasoning` del modelo, tal cual |
| Schema | la configuración (manual o del agente) y su validación | Cantidad de campos y tipos | Qué propuso el agente y en qué se diferencia del schema manual |
| Extract | result, metadata completa, usage | Campos encontrados y vacíos, confianza promedio, mínima y máxima, cantidad de citas, créditos | Qué campos revisar (confianza baja) y de qué parte del documento salió cada dato |
| Index | el índice, los chunks y las consultas de prueba | Cantidad de chunks y tokens por chunk | Cómo se partió el documento y qué chunks se recuperan para cada pregunta |
| Chat | todos los eventos de cada turno | Tokens, duración, herramientas usadas | Qué buscó el agente, qué encontró y cómo respondió |

**La interpretación** es un texto didáctico fijo por paso ("qué hace este paso") más frases armadas con los datos que devolvió la API. No se usa un LLM extra.

---

## 4. Plan que sigue

1. **Fase 2, schema manual o automático.** El editor de campos con tipos, `generate_schema` y `validate_schema`, y las plantillas guardadas en `configurations`. Resuelve los hallazgos #2, #3 y #4.
2. **Fase 3, el wizard.** Los pasos Subir → Parse → Split → Classify → Schema → Extract → Index → **Chat**, las corridas en `data/documents/runs/` y un panel por paso con lo guardado, lo medido y lo interpretado. Resuelve #1, #5 a #10, #12 a #14 y #16.
3. **Fase 4, audio.** La misma metodología con ElevenLabs.

## 5. Roadmap (más adelante)

- **Pasar la carpeta-DB a `agent_data`.** LlamaCloud tiene una base JSON nativa (`beta.agent_data`) con búsqueda, filtros y agregaciones. Las corridas se guardarían en LlamaCloud en lugar de en `data/`. Hoy elegimos la carpeta para que la demo funcione sin conexión y se puedan abrir los archivos a mano.
- **Verify** (`alpha.verify`): detecta si un documento fue adulterado. Es alpha; lo sumamos cuando salga de alpha.
- **Webhooks** (`webhook_configs`): avisarían cuando termina un job, en lugar de consultar. Solo sirven con el servidor publicado en internet.

## 6. Lo que hay que verificar con llamadas reales

1. Si el índice nuevo permite **listar todos los chunks** de un documento, o solo los que devuelve `retrieve`.
2. Qué valores acepta `images_to_save` y si las capturas de página alcanzan para dibujar las cajas de las citas (#14).
3. Si Split devuelve `usage`, porque en el tipo de respuesta no aparece.
4. Cuántos créditos cuesta una corrida completa con la factura de ejemplo, para saber cuánto sale cada demo en clase.
