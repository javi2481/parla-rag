# Estado del proyecto · Parla RAG

**Última actualización:** 16/11/2026 (README nuevo, con diagramas) · **Commit de partida:** `c3660a9` (antes de separar Parla en dos proyectos)

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

El historial de git es el mismo hasta la separación: los commits viejos de audio quedan en el historial, pero el código de audio ya no está acá.
La conexión entre los dos (sumar la transcripción del audio a una biblioteca) quedó como pendiente: ver [Integración con parla-audio](#integración-con-parla-audio).

---

## Resumen en una tabla

| Fase | Qué | Estado |
|---|---|---|
| 0 | Reorganización: cada pipeline en su carpeta | ✅ Hecha |
| 1 | Informe: relevamiento de la API de LlamaCloud y 16 hallazgos | ✅ Hecha |
| 2 | Motor de corridas (carpeta-DB), wizard base, Subir y Parse | ✅ Hecha y probada con LlamaCloud real |
| 3 | Split, Classify, Schema (manual o automático) y Extract, con cajas sobre las capturas | ✅ Hecha y probada en los EEFF y en el comunicado |
| 4 | Bibliotecas: índice compartido, búsqueda, chat y evals | ✅ Hecha con el motor local: "BYMA 3T26" (corte por página) con 13 de 13 respuestas correctas en los evals |
| 5 | Audio | ➡️ Se fue a **parla-audio** |
| 6 | Cierre para la clase | ⏳ Pendiente |

---

## ✅ Lo que está hecho

### El wizard de un documento (fases 2 y 3)

`Subir → Parse → Split → Classify → Schema → Extract`. Cada paso arranca con un botón, muestra el estado real del job y, al terminar, el tilde verde. Para cada paso se ve qué se pidió, el resultado (amigable y crudo, descargable), las métricas y la interpretación, todo armado **solo con lo que devolvió la API**.

| Paso | Qué hace | Producto de LlamaCloud | Estado |
|---|---|---|---|
| 1 Subir | Sube el archivo y guarda una copia | `files.create` | ✅ |
| 2 Parse | Lee **todo**: Markdown, texto, items con cajas, confianza por página, tablas en Excel, gráficos como tablas, capturas, formularios y 3 salidas extra (`stripped_md`, `concatenated_stripped_txt`, `word_bbox`). Sin `max_pages` (Split lo rechaza). Guarda el pedido como configuración `parse_v2` | `parsing.create` / `get` | ✅ |
| 3 Split | Divide el documento en partes según categorías editables | `split.create` / `get`, `split_v1` | ✅ |
| 4 Classify | Elige el tipo de documento con reglas editables, confianza y razonamiento | `classify.create` / `get`, `classify_v2` | ✅ |
| 5 Schema | Manual (tabla, plantilla o JSON) o automático (`generate_schema`). Valida y guarda como configuración `extract_v2` | `extract.generate_schema`, `validate_schema`, `configurations` | ✅ |
| 6 Extract | Saca los datos con la cita (página, texto, caja) y la confianza de cada uno. Puede limitarse a una parte del Split (`target_pages`) | `extract.create` / `get` | ✅ |

**Además:**
- **Cajas sobre el archivo subido** (PDF o imagen), dibujadas sobre las capturas de Parse: los elementos de Parse (títulos, tablas, gráficos) y la cita de cada campo de Extract (verde o roja según la confianza; los campos sin cita, aparte).
- **Repetir un paso no borra nada:** la ejecución anterior pasa a `historial/`, los pasos siguientes vuelven a pendiente y `run.json` guarda el estado anterior con su `job_id`.
- **Borrar una corrida** borra en LlamaCloud el archivo y **todos** sus jobs, incluidos los del historial.
- **Plantillas de schema:** "Resultados trimestrales" (con el campo de identidad `emisor` y su guía de alias) y "Factura AR".
- **Opción "solo identidad obligatoria"** en Schema, porque un campo obligatorio obliga a Extract a devolver algo aunque no exista (con el schema automático inventó 8 ceros).
- **Aviso en la interpretación** cuando todos los campos son obligatorios.

### Bibliotecas (fase 4)

Una biblioteca junta documentos relacionados (por ejemplo "BYMA 3T26": EEFF, comunicado y presentación) para buscar y chatear con todos a la vez. Hay **dos motores** con las mismas funciones y las mismas respuestas, así la pantalla es una sola:

| Motor | Estado | Por qué |
|---|---|---|
| **Local** (`local_library.py`, el que se usa): LlamaIndex + Voyage AI + DeepSeek | ✅ Funciona. Chat probado de punta a punta | El índice de LlamaCloud necesita un plan pago |
| **LlamaCloud** (`library.py`): directorio + índice v2 + `retrieval` + `chat` | 🔒 Código hecho y probado con el cliente falso; con el plan gratis responde **403** | Necesita Pay as you go, Pro o Enterprise |

**El motor local:**
- **Agregar un documento** copia el Markdown de cada página del parse del wizard (no se vuelve a parsear nada) con la **metadata de identidad**: el tipo de Classify y los campos **obligatorios** del schema de Extract.
- **Sincronizar** arma el índice vectorial de LlamaIndex con los embeddings de **`voyage-4`** y lo guarda en la carpeta de la biblioteca (`index/`). El índice anterior pasa al historial.
- **Búsqueda de prueba:** `voyage-4` trae 3 candidatos por resultado y **`rerank-2.5`** los ordena. Se puede filtrar por metadata (solo igualdad). Cada búsqueda queda guardada.
- **Chat:** el chat engine nativo de LlamaIndex (`CondensePlusContextChatEngine`):
  1. si ya hubo preguntas, **`deepseek-flash`** reescribe la nueva para que se entienda sola;
  2. Voyage busca y rerankea, y quedan las 6 mejores páginas;
  3. DeepSeek responde **en vivo**, solo con esas páginas y citando *(documento, pág. N)*. Si el dato no está, lo dice.
- **Auditoría de cada turno** (`chats/local/turno_N.json`), con la instrumentación nativa de LlamaIndex: la consulta que se buscó de verdad, las páginas con su score, el prompt completo de cada llamada al modelo y los tokens (incluidos los de razonamiento).
- **Prueba real con la factura:** respondió el total y el emisor citando la página, entendió la pregunta de seguimiento y, ante una pregunta trampa (algo que no está), dijo que no estaba en los documentos. **No inventó.** Costo: unos USD 0,01 de DeepSeek.

### Calidad y auditoría

- **18 tests** con clientes falsos (sin red ni créditos): el wizard completo, los resúmenes, las bibliotecas con los dos motores, el chat local y los evals.
- **Bitácora** con cada prueba, hallazgo y decisión, y **registro de créditos** con cada llamada paga (30 entradas).
- **Datos crudos** de cada verificación en `backend/data/verificacion/` (fuera de git).

### Hallazgos importantes (para la clase y para la plantilla)

1. **El parse es el corazón:** se parsea **una vez**, completo, y los demás pasos usan ese parse (`pjb-...`).
2. **El parse no es determinístico:** el mismo archivo con la misma versión dio otra confianza, y una vez **inventó valores de un gráfico** (página 5 de la presentación). Los datos de gráficos hay que verificarlos contra la captura.
3. **Una cita válida y una confianza alta no garantizan el dato:** los ceros inventados tenían cita a un "0%" real de otro renglón. Lo que sirve es **ver la caja en la página**.
4. **Los campos obligatorios fuerzan a inventar.** Con pocos obligatorios y la regla "null si no consta", Extract no inventó nada.
5. **Costos medidos:** Parse agentic con todo, 15 créditos por página (21 a 39 en páginas con gráficos); Extract agentic, 15 por página; Classify sobre un parse, 0; Split no informa (la lista de precios dice 3 por página).

---

## ⏳ Lo pendiente, en orden

### 1. Terminar la fase 4 ✅ (16/11)

- [x] **Medio de pago cargado en Voyage AI**: se fue el límite de 3 pedidos y 10.000 tokens por minuto.
- [x] **"BYMA 3T26" sincronizada:** 111 páginas, 229 chunks, unos 184.000 tokens de Voyage (gratis), 7 segundos.
- [x] **"Listo cuando" de la fase 4:** respondió que el resultado neto coincide (22,162 miles en el comunicado, pág. 3, y 22.161.940 en los EEFF, pág. 4), citando los dos documentos. Las citas se verificaron contra el parse.
- [x] **Sacar un documento y volver a sincronizar:** sin el comunicado, la búsqueda ya no trae páginas de él. Después se volvió a agregar.
- [x] Registrado en la bitácora (16/11).
- **Para tener en cuenta:** el historial del chat sigue después de sacar un documento, así que las respuestas viejas quedan en la memoria del chat. No hay un botón para empezar un chat nuevo: evaluarlo para la clase.

### 2. Unificar la identidad de los documentos ✅ (16/11)

- [x] El comunicado y la presentación se extrajeron con la plantilla "Resultados trimestrales" y la opción "solo identidad obligatoria" (150 y 225 créditos, más el Split de la presentación, que no se informa).
- [x] Se volvieron a agregar a la biblioteca y se sincronizó. Los 3 documentos tienen `emisor: BYMA` y `periodo: 3T26`, y el filtro por `emisor`, `tipo` y `periodo` funciona.
- **Quedó pendiente:** `fecha_de_cierre` viene en dos formatos distintos (el problema de `format: date`) y la presentación no la tiene, así que no sirve para filtrar.
- **Hallazgo para decidir:** el corte en chunks separa las tablas de sus encabezados (unidades, histórico o ajustado por inflación), y el chat **supuso** las unidades. Se puede probar el separador de Markdown nativo de LlamaIndex. Ver la bitácora del 16/11.
- **Detalles chicos:** la búsqueda dice "documento(s)". (El 500 del filtro mal armado se arregló el 16/11: ahora responde 409 con el formato correcto.)

### 2b. Evals de las bibliotecas ✅ primera versión (16/11)

- [x] Evals nativos de LlamaIndex (`library_evals.py`, `POST /libraries/{id}/evals`): búsqueda con `RetrieverEvaluator` y respuestas con `FaithfulnessEvaluator` y `CorrectnessEvaluator`, con DeepSeek como juez. Cada corrida va a `libraries/<id>/evals/<fecha>/`.
- [x] Set de 13 preguntas verificadas: [`samples/byma/evals/preguntas.json`](../backend/data/samples/byma/evals/preguntas.json).
- [ ] **El usuario tiene que revisar el set**, sobre todo `datos-de-mercado-3t25` (marcada `a_revisar`).
- [x] **Separador decidido (16/11): `pagina` por defecto** (una página = un chunk). En los evals de BYMA dio MRR 0,84 y 13 de 13 respuestas correctas (oraciones: 0,71 y 12 de 13; markdown: 0,76 y 11 de 13). Usa el doble de tokens de DeepSeek por pregunta. Las bibliotecas creadas antes siguen con `oraciones`.
- [x] **Biblioteca principal: "BYMA 3T26"** (`2026-11-16_123606_byma-3t26-una-pagina-un-chunk`, separador `pagina`). Las dos pruebas (`· prueba: oraciones` y `· prueba: markdown`) **se dejan a propósito**, para que quede la trazabilidad y se pueda mostrar en la clase por qué ganó. La pantalla muestra el corte de cada biblioteca.
- [ ] Mostrar los evals en la pantalla de la biblioteca (hoy solo se ven por la API y en la carpeta).

### 3. Lo que falta del plan original de la fase 4

- [ ] **Paso 7 del wizard, "Biblioteca":** hoy un documento se suma desde la pestaña Bibliotecas. El plan pedía también un botón al final del wizard.
- [ ] **Procesar en lote** (`batches` de LlamaCloud): necesita el plan pago, igual que el índice. Con el motor local no hace falta para el índice, pero sí serviría para parsear varios PDFs de una vez.
- [ ] **Medir el índice de LlamaCloud** cuando haya plan: si el sync reutiliza un parse ya hecho o vuelve a cobrar (el código ya lo mide con `parsing.list`), y la caché de 48 horas.

### 4. Confirmaciones con el panel de LlamaCloud

- [ ] El saldo real. El estimado después del registro #24 es de **26.013 menos lo que cobró Split**, que no se informa.
- [ ] Lo que cobró **Split** (#13 y #17), que no informa `usage`.
- [ ] Lo que cobraron `generate_schema` y las validaciones.

### 5. Fase 6 · Cierre para la clase

- [x] README nuevo (16/11), con el estilo de los repos de portfolio: un diagrama Mermaid por etapa, las comparaciones "A vs. B" con sus números, qué aprendimos, costos y glosario. Licencia MIT. Resultados de los evals versionados en `docs/resultados/`.
- [ ] Revisar los comentarios del código.
- [ ] Dejar listas en `data/` las corridas y la biblioteca "BYMA 3T26" sincronizada, por si falla el wifi en clase.
- [ ] Escribir un **guion corto de la demo**: qué mostrar en cada paso y qué preguntarle al chat. Sugeridos: la página 8 del comunicado (gráficos), los 8 ceros inventados del schema automático, la pregunta trampa del chat.
- [ ] **Correr todo con Docker de punta a punta.** Ojo: la primera sincronización baja los datos de NLTK (necesita internet) a `data/nltk/`.

### 6. Detalles técnicos conocidos

- [ ] **`format: date` no se respeta:** Extract devuelve "30/09/2026" o "30 de septiembre del 2026" en lugar de AAAA-MM-DD. Es de LlamaCloud; documentarlo en la clase o ajustar la guía del campo.
- [ ] **El chat local usa el despachador global de la instrumentación de LlamaIndex:** si dos personas chatean **a la vez**, los registros de los dos turnos se pueden mezclar. Para una demo alcanza; para uso real habría que filtrar por `span_id`.
- [x] **Ruff sin avisos** (16/11): imports ordenados, strings concatenados entre paréntesis, `next()` en los tests; los 3 `except Exception` de los borrados quedan a propósito con `noqa` explicado. Ruff corre en el CI.
- [ ] **Las API keys se pegaron en el chat** con Claude (Voyage y DeepSeek): rotarlas al terminar.

---

## Integración con parla-audio

El plan original era que la transcripción del MP3 de la presentación (unos 9 minutos) se sumara a la biblioteca "BYMA 3T26", para que el chat respondiera con lo que **se dijo** y lo que está **escrito**. Ahora son dos proyectos, así que hay que decidir cómo se conectan:

- **Opción A (la más simple):** parla-audio exporta la transcripción como archivo (Markdown o texto, con hablantes y tiempos) y en parla-rag se sube como un documento más por el wizard. Hay que **verificar que LlamaParse acepte `.md` o `.txt`**; si no, exportarla en PDF (Scribe tiene `additional_formats`).
- **Opción B:** una ruta en parla-rag para agregar a una biblioteca un texto que no viene del wizard (por ejemplo `POST /libraries/{id}/texts`), con su metadata (documento, hablante, minuto). En el motor local es directo: es un `Document` más de LlamaIndex.
- **Para decidir más adelante.** Hasta entonces, cada proyecto funciona solo.

---

## 🗺️ Roadmap (después de la clase)

- **Evals:** la primera versión ya está hecha, con lo nativo de LlamaIndex (ver el punto 2b). [Ragas](https://docs.ragas.io/) queda solo si lo nativo no alcanza. Sumaría *context precision* y *context recall*; tiene integración con LlamaIndex (`ragas.integrations.llama_index`).
  - Además, un **set de respuestas verificadas a mano** para BYMA 3T26: las cifras de Extract, la página 5 de la presentación y preguntas de identidad ("¿qué dice la Sociedad…?").
- **Índice de LlamaCloud** (el motor `library.py` ya está escrito) cuando haya un plan pago: comparar calidad, velocidad y costo contra el motor local.
- **Pasar la carpeta-DB a `agent_data`**, la base JSON nativa de LlamaCloud.
- **Verify** (`alpha.verify`): detectar documentos adulterados, cuando salga de alpha.
- **Webhooks** de LlamaCloud en lugar de consultar el estado (solo con el servidor publicado).
- **Filtros de la búsqueda local más allá de la igualdad** (`in`, mayor que…), si hiciera falta.
- **Probar `deepseek-v4-pro`** para el chat y comparar con `deepseek-flash`.

---

## Datos locales (no están en git)

En `backend/data/` hay datos generados que **no se suben al repo** (pesan mucho y traen links firmados temporales). Están en la máquina donde se trabajó:

| Carpeta | Qué hay |
|---|---|
| `documents/runs/` | 6 corridas: comunicado (2), presentación (2), EEFF y factura |
| `documents/libraries/` | **"BYMA 3T26"**, la principal (`2026-11-16_123606_…`, corte `pagina`, con sus evals); "BYMA 3T26 · prueba: oraciones" (`2026-11-14_192312_…`, la primera, con 2 chats y sus evals); "BYMA 3T26 · prueba: markdown" (`2026-11-16_105914_…`); y "Factura (prueba de chat)" (4 turnos de chat) |
| `verificacion/` | Los datos crudos de las verificaciones 1 y 2 |
| `nltk/` | Los datos de NLTK que usa LlamaIndex para cortar el texto en oraciones (se bajan solos) |

Los documentos de ejemplo (BYMA y la factura) **sí** están en git, en `backend/data/samples/`.

## Claves que hacen falta (`backend/.env`)

| Variable | Para qué | Dónde se saca |
|---|---|---|
| `LLAMA_CLOUD_API_KEY` | Todo el wizard | [cloud.llamaindex.ai](https://cloud.llamaindex.ai) |
| `VOYAGE_API_KEY` | Embeddings y reranker de las bibliotecas | [dashboard.voyageai.com](https://dashboard.voyageai.com) (cargar un medio de pago) |
| `DEEPSEEK_API_KEY` | El chat de las bibliotecas | [platform.deepseek.com](https://platform.deepseek.com) |

El resto de las opciones está en [`backend/.env.example`](../backend/.env.example).
