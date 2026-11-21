# Diseño · El chat como página principal, búsqueda entre clases y filtros por unidad

**Fecha:** 21/11/2026 · **Estado:** borrador para aprobar (revisado por un constructor; preguntas contestadas por el autor) · **Proyecto:** Parla RAG

## 1. Para qué

El proyecto se presenta en una clase por **Google Meet, compartiendo pantalla**. El orden de la presentación es:

1. Explicar el **stack** del proyecto.
2. Hacerle **preguntas en vivo** al chat sobre el material de Aprendizaje Automático II y mostrar las respuestas.

Por eso:

- **El chat tiene que ser la página principal.** Hoy está tres clics adentro (Bibliotecas → elegir biblioteca → pestaña de chat).
- **Las respuestas tienen que salir de todas las clases** y **relacionarlas**, no solo responder con una.
- **La app se tiene que explicar sola**, como los comentarios del código: cada proceso y cada resultado con una explicación corta. Le sirve al autor como apoyo para presentar (no para leer) y a los compañeros para entender.

## 2. Objetivos, no-objetivos y anti-objetivos

**Objetivos**
- Página principal con el chat: el recorrido del proyecto fijo arriba, la conversación acumulándose abajo y el cursor listo en el cuadro de pregunta.
- Cada respuesta muestra de qué documentos y páginas salió, agrupado por documento, y un "detrás de escena" con la búsqueda, el reranker y la respuesta explicados.
- La búsqueda trae páginas de **varias clases** cuando la pregunta lo pide.
- Filtros opcionales por **unidad** y por **clase**, apagados por defecto (sin filtros busca en todo).
- Medir cada cambio con evals antes de darlo por bueno.

**No-objetivos**
- Volver a parsear (el parse de las 410 páginas queda como está).
- Usar Extract para la metadata de los filtros.
- `SubQuestionQueryEngine`, embeddings contextualizados de Voyage o las notebooks: quedan en el roadmap.
- El índice de LlamaCloud.

**Anti-objetivos** (cosas que harían fallar el trabajo aunque funcione)
- Que una pregunta que cruza clases se responda con páginas de una sola clase.
- Explicaciones en pantalla con datos inventados: todo número que se muestre sale de la API o de lo guardado.
- Que el chat tarde tanto que en vivo por Meet se note: el objetivo es responder en unos pocos segundos.
- Que los filtros "deduzcan" datos que no están escritos.

## 3. Restricciones

- **Solo lo nativo** de LlamaCloud, LlamaParse y LlamaIndex, con sus integraciones oficiales (Voyage AI, OpenAI). Nada de otros frameworks.
- **Código simple**, con un comentario en español arriba de cada función (`#` o `//`).
- **Carpeta-DB:** todo se guarda en `backend/data/`.
- **Créditos:** pedir el OK antes de cualquier llamada paga. Classify sobre un parse ya hecho costó 0 en las pruebas; igual se verifica el `usage` y se anota.
- **Registrar todo** en `docs/bitacora.md`, con los tokens de Voyage y el costo de OpenAI.
- **Español rioplatense** en todo texto al usuario.

## 4. Opciones consideradas

### 4.1 Cómo buscar para que la respuesta cruce clases

| Opción | Qué es | A favor | En contra |
|---|---|---|---|
| 1 · Más páginas | Subir de 6 a 12 las páginas que lee el modelo (y de 18 a 36 los candidatos) | Solo configuración | No garantiza variedad: las 12 pueden ser de una clase |
| **2 · MMR + más páginas** ✅ | Modo nativo de la búsqueda vectorial de LlamaIndex que penaliza candidatos parecidos a los ya elegidos | Ataca la variedad, una sola búsqueda, rápido | No probado: el reranker podría volver a concentrar |
| 3 · Sub-preguntas | `SubQuestionQueryEngine`: una sub-pregunta por clase y una respuesta final | La más completa | Lenta en vivo (15–30 s), no es un chat, `gpt-5-nano` parte mal las preguntas |

**Elegida: la 2**, por el autor. Se decide midiendo: 6 páginas, 12 páginas y 12 con MMR.

### 4.2 De dónde salen los filtros

| Opción | A favor | En contra |
|---|---|---|
| Extract con un schema chico | Campos a medida | La unidad no está escrita en las diapositivas de cada clase (habría que deducirla); ~600 créditos |
| **Classify + `nombre`** ✅ | Classify sobre un parse cuesta 0, explica su elección (razonamiento) y su resultado ya entra a la metadata como `tipo`. La clase ya es filtrable por `nombre` | El nombre del campo es `tipo`, no `unidad` |

**Elegida: Classify + `nombre`**, por el autor.

### 4.3 Cómo es la página principal

Se mostraron tres bocetos: A (chat con guía al costado), B (chat con el "detrás de escena" de cada respuesta) y C (portada con el recorrido del stack y el chat abajo). **Elegida: C + B**, por el autor.

## 5. Lo que ya está decidido

### 5.1 La página principal

```
┌──────────────────────────────────────────────────────────────┐
│ Parla RAG     [ Chat ] [ Documentos ] [ Bibliotecas ]        │
├──────────────────────────────────────────────────────────────┤
│ FIJO ARRIBA: el recorrido del proyecto                       │
│ 📄 14 PDF → 🔵 Parse → 🟢 1 página = 1 chunk → 🟣 Voyage → 🌸 OpenAI │
│ (cada caja se abre: qué hace, por qué se eligió, cuánto costó)│
├──────────────────────────────────────────────────────────────┤
│ [ Conversación 1 ] [ ¿Qué es RAG… ] [ + ]                    │
│ LA CONVERSACIÓN (se acumula hacia abajo, como Claude/ChatGPT)│
│  🧑 pregunta 1                                               │
│  🤖 respuesta que relaciona las clases, con citas            │
│     📘 07 Clasificación… — pág. 27 · 28   (se abren)         │
│     📗 10 Segmentación… — pág. 12                            │
│     ▸ Detrás de escena: ① búsqueda ② reranker ③ respuesta   │
│  🧑 pregunta 2 …                                             │
├──────────────────────────────────────────────────────────────┤
│ Filtros (apagados): Unidad [▾]  Clase [▾]                    │
│ [ Preguntale a las 14 clases…                        ] [➤]   │
└──────────────────────────────────────────────────────────────┘
```

- **El recorrido queda fijo arriba** y no se mueve con la conversación.
- **La conversación se acumula:** una pregunta nueva no borra las anteriores. Después de cada respuesta, la vista baja hasta el final y el cursor vuelve al cuadro de pregunta.
- **Citas agrupadas por documento.** Cada página citada se puede abrir con su texto y su captura de Parse, para comprobar la cita (con `gpt-5-nano` las citas a veces vienen mal: ver la bitácora del 21/11).
- **"Detrás de escena"** desplegable en cada respuesta: la búsqueda (candidatos), el reranker (las páginas elegidas con su puntaje) y la respuesta (modelo, tokens y costo), cada paso con una línea que explica qué es.
- **Documentos y Bibliotecas** siguen como secciones, para mostrar el proceso.
- **Pestañas de conversación**, por pedido del autor: arriba de la conversación (debajo del recorrido fijo) hay una pestaña por conversación y un **"+"** para abrir una nueva. Cada conversación tiene su propio historial (el chat usa el historial para entender las preguntas de seguimiento).
  - *Decisiones del constructor (revisables):* la pestaña se llama como las primeras palabras de su primera pregunta; cerrarla la oculta pero la conversación queda en disco para auditar; al recargar la app vuelven las mismas pestañas.
  - En el backend, cada conversación pasa a ser una carpeta propia dentro de la biblioteca (`chats/local/<conversación>/turno_N.json`), en lugar de una sola conversación por biblioteca.
- **La biblioteca del chat:** hay una sola ("Aprendizaje Automático II"). *Decisión del constructor:* el chat usa la última biblioteca sincronizada, sin selector.

### 5.2 La búsqueda

- MMR como modo de la búsqueda vectorial del chat (nativo de LlamaIndex: `vector_store_query_mode="mmr"`), y cantidad de páginas configurable. Los valores finales salen de los evals.
- *Decisión del constructor:* los evals miden también **cuánto tarda cada respuesta**. Límite: **10 segundos**. Si dos opciones buscan igual de bien, gana la más rápida.
- **Los evals tienen que usar exactamente la misma búsqueda que el chat**, si no, miden otra cosa.
- Las instrucciones del chat suman: relacionar los documentos cuando la pregunta los involucra, y citar cada uno.

### 5.3 Los filtros

- **Unidad:** Classify sobre cada una de las 14 corridas, con **6 reglas**. Cuatro salen del texto de la presentación de la materia (`00 Presentación.pdf`, págs. 10 a 13): Redes neuronales, Procesamiento del lenguaje natural, Procesamiento digital de imágenes y Aprendizaje profundo aplicado a imágenes. Las otras dos las sumó el autor, porque hay clases que no figuran en ninguna unidad: **"Temas complementarios"** (lo esperado: 12 Modelos multimodales y 13 Sesgo y robustez) y **"Presentación de la materia"** (lo esperado: 00). Se guarda el razonamiento de cada elección y se compara a mano con lo esperado. Classify nunca se corrió en estas 14 corridas, así que no se pisa ningún resultado anterior.
- **Clase:** el `nombre` del documento, que ya está en la metadata.
- **Classify pide solo el parse** (decisión del autor, opción B): hoy el wizard exige que cada paso termine el anterior (`pipeline.py`), así que Classify esperaría a Split. Split no le aporta nada a Classify, no informa lo que cobra (~1.230 créditos según la lista de precios para las 14 clases) y no tiene sentido en documentos de una sola clase. Cada paso pasa a declarar qué paso necesita: Split, Classify y Schema necesitan Parse; Extract necesita Schema. Split queda opcional.
- Después de Classify hay que **volver a sumar las corridas a la biblioteca y sincronizar**, para que la metadata nueva entre al índice.
- El chat tiene que **aceptar filtros** (hoy solo los acepta la búsqueda de prueba).

## 6. Las fases, con verificación y auditoría

Cada fase termina con: **tests** (`uv run pytest`), **Ruff**, **build del frontend** si se tocó, **la medición** que corresponda, **una entrada en la bitácora** (con créditos, tokens y costo) y **una revisión del autor antes de pasar a la siguiente**.

| Fase | Qué | Cómo se verifica |
|---|---|---|
| **1 · Set de evals más exigente** | Sumar preguntas parafraseadas, que necesiten varias diapositivas y que crucen clases, con respuestas verificadas en el parse. Medir la línea de base (6 páginas, sin MMR) | Hit rate y MRR dejan de dar 1,0 en todo; las preguntas que cruzan clases miden cuántas clases llegan al modelo |
| **2 · Búsqueda entre clases** | MMR y cantidad de páginas configurables; la misma búsqueda en el chat y en los evals; instrucciones para relacionar documentos | Comparar 6 / 12 / 12 + MMR con el set nuevo; elegir por los números y anotar por qué |
| **3 · Filtros por unidad** | Reglas de Classify con las 4 unidades; correr Classify en las 14 corridas; re-sumarlas y sincronizar; filtros en el chat | El `usage` de Classify (se espera 0); revisar a mano la unidad y el razonamiento de cada clase; una búsqueda filtrada solo trae esa unidad |
| **4 · La página principal** | El chat como pestaña principal, con el recorrido fijo, las pestañas de conversación, la conversación acumulada, las citas por documento, el detrás de escena, los filtros y las explicaciones | Probarla en el navegador con preguntas reales; revisar que cada número que muestra salga de la API |
| **5 · Cierre** | README, estado y plan al día; probar Docker; un guion corto para la demo | Docker de punta a punta; leer el guion contra la app |

## 7. Lo que queda para quien lo construya

- El diseño visual (colores, tipografía, espaciado), siguiendo el estilo que ya tiene el frontend.
- Cómo partir los componentes de React y los textos exactos de las explicaciones (cortos, en rioplatense, del estilo de los comentarios del código).
- El umbral de MMR y los valores a probar, con tal de que se comparen con los evals.
- Las preguntas nuevas del set, con tal de que cada respuesta esperada salga del parse.
