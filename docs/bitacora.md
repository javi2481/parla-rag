# Bitácora del proyecto

Registro de todo lo que se hizo, se probó, se encontró y se gastó, para poder auditarlo.

- **Las entradas van en orden cronológico.** Cada una dice qué se hizo, qué salió, qué se encontró y qué se decidió.
- **Cada llamada paga** a LlamaCloud queda en el [registro de créditos](#registro-de-créditos). Los tokens de Voyage AI y el costo de OpenAI se anotan en la entrada de cada prueba.
- **Hasta el 15/11/2026** Parla era un solo proyecto con documentos y audio. Las entradas de audio (ElevenLabs) siguen en la bitácora de **parla-audio**.
- **El 21/11/2026 se cambió el corpus de ejemplo** por el material de Aprendizaje Automático II. Lo anterior a esa fecha quedó resumido en [Antecedentes](#antecedentes-hasta-el-2111): los hallazgos que siguen valiendo, sin el detalle de los documentos de prueba de entonces.
- **Los datos crudos de cada prueba** (lo que se pidió y la respuesta completa) quedan en `backend/data/verificacion/` o en la corrida correspondiente de `backend/data/documents/runs/`. Están fuera de git porque pesan mucho y traen links firmados temporales.

---

## Registro de créditos

**Antes del 21/11:** las pruebas de la construcción del wizard y de las bibliotecas (registros #1 a #30) gastaron **4.148 créditos**: el saldo pasó de 29.443 de 30.000 (13/11) a 25.295 (21/11), según el panel.

**Material de Aprendizaje Automático II** (21/11). Saldo informado por el usuario antes de #31: **25.295** de 30.000 (se renueva el 23/11).

| # | Fecha | Qué | Documento | Job | Opciones | Créditos | Saldo estimado |
|---|---|---|---|---|---|---|---|
| 31 | 21/11 13:09 | Parse desde el wizard (prueba de costo) | Clase 02 · Perceptrón multicapa, 9 págs. | `pjb-bmiiewkmelgd2l510tatjv6sn6es` | agentic · todas + 3 salidas extra | **155** (17 por página) | 25.140 |
| 32 | 21/11 13:25 | Parse (lote de las clases restantes) | 00 Presentación, 15 págs. | `pjb-x2w44fvm7d6vujffgfoiymidymp2` | agentic · todas + 3 salidas extra | 225 (15 por página) | 24.915 |
| 33 | 21/11 13:25 | Parse (lote de las clases restantes) | 01 Introducción a Redes Neuronales, 11 págs. | `pjb-xhj3boj76vosxyw7qr9r2beg7q6a` | agentic · todas + 3 salidas extra | 265 (24 por página) | 24.650 |
| 34 | 21/11 13:25 | Parse (lote de las clases restantes) | 03 PLN - Conceptos y técnicas de procesamiento, 45 págs. | `pjb-ywao3sguzturtsqho4wj4lbz9k93` | agentic · todas + 3 salidas extra | 715 (16 por página) | 23.935 |
| 35 | 21/11 13:26 | Parse (lote de las clases restantes) | 04 PLN - Modelos estadísticos y Representaciones Vectoriales, 32 págs. | `pjb-wtzeq3e3jlafs0ye9ni4v3j67myw` | agentic · todas + 3 salidas extra | 720 (22 por página) | 23.215 |
| 36 | 21/11 13:26 | Parse (lote de las clases restantes) | 05 PLN - Redes neuronales, 28 págs. | `pjb-1tjzcplazb1p6yoconq7nv74ur33` | agentic · todas + 3 salidas extra | 460 (16 por página) | 22.755 |
| 37 | 21/11 13:26 | Parse (lote de las clases restantes) | 06 Procesamiento digital de imágenes, 40 págs. | `pjb-tmvfm930d7ymyqd1td8s2xvpk2i9` | agentic · todas + 3 salidas extra | 600 (15 por página) | 22.155 |
| 38 | 21/11 13:26 | Parse (lote de las clases restantes) | 07 Clasificación de imágenes, 36 págs. | `pjb-hg5ef9f4uwjzvi85jfap8lznug6n` | agentic · todas + 3 salidas extra | 620 (17 por página) | 21.535 |
| 39 | 21/11 13:26 | Parse (lote de las clases restantes) | 08 Transferencia de aprendizaje, 24 págs. | `pjb-a21fuc92ikqb5qpmx76vrw0396sp` | agentic · todas + 3 salidas extra | 360 (15 por página) | 21.175 |
| 40 | 21/11 13:27 | Parse (lote de las clases restantes) | 09 Detección de objetos, 41 págs. | `pjb-aqdjulwdulqe4t0nca701k9mnvy2` | agentic · todas + 3 salidas extra | 1.035 (25 por página) | 20.140 |
| 41 | 21/11 13:27 | Parse (lote de las clases restantes) | 10 Segmentación de imágenes, 26 págs. | `pjb-2n297kjkp4s15obxh2xoyrxsz234` | agentic · todas + 3 salidas extra | 390 (15 por página) | 19.750 |
| 42 | 21/11 13:27 | Parse (lote de las clases restantes) | 11 Generación de imágenes, 34 págs. | `pjb-grlv42qoj69ue76uaopiihjiazu8` | agentic · todas + 3 salidas extra | 550 (16 por página) | 19.200 |
| 43 | 21/11 13:27 | Parse (lote de las clases restantes) | 12 Modelos multimodales, 33 págs. | `pjb-mxwdl1149p7r5g8qxarpe5bk46h3` | agentic · todas + 3 salidas extra | 615 (19 por página) | 18.585 |
| 44 | 21/11 13:27 | Parse (lote de las clases restantes) | 13 Sesgo, ética y evaluación robusta de modelos, 36 págs. | `pjb-w3zk450tri3vwddh72der0vl0mg3` | agentic · todas + 3 salidas extra | 540 (15 por página) | 18.045 |

**Saldo estimado después de #44:** 25.295 − 7.250 = **18.045**. Hay que confirmarlo con el panel.

**Llamadas que no costaron nada** (comprobado): volver a pedir el resultado de un parse terminado (`parsing.get`), `validate_schema`, `configurations.create`, la subida de archivos y Classify sobre un parse ya hecho. Las 3 salidas extra de `additional_outputs` tampoco suman costo.

**No informan lo que cobran** (`usage` vacío): Split, `generate_schema` y las validaciones. Hay que conciliarlos con el panel.

---

## Antecedentes (hasta el 21/11)

Lo que se construyó y se aprendió con el corpus anterior, y que sigue valiendo:

- **13/11 · Fases 0 a 3:** reorganización por pipeline, relevamiento de la API ([informe-fase-1.md](informe-fase-1.md)), motor de corridas en carpetas y los seis pasos del wizard.
- **Parse sin `max_pages`:** Split rechaza con error 400 un parse limitado. Por eso el parse es siempre completo.
- **Costos medidos:** Parse agentic con todas las opciones, de 15 a 39 créditos por página según los gráficos; Extract agentic con citas y confianza, **15 por página**, sin importar cuántos campos tenga el schema; Classify sobre un parse, 0.
- **El parse no es determinístico:** el mismo archivo, con la misma versión, dio otra confianza, y una vez inventó los valores de un gráfico con confianza 0,85. Los datos de gráficos hay que verificarlos contra la captura.
- **Los campos obligatorios hacen inventar:** con el schema automático (todos obligatorios), Extract devolvió ceros en campos que no existían, con cita a un "0 %" real de otro renglón. Con la opción "solo identidad obligatoria" y la regla "vacío si no consta", no inventó nada.
- **`format: date` no se respeta:** Extract devuelve la fecha con el formato del documento.
- **13/11 · El índice v2 de LlamaCloud da 403 con el plan gratis.** Se armó el motor local con LlamaIndex y Voyage AI (14/11). LlamaParse y LlamaIndex no tienen embeddings propios: hace falta una integración (Voyage).
- **Voyage AI sin medio de pago** permite 3 pedidos y 10.000 tokens por minuto. Con la tarjeta cargada se fue el límite; los 200 millones de tokens gratis se mantienen.
- **15/11 · Separación en parla-rag y parla-audio.**
- **16/11 · Corte en chunks:** se compararon los tres cortes nativos de LlamaIndex con evals. El corte por oraciones separó una tabla de su encabezado y el chat **supuso las unidades**; el de Markdown armó chunks enormes que buscaban peor. Ganó **una página = un chunk**, que quedó por defecto.
- **16/11 · Evals nativos de LlamaIndex** (`RetrieverEvaluator`, `FaithfulnessEvaluator`, `CorrectnessEvaluator`), con el set de preguntas versionado junto a los documentos. El eval también auditó al set: dos fallas eran errores en las respuestas esperadas.
- **16/11 · Paso 7 del wizard, CI con GitHub Actions, Ruff sin avisos y Docker** verificado de punta a punta.

---

## Entradas

### 21/11 · Cambio de corpus, OpenAI en lugar de DeepSeek y parse de prueba de la clase 02 (155 créditos)

- **Corpus nuevo:** el material teórico de Aprendizaje Automático II en `backend/data/samples/aprendizaje-automatico-ii/`: 14 PDF (410 páginas) y 32 notebooks, una carpeta por clase. Sin videos, TPs ni entornos virtuales. Los documentos del ejemplo anterior se borraron del repo.
- **Notebooks:** LlamaParse no acepta `.ipynb` (no figura en la [lista oficial de formatos](https://developers.llamaindex.ai/llamaparse/general/supported_document_types/)). Por ahora no se parsean: la teoría está en los PDF.
- **Modelo del chat:** `gpt-5-nano` de OpenAI (el más barato de la [lista de precios](https://developers.openai.com/api/docs/pricing): USD 0,05 entrada / 0,40 salida por millón de tokens) con `reasoning_effort=minimal`. Integración oficial `llama-index-llms-openai`; se sacó `llama-index-llms-deepseek`.
- **Bug encontrado y arreglado:** el parse terminó en LlamaCloud, pero el backend falló al guardar `response.json` con `UnicodeEncodeError: 'charmap' codec can't encode character '○'`. **Causa:** `write_text` y `read_text` sin `encoding`; en Windows Python usa cp1252, en Linux y Docker UTF-8 (por eso no había aparecido). **Arreglo:** `encoding="utf-8"` en `store.py` (`write_json`, `read_json`) y en `s2_parse.py` (`document.md`, `text.txt`). Los archivos de la corrida que ya se habían guardado en cp1252 se pasaron a UTF-8 y el resultado se volvió a pedir (gratis).
- **Resultado del parse (#31):** 9 páginas, 155 créditos (**17 por página**), confianza del documento 85 %, 2 tablas, 5 gráficos convertidos en tablas, 1 tabla unida entre las páginas 5 y 6. La API marca las páginas 5 y 6 para revisar (la 6 con 30 % de confianza) y no informa el motivo.
- **Estimación para las 410 páginas:** a 17 por página, unos **7.000 créditos**. Es solo una referencia: el costo depende de los gráficos de cada página.

### 21/11 · Parse de las 13 clases restantes (7.095 créditos; 7.250 con la clase 02)

- **Qué se hizo:** con el OK del usuario, un script (fuera del repo) subió los 13 PDF por la API del wizard (`POST /runs` y `POST /runs/{id}/steps/parse`) y revisó cada 10 s el estado de cada parse. Los 13 corrieron en paralelo y terminaron en **84 s**, sin errores.
- **Resultado:** 14 corridas en `done`, **410 páginas** y **7.250 créditos** en total (registro #31 a #44). Promedio: **17,7 créditos por página**, entre 15 y 25.
- **Lo más caro:** `09 Detección de objetos` cobró 25 por página y `01 Introducción a Redes Neuronales`, 24. La API no desglosa el costo por página, así que no se puede decir qué páginas encarecieron cada parse.
- **Confianza del documento** (la informa LlamaParse): de 78 % (`09 Detección de objetos`) a 99 % (`00 Presentación`). Las más bajas, además de la 09, son `05 PLN - Redes neuronales` (79 %) y la clase 02 (85 %). La API no dice el motivo: hay que comparar las capturas con el Markdown de las páginas marcadas.
- **Con el arreglo de UTF-8** de la entrada anterior, no volvió a fallar el guardado.

### 21/11 · Biblioteca "Aprendizaje Automático II" (0 créditos de LlamaCloud; tokens gratis de Voyage)

- **Qué se hizo:** se creó la biblioteca local `2026-11-21_133046_aprendizaje-automatico-ii` con las 14 corridas parseadas y se sincronizó.
- **Resultado:** 14 documentos, **410 páginas en 410 chunks** (corte `pagina`), embeddings `voyage-4`, reranker `rerank-2.5`. La sincronización tardó **6 s** y usó el parse del wizard: no se volvió a parsear nada.
- **Costo:** 0 créditos de LlamaCloud. Los embeddings de Voyage entran en los tokens gratis; la API no devuelve el conteo en esta llamada, así que no queda registrado.
- **Nota:** el script que la armó (fuera del repo) leía mal el estado de la sincronización y siguió consultando después de que terminó. Se frenó a mano; no afectó la biblioteca.

### 21/11 · Set de preguntas de Aprendizaje Automático II y evals de búsqueda (sin costo: tokens gratis de Voyage)

- **Set:** `backend/data/samples/aprendizaje-automatico-ii/evals/preguntas.json`, con **18 preguntas** (16 con fuente y 2 trampas) repartidas entre 11 de las 14 clases. Tipos: dato, explicación y comparación. Estado: borrador, falta la revisión del usuario.
- **Cómo se verificó:** cada respuesta esperada sale del Markdown del parse. Para cada dato se buscó en las 410 páginas en cuáles aparece, y todas esas páginas quedaron como fuente (por ejemplo, ResNet está en las págs. 27 y 28 de la clase 07). Las trampas se comprobaron por ausencia: «Q-learning», «Bellman», «reinforcement» y «recompensa» no aparecen en ninguna página; la presentación nombra los parciales sin dar fecha.
- **Evals de búsqueda** (corte `pagina`, 18 candidatos, rerank a 6): **hit rate 1,0 y MRR 1,0**. En las 16 preguntas con fuente, la primera página que llega al modelo es una de las correctas.
- **Cuidado al leer el número:** las preguntas se armaron mirando los títulos de las diapositivas, y usan casi las mismas palabras. Mide que la búsqueda encuentra lo que está escrito, no que entienda preguntas formuladas de otra manera. Para eso harían falta preguntas parafraseadas o que crucen clases.
- **Costo:** 0 créditos de LlamaCloud y 0 de OpenAI. Voyage: 16 consultas con embedding y rerank, dentro de los tokens gratis; la API no devuelve el conteo.

### 21/11 · Evals con respuestas: gpt-5-nano responde y juzga (~USD 0,006 de OpenAI; tokens gratis de Voyage)

- **Corrida:** `libraries/2026-11-21_133046_aprendizaje-automatico-ii/evals/2026-11-21_134830/`, con las 18 preguntas del set. El chat responde cada una sin historial y `gpt-5-nano` (`reasoning_effort=minimal`) hace de juez con `FaithfulnessEvaluator` y `CorrectnessEvaluator` de LlamaIndex.
- **Resultado:** búsqueda con hit rate 1,0 y MRR 1,0; **17 de 18 respuestas fieles** a los fragmentos; **15 de 18 correctas** (4 o más de 5); corrección promedio 3,78.
- **Tokens de OpenAI:** 82.396 de entrada y 5.225 de salida, 0 de razonamiento (por `minimal`). Con los precios de la [lista oficial](https://developers.openai.com/api/docs/pricing) (USD 0,05 y 0,40 por millón) son unos **USD 0,006**. La cuenta es nuestra: la API devuelve tokens, no dólares.
- **Las 3 que el juez marcó como incorrectas, leídas una por una:**
  - `unet-origen` (3 de 5): **falla real del chat.** Respondió el "para qué" (imágenes médicas con pocos ejemplos) pero no el "dónde" (Universidad de Freiburg, 2015), aunque estaba en la misma página que recibió.
  - `equidad-ejemplo` (3 de 5): **la respuesta es correcta, pero la cita está mal.** Dice que el modelo cumple solo la paridad predictiva, que es lo que dice la pág. 21, pero cita la **pág. 17**. La búsqueda había traído la 21 en primer lugar.
  - `trampa-q-learning` (2 de 5, y "no fiel"): **el chat hizo lo correcto** (dijo que Q-learning y Bellman no están en los documentos) y el juez lo penalizó por no explicar el tema. Es un error del juez: `CorrectnessEvaluator` no tuvo en cuenta que la respuesta esperada era justamente esa. Lo "no fiel" viene de que el chat pegó al final una lista de páginas que no tenían nada que ver.
- **Otra cita mal armada** que el juez no detectó: en `clip-matriz` el chat citó *"04 CLIP: arquitectura, pág. 7"* en lugar de *"12 Modelos multimodales.pdf, pág. 7"*: mezcló el título de la diapositiva con el número de otra clase.
- **Qué se aprende:** con un modelo tan chico, el contenido de las respuestas es bueno, pero **las citas no son confiables**: a veces cambian la página o el nombre del documento. Para la clase conviene mostrarlo, porque es el argumento de por qué cada respuesta muestra las páginas que se buscaron. Queda para probar con un modelo más grande en el mismo set.
- **Costo:** 0 créditos de LlamaCloud. Voyage: 18 búsquedas dentro de los tokens gratis.

### 21/11 · ¿LlamaCloud o Voyage AI tienen evals propios? (investigación, sin costo)

- **LlamaIndex** (el framework) tiene los evaluadores que ya se usan (`llama_index.core.evaluation`: `RetrieverEvaluator`, `FaithfulnessEvaluator`, `CorrectnessEvaluator`, entre otros). Es lo nativo.
- **LlamaCloud / LlamaParse:** no se encontró un producto de evals. Lo más cercano es [ParseBench](https://www.llamaindex.ai/blog/parsebench), un benchmark público de parsing, no una función para evaluar una biblioteca.
- **Voyage AI:** su API oficial tiene embeddings, embeddings multimodales y contextualizados, y reranking. No tiene un endpoint de evals: lo que aparece en la búsqueda son herramientas de terceros.
- **Decisión:** los evals siguen con lo nativo de LlamaIndex.

### 21/11 · Investigación: ¿el corte por página sirve para diapositivas? (sin costo)

- **Datos del corpus:** mediana de 507 caracteres por página; 43 páginas con menos de 100 (portadas y separadores) y 120 con menos de 300. La más larga (13.443) es la portada de la clase 10: un gráfico decorativo de una red neuronal que el parse convirtió en un Mermaid de nodos vacíos.
- **Los evals actuales no sirven para comparar cortes:** dan MRR 1,0, así que cualquier estrategia empataría.
- **LlamaIndex · `PrevNextNodePostprocessor`** ([docs](https://developers.llamaindex.ai/python/framework/module_guides/querying/node_postprocessors/node_postprocessors/)): suma al resultado la página anterior y/o la siguiente (`mode`: `previous`, `next` o `both`; `num_nodes`). Es beta. **Necesita las relaciones `PREVIOUS`/`NEXT` entre los nodos, y los nuestros no las tienen:** el corte `pagina` arma un `TextNode` suelto por página (verificado en el `docstore.json` de la biblioteca).
- **Ya se embebe el nombre del documento:** `nombre` no está en `excluded_embed_metadata_keys`, así que cada página va al embedding con el nombre de su clase.
- **Voyage · embeddings contextualizados** ([docs](https://docs.voyageai.com/docs/contextualized-chunk-embeddings)): cada chunk se embebe con el contexto de los demás chunks **de la misma lista interna**, que tiene que ser un solo documento, en orden y sin solapamiento. El modelo recomendado es `voyage-context-4`, con hasta 32.000 tokens por documento. La integración de LlamaIndex lo soporta, pero **manda como una sola lista interna cada lote que arma por cantidad de tokens** (`base.py`, `inputs=[batch]`): si un lote junta páginas de varias clases, el contexto se mezcla. La página no informa el precio.
- **LlamaParse · opciones v2** ([configurar Parse](https://developers.llamaindex.ai/llamaparse/parse/guides/configuring-parse/)): **no hay una opción para ignorar imágenes decorativas ni para no convertir diagramas en Mermaid.** Lo más cercano: `agentic_options.custom_prompt` (cambia el modelo OCRia-1 por uno general, no saltea la caché y no está documentado que sirva para esto), `images_to_save` e `ignore_text_in_image`. Existe `processing_options.cost_optimizer.enable`, que manda las páginas simples a `cost_effective`, solo en `agentic` y `agentic_plus`.
- **Lista de precios** ([pricing](https://developers.llamaindex.ai/llamaparse/general/pricing/)): agentic, 10 créditos por página, más 3 por la extracción de layout. Medimos 17,7 de promedio; la API no desglosa la diferencia.

### 21/11 · Parse del panel de LlamaCloud contra el nuestro, en la clase 08 (sin costo para nosotros)

- **Qué se hizo:** el usuario parseó `08 Transferencia de aprendizaje.pdf` a mano en el panel de LlamaCloud y pasó el Markdown. Se comparó línea por línea con el `document.md` de nuestra corrida (`pjb-a21fuc92ikqb5qpmx76vrw0396sp`). No se sabe con qué tier ni con qué opciones se hizo el del panel.
- **El texto es el mismo:** títulos, viñetas, las dos tablas, el código Keras y las conclusiones coinciden. Similitud por líneas: 0,70; casi toda la diferencia está en los diagramas.
- **Diagramas Mermaid distintos:** los dos convierten los mismos diagramas, pero con otros nodos y otro orden. En la pág. 12 (fine-tuning), el panel deja solo la descripción (`drawing: …`) y el nuestro arma un Mermaid. Es otra muestra de que **el parse no es determinístico** en lo visual.
- **Bloques sin cerrar en el del panel:** tres bloques ` ```mermaid ` / ` ```python ` no tienen el cierre ` ``` `, y el texto de la diapositiva siguiente queda dentro del bloque. El nuestro los cierra bien.
- **Detalles:** el panel escribe `224 x 224` y el nuestro `224 × 224`; al nuestro le falta la nota *"Commonly referred to as a Convolutional Base or a Backbone"* de la pág. 10.
- **Hallazgo importante: los links de la bibliografía (pág. 24) están mal asignados en el nuestro.** El del panel no trae links (`[<u>link</u>]`). El nuestro sí, porque pedimos `annotate_links: true`, pero **cada texto apunta al link de otra línea**: *"Tutorial oficial de TensorFlow"* → opencv.org; *"Vision Transformer"* → ibm.com (fine-tuning); *"CLIP"* → openwebinars.net. Se verificó contra las anotaciones del PDF con pypdf: **el PDF tiene cada link en su lugar**, así que el error es de LlamaParse. La API no lo marca ni avisa.
- **Qué se aprende:** un link anotado parece un dato confiable y no lo es. Si el chat cita un link de la bibliografía, puede estar mal.

### 21/11 · Set de evals más exigente y línea de base de la búsqueda (sin costo: tokens gratis de Voyage)

- **Set:** 13 preguntas nuevas (31 en total), todas con la respuesta verificada en el parse y con **todas** las páginas que la contienen como fuente: 5 `parafraseada` (la idea con otras palabras que las de la diapositiva), 4 `varias_diapositivas` y 4 `cruza_clases` (de 2 a 4 clases). Ahora hay preguntas de las clases 01, 02 y 11, que no tenían.
- **Métrica nueva:** cobertura de clases = de las clases que tienen la respuesta, cuántas llegan al modelo. También se mide el tiempo de cada respuesta.
- **Línea de base de la búsqueda** (6 páginas al modelo, 18 candidatos, sin MMR): hit rate 1,0 · **MRR 0,96** · **cobertura de clases 0,966**.
- **Dónde falla:** `transformers-de-texto-a-imagen` (llegan las clases 07 y 12, pero no la 05: cobertura 0,5); `clip-en-la-materia` (llegan la 12 y la 08, faltan la 11 y la 13: cobertura 0,5; MRR 0,33); `clip-sin-etiquetas` (MRR 0,5: la primera página correcta llega segunda). Justo las preguntas que cruzan clases, que es lo que tiene que mejorar la búsqueda con MMR.
- **Costo:** 0 créditos de LlamaCloud; 29 búsquedas de Voyage dentro de los tokens gratis.

### 21/11 · Línea de base de las respuestas con el set de 31 preguntas (~USD 0,010 de OpenAI; tokens gratis de Voyage)

- **Corrida:** `libraries/2026-11-21_133046_aprendizaje-automatico-ii/evals/2026-11-21_185241/`. Configuración de hoy: 6 páginas al modelo, 18 candidatos antes del reranker, sin MMR.
- **Búsqueda:** hit rate 1,0 · MRR 0,96 · cobertura de clases 0,966 (igual que la corrida sin respuestas).
- **Respuestas:** **30 de 31 fieles** · **22 de 31 correctas** (4 o más de 5) · corrección promedio 3,61.
- **Tiempo por respuesta:** 2,52 s de promedio y 3,77 s de máximo (solo el chat, sin el juez). Muy por debajo del límite de 10 s.
- **Tokens de OpenAI** (chat y juez): 132.009 de entrada y 9.366 de salida. Con USD 0,05 y 0,40 por millón son unos **USD 0,010**.
- **Las que el juez marcó como incorrectas:** `rag`, `unet-origen`, `clip-matriz`, `equidad-ejemplo`, `enganiar-una-red`, `evitar-memorizar`, `vae`, `resnet-y-unet`, `trampa-q-learning`.
  - `evitar-memorizar` (2 de 5): **falla real.** Llegó la pág. 6 de la clase 02 (sobreajuste) pero no la de regularización y drop-out, y el chat dijo que los fragmentos no daban mecanismos.
  - `trampa-q-learning` (1 de 5): **otra vez un error del juez.** El chat dijo que Q-learning no está en los fragmentos, que es lo esperado, y el juez lo bajó por no explicar el tema.
  - La única no fiel es `clip-sin-etiquetas`; el juez respondió solo "NO", sin explicar el motivo.
- **Otro detalle:** en la trampa, el chat tuteó ("si quieres…, confirma…") y ofreció buscar "otros fragmentos", algo que no puede hacer. Queda para el `SYSTEM_PROMPT` de la tarea 4.
- **Costo:** 0 créditos de LlamaCloud; 31 búsquedas de Voyage dentro de los tokens gratis.
