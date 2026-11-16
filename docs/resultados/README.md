# Resultados de los evals

Los resultados de los evals de "BYMA 3T26", copiados de las corridas guardadas en `backend/data/documents/libraries/<id>/evals/<fecha>/`. Esas carpetas no van a git (están en la máquina donde se trabajó), así que acá queda la copia que sí se versiona. **Es la fuente de verdad de los números del [README](../../README.md).**

Cada fila es una pregunta del [set](../../backend/data/samples/byma/evals/preguntas.json) con una forma de cortar las páginas (`corte`): `oraciones`, `markdown` o `pagina`.

## `evals_busqueda.csv`

Lo que mide `RetrieverEvaluator` de LlamaIndex, con 18 candidatos y el reranker dejando 6, igual que el chat. Las 2 trampas no tienen página correcta y no aparecen.

| Columna | Qué es |
|---|---|
| `hit_rate` | 1 si llegó al modelo al menos un chunk de una página fuente; 0 si no |
| `mrr` | 1 / puesto del primer chunk correcto: 1 = primero, 0,5 = segundo, 0 = no llegó |
| `primera_pagina_encontrada` | La página del primer chunk que llegó al modelo |
| `corrida` | La carpeta de la corrida, dentro de `evals/` de cada biblioteca |

## `evals_respuestas.csv`

El chat responde cada pregunta sin historial y `deepseek-flash` hace de juez.

| Columna | Qué es |
|---|---|
| `fiel` | `FaithfulnessEvaluator`: la respuesta sale de los fragmentos que recibió el modelo |
| `correccion` | `CorrectnessEvaluator`: de 1 a 5, comparada con la respuesta esperada |
| `correcta` | `True` si `correccion` es 4 o más |
| `tokens_entrada` / `tokens_salida` | Los tokens de DeepSeek de la pregunta (chat y juez) |
| `referencia` | `vieja (contradicción)` en `datos-de-mercado-3t25` de oraciones y markdown: se juzgaron antes de corregir esa pregunta (ver la bitácora del 16/11) |

## Cómo se repiten

`POST /api/documents/libraries/{id}/evals` con `{"candidatos": 18}` (solo la búsqueda) o `{"candidatos": 18, "respuestas": true}`. Cada corrida queda en su carpeta `evals/<fecha>/`.
