# Bitácora del proyecto

Registro de todo lo que se hizo, se probó, se encontró y se gastó, para poder auditarlo.

- **Las entradas van en orden cronológico.** Cada una dice qué se hizo, qué salió, qué se encontró y qué se decidió.
- **Cada llamada paga** a LlamaCloud o ElevenLabs queda en el [registro de créditos](#registro-de-créditos).
- **Los datos crudos de cada prueba** (lo que se pidió y la respuesta completa) quedan en `backend/data/verificacion/` o en la corrida correspondiente de `backend/data/documents/runs/`. Están fuera de git porque pesan mucho y las respuestas traen links firmados temporales.

---

## Registro de créditos

Saldo inicial informado: **29.443** de 30.000, el 13/11/2026. Las horas están en horario argentino (UTC−3) y salen del `created_at` de cada job.

| # | Fecha | Qué | Documento | Job | Opciones | Créditos | Saldo estimado |
|---|---|---|---|---|---|---|---|
| 1 | 13/11 13:45 | Parse (verificación 1) | Comunicado, 10 págs. | `pjb-s4z0opy7i3qk91v52qsm2tk8okel` | agentic · todas las opciones | 210 | 29.233 |
| 2 | 13/11 16:54 | Parse desde el wizard | Presentación, 15 págs. | `pjb-s5617m4umqypr1wpme452lkzdxxq` | agentic · todas las opciones | 585 | 28.648 |
| 3 | 13/11 17:06 | Split (verificación 2) | Comunicado, sobre el parse #1 | — | 5 categorías | **0: rechazado** (error 400 por `max_pages`) | 28.648 |
| 4 | 13/11 17:06 | Classify (verificación 2) | Comunicado, sobre el parse #1 | `clj-xiadt3fgnwwvbvme9coidg8z3yhz` | 4 reglas, modo FAST | **no informado** (`usage: null`) | ? |
| 5 | 13/11 17:07 | Generate schema + validate + guardar configuración | Comunicado (`file_id`) | `cfg-robwbsz63f6isxhbrowp4elqc90g` | con indicación en español | **no informado** | ? |
| 6 | 13/11 17:07 | Extract (verificación 2) | Comunicado, sobre el parse #1 | `ext-193ly7aasemdt4j1fevfd6c1sg9m` | configuración #5 · agentic · citas y confianza | **no informado** (`usage: null`) | ? |
| 7 | 13/11 17:08 | Parse de 1 página, todas las opciones | EEFF, página 4 | `pjb-a9ctaro0h54b33zmwq9geim6mhh9` | agentic · todas | 15 | −15 |
| 8 | 13/11 17:08 | Parse de 1 página, sin gráficos IA ni confianza "high" | EEFF, página 4 | `pjb-6h37rk3t3zsz9h94iz6x71fapfak` | agentic · sin 2 opciones | 10 | −10 |

| 9 | 13/11 17:15 | Parse de 1 página con el pedido final (con `additional_outputs`) | EEFF, página 4 | `pjb-97ekchfjv49nwhxn1jqxcyb2llh0` | agentic · todas + 3 salidas extra | 15 | — |
| 10 | 13/11 17:17 | **Parse completo desde el wizard** | **EEFF, 86 págs.** | `pjb-skkwahpft8n75q9osbrctxpvyn6b` | agentic · todas + 3 salidas extra · sin `max_pages` | **1.310** | — |

**Conciliación con el panel de LlamaCloud (13/11, antes de #9):** el usuario informó **28.463**. Lo conocido hasta #8 sumaba 820, lo que daba 28.623 esperado. La diferencia, **160 créditos**, es lo que cobraron **juntos** Classify (#4), Generate schema (#5) y Extract (#6), que no informan `usage`.

| 11 | 13/11 17:24 | Parse de nuevo, con el pedido final, desde el wizard | Comunicado, 10 págs. | `pjb-jtmlf3lmvd4kjbw2g6rhtc07q58p` | agentic · todas + 3 salidas extra · sin `max_pages` | 210 | — |
| 12 | 13/11 17:25 | Parse de nuevo, con el pedido final, desde el wizard | Presentación, 15 págs. | `pjb-io2lmikjekdgmo6r7e3u97gkc89e` | agentic · todas + 3 salidas extra · sin `max_pages` | 585 | — |

**Saldo estimado después de #12:** 28.463 − 15 − 1.310 − 210 − 585 = **26.343**. Hay que confirmarlo con el panel.

Repetir un parse **no** usa caché: #11 y #12 cobraron lo mismo que #1 y #2.

**Prueba real de la fase 3 en los EEFF** (sobre el parse #10, sin volver a leer el documento):

| # | Fecha | Qué | Documento | Job | Opciones | Créditos | Saldo estimado |
|---|---|---|---|---|---|---|---|
| 13 | 13/11 19:46 | Split desde el wizard | EEFF, 86 págs. | `spl-zjhcnd2v4rvltbjybamgsy4zhxfg` | 7 categorías de estados financieros · `include` | **no informa** (hay que mirarlo en el panel) | ? |
| 14 | 13/11 19:47 | Classify desde el wizard | EEFF | `clj-yonw8z4ffmegkxtx07rif4w7srlo` | 4 reglas · FAST · `expand=usage` | **0** (informado: `credits: 0.0`) | — |
| 15 | 13/11 19:47 | Schema manual: validar y guardar | EEFF | `cfg-kjttpzbm0quqlynf6o2hm2mg48ln` | plantilla "Resultados trimestrales" | no informa (validar y guardar no cobraban antes) | — |
| 16 | 13/11 19:47 | Extract sobre la parte «estado_de_resultados» | EEFF, página 4 | `ext-5pys8mwxjblusy937p3f9sp39856` | configuración #15 + `target_pages: "4"` | **15** (`extract_credits: 15.0`) | — |

**Comparación de schema manual contra automático en el comunicado** (sobre el parse #11):

| # | Fecha | Qué | Documento | Job | Opciones | Créditos | Saldo estimado |
|---|---|---|---|---|---|---|---|
| 17 | 13/11 20:11 | Split | Comunicado, 10 págs. | `spl-3nnb029laeo750vd39iev3zuzu1e` | 5 categorías de comunicado | **no informa** | ? |
| 18 | 13/11 20:11 | Classify | Comunicado | `clj-gh98j8aavgog0o8oxirggwp9yx1a` | 4 reglas | **0** | — |
| 19 | 13/11 20:11 | Schema manual | Comunicado | `cfg-9ft6h0k6apx7j3x8nj3aq22qvxaw` | plantilla "Resultados trimestrales" | no informa | — |
| 20 | 13/11 20:11 | Extract con el schema manual | Comunicado, todo | `ext-wg2nii8ypgsesep0dhytnsk2dirv` | configuración #19 | **150** | — |
| 21 | 13/11 20:12 | Schema automático (`generate_schema`) | Comunicado (`file_id`) | `cfg-tloj0e9e26i9ewkaq4fi80yxtg4r` | con indicación en español | **no informa** | ? |
| 22 | 13/11 20:12 | Extract con el schema automático | Comunicado, todo | `ext-7h3ycvz9w2aj5l7vkb1gooqyi76k` | configuración #21 | **150** | — |

Extract cuesta **15 créditos por página** (agentic, con citas y confianza): 1 página → 15, 10 páginas → 150, sin importar cuántos campos tenga el schema (11 o 37).

**Prueba chica de la fase 4:**

| # | Fecha | Qué | Documento | Job | Opciones | Créditos | Saldo estimado |
|---|---|---|---|---|---|---|---|
| 23 | 13/11 20:40 | Parse desde el wizard | Factura de ejemplo, 1 pág. | corrida `2026-11-13_204022_factura-ejemplo` | agentic · todas + 3 salidas extra | 15 | — |
| 24 | 13/11 20:40 | Crear el directorio de la biblioteca "Prueba chica" | — | — | — | **0: rechazado** (403, plan) | — |

**Llamadas que no costaron nada** (comprobado): volver a pedir el resultado de un parse terminado (`parsing.get`, varias veces), `validate_schema`, `configurations.create` (dos configuraciones de parse: `cfg-lhr7sirebo2m6rhmyx9dc89bk9xy` y `cfg-bmherk6gqi5cmvozygan96hjlel5`) y la subida de archivos. Las 3 salidas extra de `additional_outputs` tampoco suman costo: la página 4 costó 15 con y sin ellas.

---

## Entradas

### 13/11 · Fase 0 · Reorganización (commits `585317e`, `41e0666`)
- **Qué se hizo:**
  - `git init` y un commit con el estado original.
  - Cada pipeline quedó entero en su carpeta (`backend/app/pipelines/documents` y `audio`), con su configuración, cliente, pasos y rutas.
  - El frontend quedó con la misma forma.
  - Un comentario en rioplatense arriba de cada función y un README por pipeline.
- **Resultado:** 25 tests pasan y no cambió el comportamiento.
- **Cambios en el `.env` del usuario:** `INVOICE_DAILY_LIMIT` pasó a llamarse `DOCUMENTS_DAILY_LIMIT`, y `TTS_CACHE_DIR` ahora apunta a `data/audio/cache`.

### 13/11 · Fase 1 · Informe (commit `ea47134`)
- **Qué se hizo:** el relevamiento de la API de LlamaCloud a partir del SDK `llama-cloud` 2.19.0, que se genera de la API reference.
- **Hallazgos:** 16 sobre el código de ese momento. Ver [informe-fase-1.md](informe-fase-1.md).
- **Decisiones:**
  - Solo se usa lo nativo de la plataforma.
  - Verify queda afuera porque está en alpha.
  - El chat es fundamental.
  - Los datos van en una carpeta; pasar a `agent_data` queda en el roadmap.

### 13/11 · Plan (commits `d7b806f`, `22cc35e`)
- **Qué se hizo:**
  - El plan completo en [plan.md](plan.md).
  - El usuario sumó los documentos de BYMA (EEFF de 86 págs., comunicado de 10, presentación de 15 y un MP3 de ~10 min). Se movieron a `backend/data/samples/byma/`.
- **Decisiones:**
  - **Bibliotecas:** un índice compartido para chatear con varios documentos, con la posibilidad de agregar o sacar documentos.
  - **Batches** para procesar en lote.
  - El wizard va antes que el schema.

### 13/11 · Verificación 1 · Parse real del comunicado (commit `16eaeee`)
- **Qué se hizo:** un parse del comunicado (10 págs.) pidiendo todas las opciones y todas las salidas. Créditos: ver #1 del registro.
- **Resultado:** 210 créditos y 28 s de espera. Devolvió Markdown, texto, 65 items, confianza por página, 41 imágenes, un Excel con 9 hojas y las cajas por palabra. Detalle en [verificacion-1-parse.md](verificacion-1-parse.md).
- **Hallazgos:**
  - La **página 8** tiene confianza 0,3 por sus dos gráficos.
  - Parse convirtió los gráficos en tablas correctamente.
  - Encontró una **inconsistencia en el documento original**: el texto dice que el margen EBITDA fue 74% y el gráfico muestra 75%.
  - `save_output_pdf` devuelve el mismo PDF, sin cambios.
  - Las imágenes incrustadas son el logo repetido en cada página.
  - `raw_words` no vino, aunque se pidió.
- **Decisiones:** dejar de pedir `save_output_pdf` y las imágenes `embedded`.
- **Datos crudos:** `backend/data/verificacion/2026-11-13_parse-comunicado/`.

### 13/11 · Fase 2 · Motor de corridas, wizard, Subir y Parse (commits `77f3793`, `1024b4f`)
- **Qué se hizo:**
  - `core/runs/store.py` (la carpeta-DB), los pasos `s1_upload` y `s2_parse`, y las rutas `/api/documents/runs/...`.
  - En el frontend: el stepper, el panel de paso, los visores y la lista de corridas.
  - Se eliminó el flujo viejo de extracción, junto con `pypdf` y `pdfjs`.
- **Prueba sin costo:** se armó una corrida con los datos de la verificación 1 y se recorrió en Chrome headless, en escritorio y en teléfono. No hubo errores.
- **Prueba real:** la presentación (15 págs.) desde la pantalla. Créditos: ver #2 del registro.
- **Resultado:**
  - Terminó en 83 s, con 12 consultas cada ~3 s y sin errores.
  - Encontró 24 tablas, 18 de ellas gráficos convertidos en datos.
  - La confianza del documento fue 89%; las páginas 6 y 12 quedaron para revisar.
- **Hallazgos:**
  - **El costo depende de los gráficos:** 39 créditos por página contra 21 del comunicado. La estimación de ~315 quedó corta.
  - La descarga de imágenes de a una tardaba 46 s. Se pasó a paralelo y ahora tarda ~10 s.
  - El ID del archivo es un UUID, no empieza con `dfl-` como se creía.
- **Tests:** 19 pasan.
- **Datos crudos:** las corridas `2026-11-13_164319_byma-comunicado-de-prensa-3t26` (armada sin costo) y `2026-11-13_165433_presentacion-de-resultados-3t26` (real).

### 13/11 · Verificación 2 · Split, Classify, Schema automático, Extract y costo por página
- **Qué se hizo:** se encadenaron los pasos de la fase 3 sobre el **parse ya hecho del comunicado** (`pjb-...`), sin volver a mandar el documento. Créditos: #3 a #8 del registro. Detalle en [verificacion-2-fase3.md](verificacion-2-fase3.md).
- **Hallazgos:**
  - 🔴 **Split no acepta un parse hecho con `max_pages`.** Error 400: *"split results number pages relative to the full document"*. Nuestro paso Parse mandaba siempre `max_pages=100`.
  - **Classify y Extract sí aceptan ese parse.** Classify acertó (`comunicado_de_prensa`, 95%) en 10 s, con un razonamiento muy claro.
  - **`generate_schema` funciona, pero sus valores por defecto son pobres:** propone campos en inglés (aunque la indicación estaba en español), con tier `cost_effective` y sin citas ni confianza. Su API pide el `file_id`, no el parse.
  - **Extract** sacó todos los números principales correctos (comparados contra el documento) en 27 s. Las citas vienen en la misma escala que las capturas de página (612 × 792): se pueden dibujar sobre ellas sin `pdfjs`.
  - **Classify, Generate schema y Extract no informan créditos** (`usage: null`).
  - **Costo por página:** en una página de tablas de los EEFF, todas las opciones cuestan 15 créditos y sin las dos más caras, 10. El contenido es el mismo (95 números idénticos); solo cambia la confianza informada (1,0 contra 0,6).
- **Decisiones:**
  - Sacar `max_pages` del paso Parse, para que siempre se pueda usar en Split. Ya está corregido.
  - Mantener la confianza "high" por defecto, porque es la base de la interpretación.
  - Ofrecer en el wizard las opciones caras como interruptores, para mostrar en clase cuánto cambia el costo.
  - Al guardar un schema generado, forzar citas, confianza y tier `agentic`.
- **Estimación nueva para los EEFF (86 págs.):** entre ~860 y ~1.290 créditos.
- **Datos crudos:** `backend/data/verificacion/2026-11-13_fase3/` (split, classify, schema, extract, eeff_pagina).

### 13/11 · Pedido final de Parse y parse completo de los EEFF
- **Pedido del usuario:** aprovechar LlamaParse al máximo y no tener que volver a parsear. El proyecto tiene que quedar como plantilla.
- **Qué se revisó antes de gastar:** la documentación de **todas** las opciones de Parse, sacada del SDK.
- **Lo que se encontró en esa revisión:**
  - `raw_words` no venía porque hay que pedirlo con `additional_outputs: ["word_bbox"]`. Hay dos salidas extra más: `stripped_md` (texto sin formato por página, para búsqueda) y `concatenated_stripped_txt` (todo el texto en un archivo, para embeddings).
  - `confidence_score_effort: "high"` cuesta **+5 créditos por página**. Explica el 15 contra 10 de la verificación 2.
  - Con la lista completa de `expand`, LlamaCloud también entrega texto, Markdown, items, metadata y formularios **como archivos descargables**. Así no se pierde nada en documentos largos.
  - La configuración de parse (`parse_v2`) admite todas las opciones y **el índice puede usarla** (`product_config_id`).
- **Cambios en el paso Parse:**
  - Se agregaron las 3 `additional_outputs` y la lista completa de `expand`.
  - Se bajan **todos** los archivos descargables, incluidos los desconocidos, que van a `archivos/`.
  - Se guarda el pedido como configuración en LlamaCloud y su ID queda en `run.json`.
- **Validación antes de gastar:**
  - Gratis: se volvió a pedir el comunicado con el `expand` nuevo y se guardó la configuración.
  - Con 15 créditos: una página con el pedido final (#9). Salieron los 10 archivos descargables, incluido `raw_words`.
- **Parse completo de los EEFF desde el wizard (#10):**
  - 1.310 créditos (15 por página), 32,7 s de procesamiento y 82 s en total, sin errores.
  - Confianza del documento: **98%**.
  - 119 tablas, 313 títulos, 35.123 palabras.
  - 195 imágenes y 101 MB guardados.
- **Hallazgos:**
  - **La página 43 tiene 65% y LlamaParse no dice por qué.** Se revisó a mano: es texto, la nota 39 de hechos posteriores, y el Markdown está completo, con firmas incluidas. La interpretación decía *"suele pasar en páginas con gráficos"*: **era una frase inventada nuestra y estaba mal**. Se reemplazó por *"LlamaParse no informa el motivo; compará su captura con el Markdown"*.
  - **Tablas unidas entre páginas** (`merged_from_pages`): 6 en los EEFF (páginas 6–7, 35–36, 37–38, 62–64, 65–66, 70–71).
  - **Dudas propias de LlamaParse** (`parse_concerns`, en cada tabla): 7 tipos encontrados en los 3 documentos. `multi_table_page` es solo un aviso. Las otras son para revisar: `header_value_type_mismatch` (por ejemplo, en la página 17 de los EEFF la columna "Total" tiene un texto), `header_row_in_body`, `inconsistent_row_cell_count`, `possible_merged_columns`, `multi_color_table_text` y `layout_lvm_disagreement`.
- **Cambios en la interpretación:**
  - Se suman las métricas "Tablas unidas entre páginas" y "Dudas de LlamaParse para revisar".
  - Hay una frase por cada tipo de duda, con sus páginas.
  - Se corrigieron los plurales.
  - Se recalculó la interpretación de las 3 corridas a partir de lo guardado, sin llamadas.
- **Datos crudos:** `backend/data/verificacion/2026-11-13_fase3/validacion_gratuita/` y `eeff_pagina_pedido_final/`, más la corrida `2026-11-13_171702_byma-eeff-30-09-2026-vf`.

### 13/11 · Se vuelven a parsear el comunicado y la presentación con el pedido final
- **Pedido del usuario:** que los 3 documentos queden parseados con los ajustes actuales.
- **Qué se hizo:** los dos parses desde el wizard (#11 y #12), 795 créditos en total. Las corridas viejas **no se borraron**: quedan para comparar.
  - Corridas nuevas: `2026-11-13_172416_byma-comunicado-de-prensa-3t26` y `2026-11-13_172453_presentacion-de-resultados-3t26`.
  - Corridas viejas: `…164319_byma-comunicado…` y `…165433_presentacion…`.
- **Resultado:** las dos traen los 10 archivos descargables, `raw_words` incluido, y sirven para Split. Tardaron 14 y 18 s de procesamiento.
- **Hallazgos:**
  - 🔴 **El parse no es determinístico.** Mismo archivo, misma versión fija (`2026-10-16`) y mismas opciones, y el resultado cambia:
    - **Comunicado:** la confianza de la página 8 (los gráficos) pasó de 0,30 a **1,00**, y la del documento de 93% a 100%. El contenido es igual; solo falta un "639" del logo.
    - **Presentación:** la confianza pasó de 89% a 91% (las páginas 5 y 9, de 0,85 a 1,00). En varias tablas cambió solo el formato de los números (`12,467` → `12467`).
  - 🔴 **El parse viejo había inventado valores de un gráfico.** En la página 5 de la presentación, la serie "Datos de Mercado" del gráfico dice 250, 232, 973, 354, 291, 300… (se comprobó en la captura). El parse nuevo los leyó bien. El viejo había puesto **1.350, 1.203, 1.457, 1.679, 966**, que no aparecen en el gráfico.
  - **Lección para la clase y para la plantilla:** los datos que vienen de gráficos leídos con IA hay que verificarlos contra la captura. La confianza por página no siempre lo avisa: la página 5 vieja tenía 0,85 con valores inventados.
  - **LlamaCloud versiona las configuraciones solo.** Cada `configurations.create` con el mismo nombre crea una versión nueva con otro ID; hay 4 versiones de `parla-parse-agentic-2026-10-16`. `configurations.list(latest_only=True)` devuelve la última. Cada corrida guarda el ID de la versión que usó.

### 13/11 · Investigación · Identidad entre documentos y evals (sin costo)

- **Identidad de entidades** (que "BYMA" y "Bolsas y Mercados Argentinos" sean la misma empresa): LlamaCloud **no tiene una función nativa** de entity resolution. Ni el SDK 2.19.0 ni la documentación muestran un endpoint para esto. Lo más cercano es Extract: un schema con un campo normalizado (por ejemplo `ticker`) hace que cada documento devuelva el mismo valor, y así se pueden comparar.
- **Identidad de documentos** (el mismo archivo subido dos veces): `files.create` no deduplica. Cada subida es un archivo nuevo con otro ID. En los directorios (`beta.directories.files`) existe `unique_id`: si no se manda, se usa `external_file_id` o el nombre del archivo. Queda por probar en la fase 4 qué pasa al subir dos veces el mismo `unique_id` al mismo directorio.
- **Evals:** el SDK no tiene endpoints de evaluación. LlamaIndex publicó **ParseBench** (arXiv 2604.08538): unas 2.000 páginas verificadas a mano y 5 dimensiones (tablas, gráficos, fidelidad del contenido, formato semántico y grounding visual). Según el paper, LlamaParse Agentic queda primero con 84,88% general y 78,1 en gráficos, la dimensión más floja. El benchmark es de LlamaIndex mismo, y un competidor (Extend) cuestiona la comparación.
- **Nuestras evals:** los 19 tests prueban el código con un cliente falso, no la calidad del parse. La calidad se verificó **a mano** en las verificaciones 1 y 2: 8 cifras de Extract y la página 5 de la presentación contra la captura.
- **Herramientas nativas contra la alucinación** (revisado en el SDK 2.19.0):
  - **`alpha.verify` no sirve para esto.** Es un análisis forense del documento: integridad, metadatos, detección de adulteraciones. No controla si una respuesta de IA está inventada.
  - **El chat muestra de dónde saca cada respuesta.** El stream emite eventos `tool_call` y `tool_result`, con los fragmentos recuperados y `image_attachment`, la captura de la página.
  - **`retrieval` acepta `custom_filters`** sobre metadata propia de cada archivo. Sirve para dar identidad a cada documento (por ejemplo, "emisor: BYMA").

### 13/11 · Fase 3 · Código de Split, Classify, Schema y Extract (sin costo: probado con el cliente falso)

- **Pasos nuevos:** `s3_split.py`, `s4_classify.py`, `s5_schema.py`, `s6_extract.py`, más `jobs.py` con lo que comparten (consultar el job y leer las opciones). Las opciones del wizard (categorías, reglas, schema, páginas) viajan en el cuerpo del `POST /steps/{paso}`.
- **Cajas sobre las capturas:** en Parse, una caja por cada elemento identificado (título, texto, tabla, imagen), con su tipo y confianza. En Extract, la caja de la cita de cada campo, verde o roja según la confianza, más los campos **sin cita** marcados aparte: son los que no se pueden ubicar en el documento.
- **Hallazgos al leer el SDK 2.19.0:**
  - **Classify y Extract sí informan créditos con `expand=["usage"]`.** En la verificación 2 no lo pedimos y por eso vino `usage: null`.
  - **Classify sobre un parse ya hecho no cobra aparte.** Lo dice la documentación del tipo `Usage`: *"A job run on a parse job you created bills nothing of its own"*.
  - **En Extract, `usage.credits` incluye el parse que usó.** Lo propio de Extract está en `usage.extract_credits`, y eso es lo que se registra.
  - **`allow_uncategorized` de Split no es sí/no.** Es `include`, `omit` o `forbid`. En la verificación 2 mandamos `true`, aunque falló antes por el `max_pages`.
  - **Split y Classify también se guardan como configuración nativa** (`split_v1` y `classify_v2`), igual que Parse y Extract.
  - **`extract.create` con `configuration_id` no permite cambiar las páginas.** Para usar una parte del Split se copia la configuración guardada y se le agrega `target_pages`.
- **Corridas viejas:** se abren con los pasos nuevos como pendientes, sin migrar nada.
- **Tests:** 20, todos pasan. Uno nuevo recorre Split → Classify → Schema (automático y manual) → Extract sobre una parte del Split.

### 13/11 · Fase 3 · Prueba real en los EEFF (registro de créditos #13 a #16)

- **Split acertó en todo:**
  - Asignó las 86 páginas en 15 partes, todas con confianza "high".
  - Encontró **dos juegos de estados**: los consolidados (páginas 1 a 43) y los separados (44 a 78). Se comprobó leyendo los títulos de las páginas 1, 4, 44 y 46.
  - Dividió bien los informes: reseña informativa (79 a 82), comisión fiscalizadora (83 y 84) y auditor PwC (85 y 86).
  - Tardó 12 segundos. No informa créditos.
- **Classify:** `estados_financieros`, 100% de confianza, **0 créditos**. Confirma lo que dice el SDK. El razonamiento enumera los estados, las notas, los informes y la norma (NIIF, NIC 29).
- **Schema manual:** validado y guardado. `format: date` es aceptado.
- **Extract sobre la página 4** (15 créditos), comparado contra el Markdown del parse:
  - `resultado_neto = 22.161.940`. ✅ Es la columna correcta, la del trimestre (01/07 al 30/09/2026), y coincide con los 22.162 millones ajustados del comunicado. La guía del campo decía "valor histórico (sin ajustar)", pero los EEFF solo vienen en moneda constante: el valor es correcto y la guía de la plantilla no aplica a este documento.
  - `razon_social`, `unidad` y `moneda` ✅, con cita.
  - `fecha_de_cierre = "30/09/2026"` ✅, pero **no vino en formato AAAA-MM-DD**, aunque el schema dice `format: date`.
  - `emisor = BYMA` y `periodo = 3T26`: **deducidos, sin cita**, con 45% y 47% de confianza. "BYMA" y "3T26" no aparecen escritos en la página 4. La identidad se resolvió (Bolsas y Mercados Argentinos S.A. → BYMA), y LlamaCloud avisó bien que es una deducción: sin cita y con confianza baja.
  - **`ingresos`, `gastos`, `ebitda` y `margen_ebitda` no los devolvió.** ✅ Es correcto: el estado no tiene renglón de ingresos totales (tiene dos, que sumados dan 81.147.620 = los 81.148 millones del comunicado) ni EBITDA. **No sumó ni inventó**, como pide el `system_prompt`.
- **Corregido:**
  - **El resumen de Extract no contaba los campos que LlamaCloud no devuelve.** Ahora se comparan contra el schema y aparecen como "No los devolvió".
  - **En la tabla de campos,** los campos vacíos mostraban "sin cita" en rojo. Ahora muestran "—".
  - **Redacción:** se cambió "páginas 4" por "página 4" cuando la parte tiene una sola página.
  - Los resúmenes se volvieron a generar a partir de las respuestas guardadas, sin volver a llamar a LlamaCloud.
- **Lección para el schema:** las guías de los campos tienen que servir para el tipo de documento. "Histórico" tiene sentido en el comunicado, que trae los dos valores, pero no en los EEFF.

### 13/11 · Auditoría del proyecto (sin costo)

- **Revisado y bien:**
  - No quedan restos del extractor de facturas viejo (`clean_amount`, `normalize_result`, `pdfjs`…).
  - Ni la `.env` ni las corridas están en el historial de git. Solo están las muestras públicas de BYMA, a propósito (unos 12 MB).
  - `.env.example` no tiene claves.
  - Los tests pasan (20), `ruff` y TypeScript no dan errores y el build del frontend compila.
- **Problemas encontrados y corregidos:**
  1. **Repetir un paso borraba su ejecución anterior** (`step_dir(reset=True)` hacía `rmtree`). Ahora la carpeta se mueve a `historial/<carpeta>_<fecha>`, porque hay que poder auditar todo.
  2. **Repetir un paso dejaba los siguientes con resultados viejos.** Por ejemplo, Extract seguía con las páginas de un Split anterior. Ahora los pasos siguientes vuelven a pendiente y su carpeta pasa al historial.
  3. **Al borrar una corrida quedaban jobs vivos en LlamaCloud:** solo se borraban el archivo y el parse. Ahora se borran también Split, Classify y Extract, incluidos los de ejecuciones anteriores (que quedan en `run.json` → `historial`). El test lo detectó.
  4. **Mientras Schema esperaba al agente** (unos 25 segundos), la pantalla no mostraba nada y se podía apretar el botón dos veces. Ahora muestra "Esperando a LlamaCloud…" y bloquea el botón y los editores.
  5. **Documentación desactualizada:** el plan seguía hablando de `page_ranges`, y los README mostraban solo Subir y Parse. Se actualizaron.

### 13/11 · Fase 3 · Schema manual contra automático en el comunicado (registro de créditos #17 a #22)

- **Split** dividió el comunicado en 5 partes: resumen (1 y 2), estados contables (3 y 10), ingresos (4 a 6) y gastos y eficiencia (7 a 9). **Classify:** comunicado de prensa, 95%, 0 créditos.
- **Schema manual** (11 campos, solo 4 obligatorios): **11 de 11 con valor y con cita**, confianza mínima 82%. Todas las cifras coinciden con el documento (ingresos 78.124, gastos 27.548, resultado neto 52.414, EBITDA 63.036, margen 71%). `fecha_de_cierre` volvió a venir como texto ("30 de septiembre del 2026") y no como AAAA-MM-DD.
- **Schema automático:** el agente propuso **37 campos**, todos en inglés, separados en histórico y ajustado por inflación, y **todos obligatorios**. Extract devolvió 37 de 37 con valor y una confianza promedio de 90%, pero:
  - **8 campos son ceros inventados.** El comunicado **no tiene** EBITDA ni márgenes ajustados por inflación, ni la variación interanual de los márgenes. Como el schema los obligaba, Extract devolvió **0**, con confianza de 0,82 a 0,87. La cita de casi todos es un "0%" que **sí existe** en la página 3, pero en el renglón **"Mercado"** (variación de esos ingresos). Lo vimos dibujando la caja en la captura. El EBITDA ajustado vino directamente **sin cita**.
  - `reportDate = 2026-11-06` es correcto, pero su cita dice «reportDate», el nombre del campo. Ya había pasado en la verificación 2.
  - Las otras 28 cifras son correctas y tienen cita.
- **Comparación de citas contra el texto del parse** (hecha a mano para la auditoría): de los 37 campos, 35 tienen una cita que aparece en el texto de su página, 1 no tiene cita y la de `reportDate` no está en el texto. **Igual no alcanza:** los ceros inventados pasan este control porque "0%" está en la página. Solo la caja sobre la captura muestra que es otro renglón.
- **Lecciones:**
  1. **Un campo obligatorio obliga a Extract a devolver algo, aunque no exista.** Con el schema manual (pocos obligatorios y la regla "null si no consta") no inventó nada, ni en el comunicado ni en los EEFF. Con el automático (todo obligatorio) inventó 8 ceros.
  2. **Una confianza alta y una cita válida no garantizan el dato.** Lo que sí ayuda es ver la caja en la página.
  3. **Al schema automático hay que revisarlo:** traducirlo, sacar "obligatorio" de los datos que pueden faltar y ajustar las guías. El editor ya permite cargarlo y corregirlo en JSON.
- **Cambio en el código:** la interpretación de Schema ahora cuenta los campos **obligatorios en todo su camino**. Cuando todos lo son, avisa: *"si un dato no está en el documento, Extract igual tiene que devolver un valor y puede inventarlo"*. Se volvió a generar sin costo para las dos corridas y tiene 3 tests nuevos (23 en total).
- **Repetir pasos funciona:** al correr el schema automático, el manual y su Extract pasaron solos a `historial/` y quedaron en `run.json`. Se pueden auditar los dos.
- **Detalle de la prueba:** en la captura automática el clic sobre una fila caía en la barra superior fija y no seleccionaba el campo. Es un problema del script, no de la app: con el clic dentro de la página funciona.

### 13/11 · Fase 4 · Relevamiento de bibliotecas, índice, búsqueda y chat (sin costo)

- **SDK 2.19.0:**
  - **Directorios** (`beta.directories`): create, list, get, update, delete.
  - **Archivos de un directorio** (`beta.directories.files`): add (con `file_id`, `metadata` y `unique_id`), upload, list, update, delete.
  - **Índices** (`indexes`): create (`source_directory_id`, `products` con `product_config_id` de parse o extract, `store_attachments` con screenshots e items, `sync_frequency`), get (`expand=sync_in_progress`), sync, cancel_sync, delete.
  - **Búsqueda** (`retrieval.retrieve`): `top_k`, `rerank`, `custom_filters` y `static_filters`, pesos de los modos vectorial y de texto completo.
  - **Chat:** create (hasta 10 índices), stream, retrieve, get_summary, delete.
  - **Lotes** (`batches`): create (`config` y `source_directory_id`), get, list, cancel.
- **Documentación oficial** ([precios](https://developers.llamaindex.ai/llamaparse/general/pricing/), [migración a Index v2](https://developers.llamaindex.ai/llamaparse/cloud-index-v2/migration-v1-to-v2/), [sincronización](https://developers.llamaindex.ai/llamaparse/cloud-index-v2/syncing/)):
  - **Índice:** 2 créditos por página exportada, **1 por búsqueda** y **100 por turno de chat**, además del parse.
  - **Por defecto, un índice parsea con el tier `cost_effective`.** Para usar nuestro parse completo hay que pasarle `product_config_id`.
  - **El sync parsea los archivos nuevos o cambiados** y saltea los que no cambiaron (por una huella del contenido y `source_modified_at`). **No dice si reutiliza un parse ya hecho** del mismo archivo. Esto hay que medirlo.
  - **Caché:** *"Parsed files are cached for 48 hours. Re-parsing the same file within that window is free."* No dice cuál es la clave de la caché. Nuestros parses repetidos (#11 y #12) **sí cobraron**, pero fueron archivos subidos de nuevo y con un pedido distinto al primero, que tenía `max_pages`.
  - **Chunks:** son fijos (por oraciones, 1.024 tokens, 200 de solapamiento). En v2 **no se pueden listar** (`documents/{id}/chunks` no existe); se ven en los resultados de la búsqueda.
  - **Un índice no se puede modificar después de crearlo** (`store_attachments`, productos). Se puede agregar o sacar archivos y volver a sincronizar.
  - **`unique_id`:** volver a subir con el mismo ID reemplaza el archivo en lugar de duplicarlo.
  - **Metadata por archivo,** filtrable en la búsqueda con `custom_filters` (`eq`, `in`, …).
- **Precios publicados contra lo que medimos:**
  - **Extract agentic:** 15 por página. ✅ Coincide.
  - **Split:** 3 por página sobre un parse ya hecho. Daría unos 258 para los EEFF y 30 para el comunicado; no lo informa, así que hay que confirmarlo con el panel.
  - **Classify:** dice 1 por página, pero **nos informó 0** sobre un parse ya hecho.
  - **Gráficos con IA y confianza "high":** no figuran en la página de precios. Lo medimos nosotros: +5 por página.

### 13/11 · Fase 4 · Código de bibliotecas y prueba real bloqueada por el plan (créditos #23 y #24)

- **Código hecho** (probado con el LlamaCloud falso, 26 tests):
  - **Crear una biblioteca:** un directorio y un índice que parsea con **nuestra** configuración completa (`product_config_id`) y guarda capturas e items.
  - **Agregar y sacar corridas del wizard:** se usa el mismo `file_id`, sin volver a subir el archivo; `unique_id` es la corrida. Cada documento lleva metadata de identidad: el tipo de Classify y los campos sueltos de Extract.
  - **Sincronizar:** al terminar, lista con `parsing.list` los parses que creó LlamaCloud durante la sincronización, para **medir si volvió a parsear** y cuánto costó.
  - **Búsqueda de prueba** (`retrieval.retrieve`): con score, rerank, documento, páginas y la captura local de la página.
  - **Chat en vivo:** se reenvían los eventos de `chat.stream` tal cual, y al final se guardan con `chat.retrieve` y `get_summary`.
  - Pestaña **Bibliotecas** en el frontend.
- **Prueba real: bloqueada.** `POST /api/v1/beta/directories` respondió **403**: *"Buy credits in Settings › Plan & Credits to unlock this feature and raise your limits."* Coincide con la documentación: Index v2 (directorios, índice, búsqueda y chat) necesita un plan **Pay as you go, Pro o Enterprise**. Con el plan actual (los créditos gratis) no se puede usar. No se creó nada en LlamaCloud ni se cobró nada por la biblioteca. Sí se cobró el parse de la factura (15).
- **Corregido:**
  - `create_library` dejaba una carpeta local vacía cuando LlamaCloud fallaba. Ahora llama primero a LlamaCloud y, si algo falla a mitad de camino, borra lo creado (en LlamaCloud y en la carpeta). Tiene un test nuevo. Se borró la carpeta vacía que había quedado (`2026-11-13_204052_prueba-chica`, que solo tenía un `run.json`).
  - **Parse decía "1 páginas"** y "Todas las páginas se leyeron…" con una sola página. Se corrigió y se volvió a generar el resumen de la factura sin costo.
- **Queda sin responder** (hace falta el plan): si el sync de un índice reutiliza un parse ya hecho o vuelve a cobrar.

### 14/11 · Fase 4 · Plan B: bibliotecas locales con LlamaIndex y Voyage AI

- **Decisión del usuario:** como el índice de LlamaCloud necesita un plan pago, la búsqueda se arma con el **framework LlamaIndex** (código abierto, nativo de la familia LlamaIndex) en nuestro servidor, con **Voyage AI** para los embeddings y el reranker. El código de bibliotecas con LlamaCloud se deja para cuando haya plan.
- **Voyage AI** ([documentación](https://docs.voyageai.com/docs/introduction), [precios](https://docs.voyageai.com/docs/pricing)):
  - ofrece **embeddings y rerankers, no un modelo para el chat**;
  - los 200 millones de tokens iniciales son gratis en `voyage-4`, `voyage-4-large`, `voyage-4-lite`, `voyage-context-4` y `rerank-2.5`, y los 50 millones iniciales en `voyage-finance-2`.
- **La API key** quedó en `backend/.env` (ignorado por git) y `.env.example` tiene el lugar vacío.
- **Prueba de la key** (3 frases en español inventadas, sin datos del proyecto; 214 tokens, gratis):
  - `voyage-4` (1024 dimensiones): la frase del resultado neto quedó primera, con 0,62 de similitud contra 0,37 y 0,16 de las otras.
  - `voyage-finance-2` separó menos: 0,54, 0,38 y 0,17.
  - `rerank-2.5` ubicó primera la frase correcta, con 0,85.
  - **Se elige `voyage-4` y `rerank-2.5`.**
- **Pendiente:** un modelo de lenguaje para que el chat escriba las respuestas (Voyage no tiene).
