# Estado del proyecto · Parla RAG

**Última actualización:** 21/11/2026 (corpus de Aprendizaje Automático II, chat con OpenAI, evals nuevos) · **Commit de partida:** `c3660a9` (antes de separar Parla en dos proyectos)

Este archivo es el resumen para retomar el trabajo: qué está hecho, qué falta y en qué orden, y qué queda para después.
El detalle de cada prueba, con sus datos y lo que costó, está en la [bitácora](bitacora.md). El diseño completo está en el [plan](plan.md).

---

## De dónde viene

Parla empezó como **un solo proyecto** con dos pipelines: documentos (LlamaCloud) y audio (ElevenLabs).
El **15/11/2026** se separó en dos repositorios, para trabajar cada uno por su lado:

| Proyecto | Qué tiene |
|---|---|
| **parla-rag** (este) | El wizard de documentos con LlamaCloud y las bibliotecas: índice compartido, búsqueda y chat |
| **parla-audio** | Texto a voz con la voz clonada y voz a texto con ElevenLabs (Scribe) |

El **21/11/2026** se cambió el corpus de ejemplo por el material teórico de **Aprendizaje Automático II** (14 PDF, 410 páginas) y el modelo del chat pasó de DeepSeek a **`gpt-5-nano`** de OpenAI.

---

## Resumen en una tabla

| Fase | Qué | Estado |
|---|---|---|
| 0 | Reorganización: cada pipeline en su carpeta | ✅ Hecha |
| 1 | Informe: relevamiento de la API de LlamaCloud y 16 hallazgos | ✅ Hecha |
| 2 | Motor de corridas (carpeta-DB), wizard base, Subir y Parse | ✅ Hecha y probada con LlamaCloud real |
| 3 | Split, Classify, Schema (manual o automático) y Extract, con cajas sobre las capturas | ✅ Hecha y probada |
| 4 | Bibliotecas: índice compartido, búsqueda, chat y evals | ✅ Hecha con el motor local: "Aprendizaje Automático II", 410 páginas indexadas |
| 5 | Audio | ➡️ Se fue a **parla-audio** |
| 6 | Cierre para la clase | 🟡 En curso |

---

## ✅ Lo que está hecho

### El wizard de un documento (fases 2 y 3)

`Subir → Parse → Split → Classify → Schema → Extract → Biblioteca`. Cada paso arranca con un botón, muestra el estado real del job y, al terminar, el tilde verde. Para cada paso se ve qué se pidió, el resultado (amigable y crudo, descargable), las métricas y la interpretación, todo armado **solo con lo que devolvió la API**.

| Paso | Qué hace | Producto de LlamaCloud | Estado |
|---|---|---|---|
| 1 Subir | Sube el archivo y guarda una copia | `files.create` | ✅ |
| 2 Parse | Lee **todo**: Markdown, texto, items con cajas, confianza por página, tablas en Excel, gráficos como tablas, capturas, formularios y 3 salidas extra (`stripped_md`, `concatenated_stripped_txt`, `word_bbox`). Sin `max_pages` (Split lo rechaza). Guarda el pedido como configuración `parse_v2` | `parsing.create` / `get` | ✅ |
| 3 Split | Divide el documento en partes según categorías editables | `split.create` / `get`, `split_v1` | ✅ |
| 4 Classify | Elige el tipo de documento con reglas editables, confianza y razonamiento | `classify.create` / `get`, `classify_v2` | ✅ |
| 5 Schema | Manual (tabla, plantilla o JSON) o automático (`generate_schema`). Valida y guarda como configuración `extract_v2` | `extract.generate_schema`, `validate_schema`, `configurations` | ✅ |
| 6 Extract | Saca los datos con la cita (página, texto, caja) y la confianza de cada uno. Puede limitarse a una parte del Split (`target_pages`) | `extract.create` / `get` | ✅ |
| 7 Biblioteca | Suma la corrida a una biblioteca, sin gastar créditos | motor local | ✅ |

**Además:**
- **Cajas sobre el archivo subido** (PDF o imagen), dibujadas sobre las capturas de Parse: los elementos de Parse (títulos, tablas, gráficos) y la cita de cada campo de Extract (verde o roja según la confianza; los campos sin cita, aparte).
- **Repetir un paso no borra nada:** la ejecución anterior pasa a `historial/`, los pasos siguientes vuelven a pendiente y `run.json` guarda el estado anterior con su `job_id`.
- **Borrar una corrida** borra en LlamaCloud el archivo y **todos** sus jobs, incluidos los del historial.
- **Plantillas de schema:** "Resultados trimestrales" (con un campo de identidad y su guía de alias) y "Factura AR".
- **Opción "solo identidad obligatoria"** en Schema, porque un campo obligatorio obliga a Extract a devolver algo aunque no exista.
- **Aviso en la interpretación** cuando todos los campos son obligatorios.

### Bibliotecas (fase 4)

Una biblioteca junta documentos relacionados (por ejemplo, las 14 clases de "Aprendizaje Automático II") para buscar y chatear con todos a la vez. Hay **dos motores** con las mismas funciones y las mismas respuestas, así la pantalla es una sola:

| Motor | Estado | Por qué |
|---|---|---|
| **Local** (`local_library.py`, el que se usa): LlamaIndex + Voyage AI + OpenAI | ✅ Funciona | El índice de LlamaCloud necesita un plan pago |
| **LlamaCloud** (`library.py`): directorio + índice v2 + `retrieval` + `chat` | 🔒 Código hecho y probado con el cliente falso; con el plan gratis responde **403** | Necesita Pay as you go, Pro o Enterprise |

**El motor local:**
- **Agregar un documento** copia el Markdown de cada página del parse del wizard (no se vuelve a parsear nada) con la **metadata de identidad**: el tipo de Classify y los campos **obligatorios** del schema de Extract.
- **Sincronizar** arma el índice vectorial de LlamaIndex con los embeddings de **`voyage-4`** y lo guarda en la carpeta de la biblioteca (`index/`). El índice anterior pasa al historial.
- **Corte por página** (`LIBRARY_SPLITTER=pagina`, por defecto): una página = un chunk. Fue el que mejor dio en las comparaciones con los otros dos cortes nativos (`SentenceSplitter` y `MarkdownNodeParser`), porque no separa una tabla de su encabezado. Las diapositivas de clase son cortas, así que una página entra entera.
- **Búsqueda de prueba:** `voyage-4` trae 3 candidatos por resultado y **`rerank-2.5`** los ordena. Se puede filtrar por metadata (solo igualdad). Cada búsqueda queda guardada.
- **Chat:** el chat engine nativo de LlamaIndex (`CondensePlusContextChatEngine`):
  1. si ya hubo preguntas, **`gpt-5-nano`** reescribe la nueva para que se entienda sola;
  2. Voyage busca y rerankea, y quedan las 6 mejores páginas;
  3. `gpt-5-nano` responde **en vivo**, solo con esas páginas y citando *(documento, pág. N)*. Si el dato no está, lo dice.
- **Auditoría de cada turno** (`chats/local/turno_N.json`), con la instrumentación nativa de LlamaIndex: la consulta que se buscó de verdad, las páginas con su score, el prompt completo de cada llamada al modelo y los tokens (incluidos los de razonamiento).

### La biblioteca "Aprendizaje Automático II" (21/11)

- **14 corridas parseadas** (la presentación y las 13 clases): 410 páginas, **7.250 créditos** (17,7 por página en promedio, entre 15 y 25). Confianza del documento entre 78 % y 99 %.
- **Sincronizada** en 6 s: 410 páginas en 410 chunks, 0 créditos de LlamaCloud.
- **Set de evals** en [`samples/aprendizaje-automatico-ii/evals/preguntas.json`](../backend/data/samples/aprendizaje-automatico-ii/evals/preguntas.json): 18 preguntas (16 con fuente y 2 trampas), con las respuestas verificadas en el parse.
- **Evals de búsqueda:** hit rate 1,0 y MRR 1,0. Ojo: las preguntas usan casi las mismas palabras que las diapositivas (ver la bitácora del 21/11).

### Calidad y auditoría

- **18 tests** con clientes falsos (sin red ni créditos): el wizard completo, los resúmenes, las bibliotecas con los dos motores, el chat local y los evals.
- **Bitácora** con cada prueba, hallazgo y decisión, y **registro de créditos** con cada llamada paga.
- **Datos crudos** de cada verificación en `backend/data/verificacion/` (fuera de git).

### Hallazgos importantes (para la clase y para la plantilla)

1. **El parse es el corazón:** se parsea **una vez**, completo, y los demás pasos usan ese parse (`pjb-...`).
2. **El parse no es determinístico** y puede **inventar los valores de un gráfico** con confianza alta. Los datos de gráficos hay que verificarlos contra la captura.
3. **Una cita válida y una confianza alta no garantizan el dato.** Lo que sirve es **ver la caja en la página**.
4. **Los campos obligatorios fuerzan a inventar.** Con pocos obligatorios y la regla "null si no consta", Extract no inventó nada.
5. **Cortar mal los chunks hace que el chat suponga lo que falta:** si la tabla queda separada de su encabezado, el modelo "completa" las unidades. Por eso el corte por defecto es una página = un chunk.
6. **Costos medidos:** Parse agentic con todo, de 15 a 25 créditos por página según los gráficos; Extract agentic, 15 por página; Classify sobre un parse, 0; Split no informa (la lista de precios dice 3 por página).
7. **En Windows hay que decir `encoding="utf-8"`** al leer y escribir archivos: si no, Python usa cp1252 y el guardado del parse falla con caracteres como "○" (bitácora del 21/11).

---

## ⏳ Lo pendiente, en orden

### 1. Revisar el set de evals

- [ ] **El usuario tiene que revisar** [`preguntas.json`](../backend/data/samples/aprendizaje-automatico-ii/evals/preguntas.json) (está marcado como borrador).
- [ ] Sumar **preguntas más exigentes**: parafraseadas y que crucen clases (por ejemplo, *"¿qué tienen en común ResNet y U-Net?"*). Las actuales copian el vocabulario de las diapositivas.
- [ ] Cubrir las clases que no tienen preguntas: 01, 02 y 11.

### 2. Revisar las páginas con baja confianza

- [ ] Comparar las capturas con el Markdown en las clases con menos confianza: `09 Detección de objetos` (78 %), `05 PLN - Redes neuronales` (79 %) y la clase 02 (85 %, sobre todo las págs. 5 y 6). La API no dice el motivo.

### 3. Lo que falta del plan original de la fase 4

- [ ] **Procesar en lote** (`batches` de LlamaCloud): necesita el plan pago. Para el lote del 21/11 se usó la API del wizard con 13 parses en paralelo (84 s).
- [ ] **Medir el índice de LlamaCloud** cuando haya plan: si el sync reutiliza un parse ya hecho o vuelve a cobrar (el código ya lo mide con `parsing.list`), y la caché de 48 horas.

### 4. Confirmaciones con el panel de LlamaCloud

- [ ] El saldo real. El estimado después del registro #44 es **18.045** (25.295 informado el 21/11, menos 7.250). Se renueva el 23/11.
- [ ] Lo que cobran **Split**, `generate_schema` y las validaciones, que no informan `usage`.

### 5. Fase 6 · Cierre para la clase

- [ ] Revisar los comentarios del código.
- [ ] Dejar listas en `data/` las corridas y la biblioteca sincronizada, por si falla el wifi en clase.
- [ ] Escribir un **guion corto de la demo**: qué mostrar en cada paso y qué preguntarle al chat. Sugeridos: una clase con gráficos (09), la pregunta trampa de Q-learning y una pregunta que cruce clases.
- [ ] **Capturas nuevas para el README** con la biblioteca de la materia.
- [ ] **Volver a probar Docker** con el corpus nuevo (la imagen copia `data/samples/`: ahora son 57 MB de PDF y notebooks).
- [ ] **Decidir si el material de la materia va a git** (`backend/data/samples/aprendizaje-automatico-ii/`) o queda fuera, si el repo es público.

### 6. Detalles técnicos conocidos

- [ ] **`format: date` no se respeta:** Extract devuelve fechas en el formato del documento en lugar de AAAA-MM-DD. Es de LlamaCloud; documentarlo en la clase o ajustar la guía del campo.
- [ ] **El chat local usa el despachador global de la instrumentación de LlamaIndex:** si dos personas chatean **a la vez**, los registros de los dos turnos se pueden mezclar. Para una demo alcanza; para uso real habría que filtrar por `span_id`.
- [ ] **Un test falla en Windows** (`test_upload_parse_and_delete`): compara rutas con `/` y Windows las arma con `\`. En el CI (Linux) pasa.
- [ ] **Las API keys de Voyage y DeepSeek se pegaron en el chat** con Claude en una sesión anterior: rotarlas. La de DeepSeek ya no se usa.

---

## Integración con parla-audio

La idea es que la transcripción de un audio se sume a una biblioteca, para que el chat responda con lo que **se dijo** y lo que está **escrito**. Por ejemplo, el audio de una clase junto a sus diapositivas. Hay que decidir cómo se conectan los dos proyectos:

- **Opción A (la más simple):** parla-audio exporta la transcripción como archivo y en parla-rag se sube como un documento más por el wizard. LlamaParse acepta `.txt` ([lista oficial](https://developers.llamaindex.ai/llamaparse/general/supported_document_types/)), pero no `.md`; también se puede exportar en PDF (Scribe tiene `additional_formats`).
- **Opción B:** una ruta en parla-rag para agregar a una biblioteca un texto que no viene del wizard (por ejemplo `POST /libraries/{id}/texts`), con su metadata (documento, hablante, minuto). En el motor local es directo: es un `Document` más de LlamaIndex.
- **Para decidir más adelante.** Hasta entonces, cada proyecto funciona solo.

---

## 🗺️ Roadmap (después de la clase)

- **Evals:** todo es nativo de LlamaIndex (`RetrieverEvaluator`, `FaithfulnessEvaluator`, `CorrectnessEvaluator`). LlamaCloud y Voyage AI no tienen un producto de evals propio (verificado el 21/11). [Ragas](https://docs.ragas.io/) queda solo si lo nativo no alcanza.
- **Notebooks de las clases** con `IPYNBReader`, el lector nativo de LlamaIndex, si se quiere que el chat responda sobre el código de las prácticas.
- **Índice de LlamaCloud** (el motor `library.py` ya está escrito) cuando haya un plan pago: comparar calidad, velocidad y costo contra el motor local.
- **Pasar la carpeta-DB a `agent_data`**, la base JSON nativa de LlamaCloud.
- **Verify** (`alpha.verify`): detectar documentos adulterados, cuando salga de alpha.
- **Webhooks** de LlamaCloud en lugar de consultar el estado (solo con el servidor publicado).
- **Filtros de la búsqueda local más allá de la igualdad** (`in`, mayor que…), si hiciera falta.
- **Comparar modelos de OpenAI** para el chat (`gpt-5-nano` contra uno más grande), con los mismos evals.

---

## Datos locales (no están en git)

En `backend/data/` hay datos generados que **no se suben al repo** (pesan mucho y traen links firmados temporales). Están en la máquina donde se trabajó:

| Carpeta | Qué hay |
|---|---|
| `documents/runs/` | 14 corridas: la presentación y las 13 clases, todas con el parse terminado |
| `documents/libraries/` | **"Aprendizaje Automático II"** (`2026-11-21_133046_…`, corte `pagina`, con sus evals) |
| `nltk/` | Los datos de NLTK que usa LlamaIndex para cortar el texto en oraciones (se bajan solos) |

El material de la materia está en `backend/data/samples/aprendizaje-automatico-ii/`, **fuera de git** (es de la cátedra y el repo es público). En git va solo `evals/preguntas.json`.

## Claves que hacen falta (`backend/.env`)

| Variable | Para qué | Dónde se saca |
|---|---|---|
| `LLAMA_CLOUD_API_KEY` | Todo el wizard | [cloud.llamaindex.ai](https://cloud.llamaindex.ai) |
| `VOYAGE_API_KEY` | Embeddings y reranker de las bibliotecas | [dashboard.voyageai.com](https://dashboard.voyageai.com) (cargar un medio de pago) |
| `OPENAI_API_KEY` | El chat de las bibliotecas y el juez de los evals | [platform.openai.com](https://platform.openai.com) |

El resto de las opciones está en [`backend/.env.example`](../backend/.env.example).
