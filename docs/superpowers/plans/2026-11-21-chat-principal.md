# El chat como página principal · Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** que la página principal sea un chat sobre las 14 clases, con el recorrido del proyecto fijo arriba, pestañas de conversación, respuestas que relacionan clases con sus citas agrupadas por documento, un "detrás de escena" explicado y filtros por unidad y clase.

**Architecture:** el backend (FastAPI + LlamaIndex) suma una búsqueda compartida con modo MMR configurable, conversaciones como carpetas dentro de la biblioteca, filtros en el chat y pasos del wizard con requisito propio (Classify pide solo el parse). Los evals miden cobertura de clases y tiempo. El frontend (React + Vite) suma una sección "Chat" nueva que usa esas rutas.

**Tech Stack:** Python 3.11, FastAPI, LlamaIndex 0.14 (`VectorStoreIndex`, `CondensePlusContextChatEngine`, `llama_index.core.evaluation`), Voyage AI (`voyage-4`, `rerank-2.5`), OpenAI (`gpt-5-nano`), LlamaCloud (Classify), React + TypeScript + Tailwind, pytest con clientes falsos.

**Spec:** [docs/superpowers/specs/2026-11-21-chat-principal-design.md](../specs/2026-11-21-chat-principal-design.md)

## Global Constraints

- Solo lo nativo de LlamaCloud, LlamaParse y LlamaIndex, con sus integraciones oficiales (Voyage AI, OpenAI). No sumar otros frameworks.
- Un comentario `#` (o `//`) en español rioplatense arriba de cada función nueva o tocada, que diga qué hace y por qué.
- Todo texto al usuario, en español rioplatense (voseo).
- Sin base de datos: todo en `backend/data/` (carpeta-DB, `app/core/runs/store.py`). Leer y escribir siempre con `encoding="utf-8"`.
- Pedir el OK del usuario antes de cualquier llamada paga (los evals con respuestas cobran OpenAI; Classify se espera en 0 pero se verifica el `usage`).
- Cada prueba real, hallazgo y decisión va a `docs/bitacora.md`, con créditos de LlamaCloud, tokens de Voyage y costo de OpenAI.
- Ningún número en pantalla inventado: sale de la API o de lo guardado. Un costo en dólares calculado con la lista de precios se marca como "estimado".
- Límite de tiempo por respuesta del chat: **10 segundos**. Si dos configuraciones buscan igual de bien, gana la más rápida.
- Commits: conventional commits, **sin** líneas de coautoría ni atribución a IA (regla del usuario). Commitear solo con el OK del usuario.
- Verificación de cada fase: `cd backend && uv run pytest`, `uv run ruff check .`, `cd frontend && npm run build`, la medición de la fase, la entrada en la bitácora y la revisión del usuario antes de seguir.

## Review Focus

1. **Pregunta con filtros que no dejan ninguna página** (por ejemplo, unidad "Temas complementarios" y clase 03): el chat tiene que decir que no encontró páginas con esos filtros, no romper ni responder sin fuentes. → test en la tarea 6.
2. **Conversación nueva sin turnos y pestaña cerrada:** abrir una conversación vacía, cerrarla y recargar no tiene que dejar pestañas fantasma ni perder las otras. → test en la tarea 5.
3. **Clase que Classify ubica en otra unidad** (por ejemplo, la 12 en "Aprendizaje profundo aplicado a imágenes"): el resultado se muestra con su razonamiento y se anota; no se corrige a mano en silencio. → verificación en la tarea 8.
4. **Re-correr Split en una corrida que ya tiene Classify:** no tiene que borrar el Classify (ya no depende de Split). → test en la tarea 7.
5. **Una pregunta que llega mientras otra está respondiendo** en la misma pestaña: el cuadro queda deshabilitado hasta que termine, y la respuesta en curso no se pisa. → verificación manual en la tarea 11.

---

## Fase 0 · Dejar el repo en orden

### Task 0: Commitear el cambio de corpus y limpiar referencias viejas

**Files:**
- Modify: `.gitignore` (sumar `.superpowers/`)
- Modify: `backend/app/pipelines/documents/steps/s5_schema.py:53` (el comentario apunta a `docs/verificacion-2-fase3.md`, que ya no existe: dejar el motivo sin el link)
- Modify: `docs/plan.md` (sacar las menciones de `factura_ejemplo.pdf`, que el usuario borró)

- [ ] **Step 1:** Hacer los tres cambios de arriba.
- [ ] **Step 2:** Run `cd backend && uv run pytest -q && uv run ruff check .` → Expected: `17 passed` y el único `FAILED` es `test_upload_parse_and_delete` (rutas de Windows, preexistente); Ruff `All checks passed!`.
- [ ] **Step 3:** Pedir el OK al usuario y commitear todo lo pendiente del 21/11 (corpus nuevo, OpenAI, UTF-8, BYMA fuera, docs) en commits por unidad de trabajo, por ejemplo `feat: chat con gpt-5-nano de OpenAI en lugar de DeepSeek`, `fix: leer y escribir las corridas en UTF-8`, `docs: corpus de Aprendizaje Automático II`. Preguntar antes si `backend/data/samples/aprendizaje-automatico-ii/` va a git.

---

## Fase 1 · Un set de evals que mida de verdad

### Task 1: Cobertura de clases y tiempo en los evals

**Files:**
- Modify: `backend/app/pipelines/documents/library_evals.py` (`eval_retrieval`, `eval_answer`, `metrics_of` o la función que arma `metricas`)
- Test: `backend/tests/pipelines/documents/test_local_library.py`

**Interfaces:**
- Produces: en cada resultado de búsqueda, `"clases_esperadas": list[str]`, `"clases_encontradas": list[str]` (nombres de documento) y `"cobertura_de_clases": float` (encontradas ∩ esperadas / esperadas). En cada respuesta, `"segundos": float`. En las métricas de la corrida: `"Cobertura de clases (promedio)"` y `"Tiempo por respuesta (promedio / máximo)"`.

- [ ] **Step 1: Write the failing test** `test_evals_miden_cobertura_y_tiempo` en `test_local_library.py`, con el cliente falso: una pregunta con fuentes en dos documentos (`"CLASE"` y `"OTRA"`), donde solo llegan páginas de uno.

```python
busqueda = resultado["resultados"][0]["busqueda"]
assert busqueda["clases_esperadas"] == ["clase.pdf", "otra.pdf"]
assert busqueda["cobertura_de_clases"] == 0.5
assert any(m["label"] == "Cobertura de clases (promedio)" for m in resultado["metricas"])
# con respuestas: cada una trae cuánto tardó
assert resultado_con_respuestas["resultados"][0]["respuesta"]["segundos"] >= 0
```

- [ ] **Step 2:** Run `cd backend && uv run pytest tests/pipelines/documents/test_local_library.py -k cobertura -v` → Expected: FAIL (`KeyError: 'clases_esperadas'`).
- [ ] **Step 3:** Implementar. `clases_encontradas` sale de los documentos de las páginas que llegan al modelo (después del reranker), sin repetir. El tiempo se toma con `time.perf_counter()` alrededor de la respuesta del chat en `eval_answer`. Sumar la línea de interpretación: "La cobertura de clases mide, en las preguntas que cruzan clases, cuántas de las clases correctas llegaron al modelo."
- [ ] **Step 4:** Run el mismo test → Expected: PASS. Run `uv run pytest -q` → sin fallas nuevas.
- [ ] **Step 5:** Commit `feat: los evals miden cobertura de clases y tiempo por respuesta`.

### Task 2: Preguntas más exigentes y línea de base

**Files:**
- Modify: `backend/data/samples/aprendizaje-automatico-ii/evals/preguntas.json`
- Modify: `docs/bitacora.md`

- [ ] **Step 1:** Sumar **al menos 10 preguntas** con tres tipos nuevos en `"tipo"`: `"parafraseada"` (la misma idea con otras palabras que las de la diapositiva), `"varias_diapositivas"` (la respuesta está repartida en páginas seguidas, por ejemplo YOLO en la clase 09) y `"cruza_clases"` (necesita dos o más clases; por ejemplo: "¿qué tienen en común ResNet y U-Net?" → clase 07 págs. 27–28 y clase 10 pág. 12). Cubrir también las clases 01, 02 y 11, que hoy no tienen preguntas. Cada respuesta esperada se verifica en el `document.md` del parse y se buscan **todas** las páginas que la contienen (como en el set actual). `"estado"` sigue en borrador.
- [ ] **Step 2:** Run los evals **de búsqueda** (gratis: tokens de Voyage) con la configuración actual: `POST /api/documents/libraries/2026-11-21_133046_aprendizaje-automatico-ii/evals` con `{"conjunto": "aprendizaje-automatico-ii", "respuestas": false}` → Expected: 200 y MRR **menor que 1,0** en las preguntas nuevas (si da 1,0 en todas, el set sigue siendo fácil: endurecerlo antes de seguir).
- [ ] **Step 3:** Pedir el OK y correr los evals **con respuestas** (unos centavos de OpenAI). Anotar en la bitácora: hit rate, MRR, cobertura de clases, correctas, fieles, tiempo promedio y máximo, tokens y costo estimado. Esta es la **línea de base** (6 páginas, sin MMR).
- [ ] **Step 4:** Revisión del usuario: el set nuevo y la línea de base.

---

## Fase 2 · Búsqueda entre clases

### Task 3: Una sola búsqueda para el chat, la búsqueda de prueba y los evals, con MMR configurable

**Files:**
- Modify: `backend/app/pipelines/documents/settings.py`
- Modify: `backend/app/pipelines/documents/local_library.py` (`make_chat_engine`, `search`)
- Modify: `backend/app/pipelines/documents/library_evals.py` (`eval_retrieval`, `run_evals`)
- Modify: `backend/app/pipelines/documents/library_router.py` (`run_evals`: cuerpo con `top_k` y `modo`)
- Test: `backend/tests/pipelines/documents/test_local_library.py`

**Interfaces:**
- Produces: en `DocumentsSettings`, `library_retrieval_mode: str = "default"` (`"default"` o `"mmr"`) y `library_mmr_threshold: float = 0.5`.
- Produces: `make_retriever(index: VectorStoreIndex, settings: DocumentsSettings, candidates: int | None = None, filters: MetadataFilters | None = None) -> BaseRetriever` en `local_library.py`. Usa `index.as_retriever(similarity_top_k=candidates or settings.library_chat_top_k * CANDIDATES_PER_RESULT, filters=filters, vector_store_query_mode=settings.library_retrieval_mode, vector_store_kwargs={"mmr_threshold": settings.library_mmr_threshold})` (los kwargs solo con `"mmr"`).
- Produces: `run_evals(store, settings, library, name, candidates, with_answers, top_k: int | None = None, mode: str | None = None)`; si vienen `top_k` o `mode`, se usa `settings.model_copy(update=...)` y los valores quedan en el `request.json` de la corrida.

- [ ] **Step 1: Write the failing test** `test_make_retriever_usa_mmr_si_esta_configurado`: con `settings.library_retrieval_mode = "mmr"`, `make_retriever(index, settings)._vector_store_query_mode == VectorStoreQueryMode.MMR`; con `"default"`, `== VectorStoreQueryMode.DEFAULT`. Y `test_evals_aceptan_top_k_y_modo`: `POST /evals` con `{"top_k": 12, "modo": "mmr"}` guarda `"top_k": 12` y `"modo": "mmr"` en el `request` de la corrida.
- [ ] **Step 2:** Run `uv run pytest tests/pipelines/documents/test_local_library.py -k "mmr or top_k" -v` → Expected: FAIL (`ImportError` de `make_retriever`).
- [ ] **Step 3:** Implementar `make_retriever` y usarlo en `make_chat_engine`, `search` y `eval_retrieval` (así los evals miden exactamente la búsqueda del chat). Un valor de `library_retrieval_mode` que no sea `"default"` ni `"mmr"` da `ValueError` con un mensaje en español.
- [ ] **Step 4:** Run los tests → PASS; `uv run pytest -q` → sin fallas nuevas; `uv run ruff check .` → limpio.
- [ ] **Step 5:** Commit `feat: búsqueda compartida con modo MMR configurable`.

### Task 4: Instrucciones para relacionar clases y la comparación

**Files:**
- Modify: `backend/app/pipelines/documents/local_library.py` (`SYSTEM_PROMPT`)
- Modify: `backend/app/pipelines/documents/settings.py` (valores por defecto que ganen)
- Modify: `docs/bitacora.md`

- [ ] **Step 1:** Sumar a `SYSTEM_PROMPT`, en el mismo tono: "Si la pregunta involucra varios temas o clases, relacioná lo que dice cada documento (en qué se parecen y en qué se diferencian) y citá cada uno."
- [ ] **Step 2:** Pedir el OK y correr los evals con respuestas en tres configuraciones: `{"top_k": 6, "modo": "default"}` (ya es la línea de base, con el prompt nuevo), `{"top_k": 12, "modo": "default"}` y `{"top_k": 12, "modo": "mmr"}`.
- [ ] **Step 3:** Elegir con los números: primero cobertura de clases y correctas; después tiempo (máximo 10 s). Poner los valores elegidos como defecto en `settings.py`, `backend/.env.example` (avisarle al usuario, porque no se puede editar desde acá) y `docs/estado.md`. Anotar en la bitácora la tabla de las tres corridas y el motivo de la elección.
- [ ] **Step 4:** Commit `feat: el chat relaciona las clases y usa la búsqueda elegida por los evals`.
- [ ] **Step 5:** Revisión del usuario.

---

## Fase 3 · Filtros por unidad

### Task 5: Conversaciones como carpetas dentro de la biblioteca

**Files:**
- Modify: `backend/app/pipelines/documents/local_library.py` (`chat_turn`, `chat_history`)
- Modify: `backend/app/pipelines/documents/library.py` (`chat_turn`: acepta y descarta `conversation_id` y `filters`, para que los dos motores tengan la misma firma)
- Modify: `backend/app/pipelines/documents/library_router.py` (rutas nuevas y `describe`)
- Test: `backend/tests/pipelines/documents/test_local_library.py`

**Interfaces:**
- Produces (carpeta-DB): `libraries/<id>/chats/local/<conversation_id>/conversacion.json` con `{"id", "creada", "cerrada": false}` y sus `turno_N.json`. `conversation_id` = fecha y hora (`2026-11-21_150000`), como las corridas.
- Produces (HTTP):
  - `GET /api/documents/libraries/{id}/conversations` → `[{"id", "titulo", "creada", "turnos": int}]`, solo las no cerradas, de la más vieja a la más nueva. `titulo` = las primeras 6 palabras de la primera pregunta, o `"Conversación nueva"` si no tiene turnos.
  - `POST /api/documents/libraries/{id}/conversations` → la conversación creada.
  - `GET /api/documents/libraries/{id}/conversations/{cid}` → `{"id", "titulo", "turns": [...]}` con el mismo formato de turno que hoy devuelve `describe`.
  - `POST /api/documents/libraries/{id}/conversations/{cid}/close` → marca `"cerrada": true` (no borra nada).
  - `POST /api/documents/libraries/{id}/chat` suma `conversation_id: str | None` (si no viene, se crea una) y `filters: dict | None`.
- Produces: `chat_turn(client, store, settings, library, prompt, conversation_id: str | None = None, filters: dict | None = None)` en los dos motores.

- [ ] **Step 1: Write the failing tests** `test_conversaciones_separadas` (dos conversaciones: la segunda pregunta de la conversación B no ve el historial de A; el turno se guarda en `chats/local/<cid>/turno_1.json`) y `test_conversacion_cerrada_no_se_lista` (crear una vacía, cerrarla: `GET /conversations` no la devuelve, la otra sigue, y la carpeta sigue en disco).
- [ ] **Step 2:** Run `uv run pytest -k conversacion -v` → Expected: FAIL (404 en `/conversations`).
- [ ] **Step 3:** Implementar. `describe` sigue mostrando todos los turnos de la biblioteca (para la pestaña Bibliotecas): el glob pasa a `chats/**/turno_*.json`. Los turnos viejos sueltos en `chats/local/` (si los hay) no aparecen como conversación.
- [ ] **Step 4:** Run los tests → PASS; suite completa sin fallas nuevas.
- [ ] **Step 5:** Commit `feat: conversaciones separadas en el chat de la biblioteca`.

### Task 6: Filtros en el chat

**Files:**
- Modify: `backend/app/pipelines/documents/local_library.py` (`chat_turn`, `make_chat_engine`)
- Test: `backend/tests/pipelines/documents/test_local_library.py`

**Interfaces:**
- Consumes: `make_retriever(..., filters=...)` (tarea 3), `to_filters(filters)` (ya existe), `chat_turn(..., filters=...)` (tarea 5).
- Produces: el turno guardado incluye `"request": {..., "filters": filters}`.

- [ ] **Step 1: Write the failing tests** `test_chat_con_filtro_solo_usa_esa_clase` (con `filters={"nombre": "clase.pdf"}`, todas las `sources` son de `clase.pdf`) y `test_chat_con_filtros_sin_paginas` (filtros que no coinciden con nada: el chat manda un evento `text_delta` con "No encontré páginas con esos filtros." y un `stop`, sin llamar al modelo; el turno se guarda).
- [ ] **Step 2:** Run `uv run pytest -k filtro -v` → FAIL.
- [ ] **Step 3:** Implementar: validar los filtros con `to_filters` antes de abrir el índice (un filtro mal armado sigue dando 409, como en la búsqueda de prueba). Si la búsqueda filtrada no trae ninguna página, responder el mensaje fijo sin llamar a OpenAI.
- [ ] **Step 4:** Run → PASS; suite completa.
- [ ] **Step 5:** Commit `feat: filtros por metadata en el chat`.

### Task 7: Cada paso del wizard declara qué paso necesita

**Files:**
- Modify: `backend/app/pipelines/documents/pipeline.py` (`describe_run`, `start_step`, `reset_following`)
- Modify: `backend/app/pipelines/documents/steps/s2_parse.py` … `s6_extract.py` (constante `REQUIRES`)
- Test: `backend/tests/pipelines/documents/test_wizard_flow.py`

**Interfaces:**
- Produces: en cada módulo de paso, `REQUIRES: str | None` — `s1_upload`: `None`; `s2_parse`: `"upload"`; `s3_split`, `s4_classify`, `s5_schema`: `"parse"`; `s6_extract`: `"schema"`.
- Produces: `locked` de cada paso = su `REQUIRES` no está en `done`. `reset_following(store, run, name)` vuelve a pendiente **solo** los pasos que necesitan a ese (y los que necesitan a esos), no todos los que vienen después.

- [ ] **Step 1: Write the failing tests** `test_classify_corre_sin_split` (con el parse terminado y Split pendiente, `POST /steps/classify` responde 200) y `test_repetir_split_no_borra_classify` (Split y Classify hechos; repetir Split deja Classify en `done`).
- [ ] **Step 2:** Run `uv run pytest tests/pipelines/documents/test_wizard_flow.py -k "sin_split or no_borra" -v` → FAIL (409 "Primero tiene que terminar el paso anterior.").
- [ ] **Step 3:** Implementar. El mensaje de error pasa a nombrar el paso que falta: "Primero tiene que terminar el paso Parse." En el frontend, el Stepper ya usa `locked`, así que no cambia; revisar que `DocumentsWizard.tsx` no asuma el orden en otro lado.
- [ ] **Step 4:** Run → PASS; suite completa; `npm run build`.
- [ ] **Step 5:** Commit `feat: cada paso del wizard pide solo el paso que necesita`.

### Task 8: Las unidades de la materia como reglas de Classify

**Files:**
- Modify: `backend/app/pipelines/documents/steps/s4_classify.py` (`DEFAULTS["rules"]`)
- Modify: `docs/bitacora.md`

**Interfaces:**
- Produces: los valores de `tipo` en la metadata: `redes_neuronales`, `procesamiento_del_lenguaje_natural`, `procesamiento_digital_de_imagenes`, `aprendizaje_profundo_en_imagenes`, `temas_complementarios`, `presentacion_de_la_materia`. El frontend (tarea 10) los muestra con estos nombres: "Redes neuronales", "PLN", "Procesamiento de imágenes", "Aprendizaje profundo en imágenes", "Temas complementarios", "Presentación de la materia".

- [ ] **Step 1:** Reemplazar las reglas por estas 6. Las descripciones de las 4 unidades se copian **textuales** de `00 Presentación.pdf`, págs. 10 a 13 (están en el `document.md` de esa corrida). Las otras dos: `temas_complementarios` → "Temas de la materia que no están en el temario de las unidades: modelos multimodales (visión y lenguaje), sesgo, ética y evaluación robusta de modelos"; `presentacion_de_la_materia` → "Presentación del curso: docentes, temario completo, unidades y condiciones de aprobación".
- [ ] **Step 2:** Correr Classify en las 14 corridas (`POST /api/documents/runs/{id}/steps/classify` y consultar hasta `done`). Verificar que el `usage` de cada job sea 0; si no lo es, frenar y avisar.
- [ ] **Step 3:** Comparar la unidad de cada clase con lo esperado (01–02 redes neuronales; 03–05 PLN; 06 procesamiento de imágenes; 07–11 aprendizaje profundo en imágenes; 12–13 temas complementarios; 00 presentación). Anotar en la bitácora la tabla con la unidad, la confianza y el razonamiento de cada una. Si alguna no coincide, se deja como la eligió Classify y se anota (no se corrige a mano).
- [ ] **Step 4:** Volver a sumar las 14 corridas a la biblioteca (sacar y agregar) y sincronizar. Verificar con `POST /search` y `filters: {"tipo": "procesamiento_del_lenguaje_natural"}` que solo vuelvan páginas de las clases 03 a 05.
- [ ] **Step 5:** Commit `feat: reglas de Classify con las unidades de la materia`. Revisión del usuario.

---

## Fase 4 · La página principal

Todo en una carpeta nueva: `frontend/src/pipelines/documents/chat/`. Estilo: el mismo del frontend actual (componentes de `@/components/ui`, Tailwind, colores de cada herramienta como en el README: azul LlamaCloud, verde LlamaIndex, violeta Voyage, rosa OpenAI). Verificación de cada tarea: `npm run build` sin errores y prueba en el navegador con el backend real.

### Task 9: La sección Chat y el recorrido del proyecto

**Files:**
- Create: `frontend/src/pipelines/documents/chat/ChatPage.tsx` (arma la página: recorrido fijo arriba, pestañas, conversación, cuadro de pregunta)
- Create: `frontend/src/pipelines/documents/chat/ProjectJourney.tsx` (las 5 cajas del recorrido; cada una se abre con su explicación)
- Create: `frontend/src/pipelines/documents/chat/explicaciones.ts` (los textos de las explicaciones, en un solo lugar)
- Modify: `frontend/src/App.tsx` (pestaña `chat` primera y por defecto: `Chat · Documentos · Bibliotecas`)

**Interfaces:**
- Consumes: `listLibraries()` y `listRuns()` (ya existen). La biblioteca del chat es la local con la sincronización `done` más reciente.
- Produces: `explicaciones.ts` exporta `RECORRIDO: { id: 'pdf' | 'parse' | 'chunks' | 'voyage' | 'openai'; titulo: string; herramienta: string; queHace: string; porQue: string }[]` y `DETRAS_DE_ESCENA: Record<'busqueda' | 'reranker' | 'respuesta', string>`.

- [ ] **Step 1:** Escribir `explicaciones.ts`: una o dos frases por caja, del estilo de los comentarios del código (qué hace y por qué se eligió). Los números **no** van en el texto fijo: salen de la API (páginas y documentos de la biblioteca, créditos totales de las corridas con `total_credits`, chunks de la última sincronización).
- [ ] **Step 2:** `ProjectJourney` muestra las cajas con sus números reales; queda fijo (`sticky`) arriba de la conversación.
- [ ] **Step 3:** `App.tsx`: la pestaña `chat` va primera y es la inicial (`#chat`); si no hay biblioteca sincronizada, la página lo dice y manda a Bibliotecas.
- [ ] **Step 4:** `npm run build` → sin errores. En el navegador: la pestaña Chat abre primero y el recorrido muestra 14 documentos, 410 páginas y los créditos reales.
- [ ] **Step 5:** Commit `feat: el chat como página principal, con el recorrido del proyecto`.

### Task 10: Pestañas de conversación, conversación acumulada y filtros

**Files:**
- Create: `frontend/src/pipelines/documents/chat/ConversationTabs.tsx`
- Create: `frontend/src/pipelines/documents/chat/ChatThread.tsx`
- Create: `frontend/src/pipelines/documents/chat/ChatFilters.tsx`
- Modify: `frontend/src/pipelines/documents/libraries/api.ts` (funciones de conversaciones y `chat` con `conversationId` y `filters`)
- Modify: `frontend/src/pipelines/documents/libraries/LibraryChat.tsx` (pasa a usar la firma nueva de `chat`)

**Interfaces:**
- Consumes: las rutas de la tarea 5 y los filtros de la tarea 6.
- Produces en `api.ts`: `listConversations(libraryId)`, `createConversation(libraryId)`, `getConversation(libraryId, conversationId)`, `closeConversation(libraryId, conversationId)` y `chat(libraryId, prompt, onEvent, options?: { conversationId?: string; filters?: Record<string, string> })`.
- Produces: los valores de los filtros salen de `library.documents[].metadata`: `tipo` (unidad, con las etiquetas de la tarea 8) y `nombre` (clase). Sin filtros elegidos, no se manda `filters`.

- [ ] **Step 1:** `ConversationTabs`: una pestaña por conversación (título de la API), una "×" para cerrarla y un "+" para crear una. Al cargar la página se abren las mismas pestañas; si no hay ninguna, se crea una.
- [ ] **Step 2:** `ChatThread`: los turnos se acumulan; al terminar una respuesta baja hasta el final y el foco vuelve al cuadro de pregunta. Mientras responde, el cuadro y el botón quedan deshabilitados.
- [ ] **Step 3:** `ChatFilters`: dos selectores (Unidad y Clase), vacíos por defecto, con un texto que diga "Sin filtros, busca en las 14 clases".
- [ ] **Step 4:** `npm run build` → sin errores. En el navegador: dos pestañas con preguntas distintas, cerrar una, recargar (siguen las mismas); una pregunta con filtro de unidad solo cita clases de esa unidad.
- [ ] **Step 5:** Commit `feat: pestañas de conversación y filtros en el chat`.

### Task 11: Citas por documento y detrás de escena

**Files:**
- Create: `frontend/src/pipelines/documents/chat/AnswerSources.tsx`
- Create: `frontend/src/pipelines/documents/chat/BehindTheScenes.tsx`
- Modify: `backend/app/pipelines/documents/settings.py` y `local_library.py` (`total_usage`: suma `"costo_estimado_usd"`)
- Test: `backend/tests/pipelines/documents/test_local_library.py`

**Interfaces:**
- Consumes: el evento `tool_result` de cada turno, con `documento`, `pagina`, `rerank_score`, `texto` y `metadata.corrida`; el evento `stop` con `usage`.
- Produces: en `DocumentsSettings`, `library_chat_price_input_usd: float = 0.05` y `library_chat_price_output_usd: float = 0.40` (por millón de tokens, de la lista de precios de OpenAI del 21/11). `total_usage` suma `"costo_estimado_usd": float`.

- [ ] **Step 1: Write the failing test** `test_usage_trae_costo_estimado`: con 1.000.000 de tokens de entrada y 100.000 de salida, `total_usage(...)["costo_estimado_usd"] == 0.09`.
- [ ] **Step 2:** Run `uv run pytest -k costo -v` → FAIL; implementar; → PASS.
- [ ] **Step 3:** `AnswerSources`: las páginas que llegaron al modelo, agrupadas por documento; cada página se abre con su texto y su captura (`/api/documents/runs/{corrida}/files/2_parse/images/page_{N}.jpg`).
- [ ] **Step 4:** `BehindTheScenes` (desplegable): ① búsqueda (cuántos candidatos y el modo), ② reranker (las páginas elegidas con su puntaje), ③ respuesta (modelo, tokens y costo, marcado como "estimado"), cada uno con su línea de `DETRAS_DE_ESCENA`.
- [ ] **Step 5:** `npm run build` y prueba en el navegador con "¿Qué tienen en común ResNet y U-Net?": aparecen las clases 07 y 10 agrupadas, las capturas abren, y el detrás de escena muestra los números del turno guardado.
- [ ] **Step 6:** Commit `feat: citas por documento y detrás de escena en el chat`. Revisión del usuario.

---

## Fase 5 · Cierre

### Task 12: Documentación, Docker y guion de la demo

**Files:**
- Modify: `README.md`, `docs/estado.md`, `docs/plan.md`, `docs/bitacora.md`
- Create: `docs/guion-demo.md`

- [ ] **Step 1:** Actualizar README, estado y plan con lo hecho (búsqueda elegida, filtros, página principal) y sus números.
- [ ] **Step 2: Pruebas e2e en el navegador** (con el backend y el frontend de desarrollo, manejando el navegador con Playwright): abrir la app y ver la pestaña Chat primero, con el recorrido y sus números reales; crear dos conversaciones, preguntar en cada una, cerrar una y recargar; una pregunta que cruza clases (citas de las clases 07 y 10, capturas que abren, detrás de escena con tokens y costo estimado); una pregunta con filtro de unidad; la trampa de Q-learning; filtros que no dejan páginas; el wizard con Classify sin Split; la pestaña Bibliotecas con los evals. Anotar cada resultado en la bitácora. **Docker recién después de que pasen todas, con el OK del usuario.**
- [ ] **Step 3:** `docker compose up --build -d` → Expected: contenedor `healthy`, `/api/config` responde y la pestaña Chat abre en `http://localhost:8000`.
- [ ] **Step 3:** Escribir `docs/guion-demo.md`: qué mostrar del recorrido para explicar el stack y 4 o 5 preguntas para hacer en vivo (una que cruce clases, una con filtro de unidad, la trampa de Q-learning), con lo que se espera ver en cada una.
- [ ] **Step 4:** Leer el guion contra la app y corregir lo que no coincida.
- [ ] **Step 5:** Commit `docs: guion de la demo y documentación al día`. Revisión final del usuario.
