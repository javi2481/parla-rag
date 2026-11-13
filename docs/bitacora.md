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

**Pendiente de auditar:** Classify, Generate schema y Extract no informan créditos en su respuesta. Para saber cuánto costaron hay que comparar con el saldo del panel de LlamaCloud. Lo que sí se conoce suma **820 créditos** (210 + 585 + 15 + 10). Si el panel muestra menos de **28.623**, la diferencia es lo que cobraron esos tres pasos juntos.

Pedir de nuevo el resultado de un job que ya terminó (`parsing.get`) **no cobra créditos**: se comprobó el 13/11, el job #2 siguió marcando 585.

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
