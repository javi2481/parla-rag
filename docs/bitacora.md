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

### 21/11 · Comparación de búsquedas: 6 o 12 páginas, con o sin MMR (~USD 0,08 de OpenAI en total; tokens gratis de Voyage)

- **Prompt nuevo en las tres corridas:** el chat tiene que relacionar las clases cuando la pregunta cruza temas, responder con voseo y no ofrecer buscar en otros documentos.
- **Un tropiezo que dejó un dato útil:** la primera tanda corrió con el código viejo (el `--reload` de uvicorn no tomó los cambios y FastAPI ignoró `top_k` y `modo`, que no conocía). Fueron **tres repeticiones de la línea de base** (`2026-11-21_185906`, `_190156`, `_190441`), con 23, 25 y 25 correctas. Junto con la línea de base (22), **la misma configuración da entre 22 y 25 correctas de 31**: el juez tiene un ruido de unas ±3 respuestas. Una diferencia más chica que eso no alcanza para elegir. Costo de esa tanda: unos USD 0,03.
- **Las corridas de verdad** (con el backend reiniciado; se verificó `modo` y `candidatos` en el `request.json`):

| Corrida | Páginas / modo | Candidatos | MRR | Cobertura de clases | Fieles | Correctas | Corrección | Tokens (entrada / salida) | Tiempo prom. / máx. |
|---|---|---|---|---|---|---|---|---|---|
| `2026-11-21_190942` | 6 / default | 18 | 0,96 | 0,966 | 30 de 31 | 24 de 31 | 3,71 | 137.295 / 11.056 | 2,70 s / 4,17 s |
| `2026-11-21_191247` | 12 / default | 36 | 0,966 | 0,966 | 30 de 31 | 25 de 31 | 3,81 | 246.847 / 12.284 | 2,94 s / 5,95 s |
| `2026-11-21_191729` | 12 / mmr (umbral 0,5) | 36 | 0,966 | **0,957** | 31 de 31 | 24 de 31 | 3,74 | 282.010 / 12.295 | 4,55 s / 5,85 s |

- **Lo que dicen los números:** ninguna configuración mejora la cobertura de clases. Con MMR **empeora** (`clip-en-la-materia` baja de 0,5 a 0,25) y tarda casi el doble. Pasar a 12 páginas duplica los tokens de entrada y suma 1 correcta, que está dentro del ruido.
- **Por qué MMR no ayudó (lo que se puede afirmar):** MMR elige candidatos variados **antes** del reranker, y el reranker después deja las 6 o 12 páginas más parecidas a la pregunta. Es probable que el reranker deshaga la variedad, pero la API no lo informa: es una hipótesis, no un dato medido.
- **Decisión:** se queda **6 páginas, búsqueda `default`** (los valores por defecto de siempre): rinde igual, es la más rápida y gasta la mitad. MMR queda disponible (`LIBRARY_RETRIEVAL_MODE=mmr`, `LIBRARY_MMR_THRESHOLD`).
- **Las trampas, con el prompt nuevo:** las tres corridas dicen que Q-learning no está y ya no ofrecen buscar en otros lados. El juez la sigue marcando como incorrecta: es el mismo error del juez de antes.
- **Costo:** 0 créditos de LlamaCloud; 93 búsquedas de Voyage dentro de los tokens gratis.

### 21/11 · Las unidades de la materia como reglas de Classify (0 créditos; tokens gratis de Voyage)

- **Reglas nuevas** (`s4_classify.py`): las 4 unidades del temario, con la descripción copiada textual de `00 Presentación.pdf` (págs. 10 a 13), más `temas_complementarios` (multimodales, sesgo, ética y evaluación robusta) y `presentacion_de_la_materia`. Reemplazan a `clase_teorica`, `enunciado_de_practica` y `factura`.
- **Classify en las 14 corridas:** las 14 terminaron con **0 créditos** cada una (`usage.credits` = 0, como se esperaba sobre un parse ya hecho). **Las 14 coinciden con la unidad esperada.** Lo que más podía fallar eran las clases 01 y 02, porque la unidad 4 también dice "Redes neuronales tipo perceptrón y profundas"; las dos quedaron en `redes_neuronales`.

El razonamiento lo devuelve la API en inglés; va recortado y tal cual (sin el nombre del docente, porque la bitácora es pública).

| Clase | Unidad que eligió Classify | Confianza | Razonamiento (resumido) |
|---|---|---|---|
| 00 Presentación | `presentacion_de_la_materia` ✅ | 100% | This document is clearly a course presentation. It contains: 1. Title "Presentación del curso" (Course Presentation) 2. Brief presentation of the professor […] with his academic and professional… |
| 01 Introducción a Redes Neuronales | `redes_neuronales` ✅ | 100% | This document is a perfect match for the "redes_neuronales" category. It is clearly an introductory presentation on Neural Networks ("Introducción a Redes Neuronales") that covers all the key topics from Unit 1:  1.… |
| 02 Perceptrón Multicapa y Deep Learning | `redes_neuronales` ✅ | 95% | This document is clearly about neural networks (Redes Neuronales), specifically covering the multilayer perceptron (Perceptrón Multicapa) and deep learning. The content directly matches Unit 1 topics including:… |
| 03 PLN - Conceptos y técnicas de procesamiento | `procesamiento_del_lenguaje_natural` ✅ | 100% | This document is a comprehensive presentation on Natural Language Processing (PLN - Procesamiento del Lenguaje Natural). It covers all the key topics from Unit 2:  1. **Processing techniques**: The document… |
| 04 PLN - Modelos estadísticos y Representaciones Vectoriales | `procesamiento_del_lenguaje_natural` ✅ | 95% | This document is clearly focused on Natural Language Processing (PLN - Procesamiento del Lenguaje Natural). It covers two main topics that are core to Unit 2:  1. **Statistical Models in NLP**: The document… |
| 05 PLN - Redes neuronales | `procesamiento_del_lenguaje_natural` ✅ | 95% | This document is clearly focused on Natural Language Processing (PLN - Procesamiento del Lenguaje Natural) with neural networks. The content extensively covers:  1. **Recurrent Neural Networks (RNN, LSTM, GRU)** -… |
| 06 Procesamiento digital de imágenes | `procesamiento_digital_de_imagenes` ✅ | 100% | This document is a perfect match for "procesamiento_digital_de_imagenes" (Unit 3: Digital Image Processing). The content extensively covers all the key topics specified in this category:  1. **Operaciones puntuales… |
| 07 Clasificación de imágenes | `aprendizaje_profundo_en_imagenes` ✅ | 95% | This document is clearly focused on convolutional neural networks (CNNs) for image classification, which is a core topic of Unit 4 (Aprendizaje profundo aplicado a imágenes). The document covers:  1. Introduction to… |
| 08 Transferencia de aprendizaje | `aprendizaje_profundo_en_imagenes` ✅ | 95% | This document is clearly about "Transferencia de aprendizaje" (Transfer Learning) applied to images, which is explicitly mentioned in the "aprendizaje_profundo_en_imagenes" category description as "Transferencia de… |
| 09 Detección de objetos | `aprendizaje_profundo_en_imagenes` ✅ | 98% | This document is clearly focused on object detection in images, which is a core topic of Unit 4 (Aprendizaje profundo aplicado a imágenes). The content extensively covers:  1. Object detection architectures (R-CNN,… |
| 10 Segmentación de imágenes | `aprendizaje_profundo_en_imagenes` ✅ | 100% | This document is a perfect match for "aprendizaje_profundo_en_imagenes" (Unit 4: Deep learning applied to images). The presentation explicitly covers:  1. **Semantic segmentation** - a core topic in image… |
| 11 Generación de imágenes | `aprendizaje_profundo_en_imagenes` ✅ | 95% | This document is a presentation about "Generación de imágenes y transferencia de estilo" (Image Generation and Style Transfer) from the course "Aprendizaje automático 2". The content extensively covers:  1. Image… |
| 12 Modelos multimodales | `temas_complementarios` ✅ | 95% | This document is clearly about multimodal models (modelos multimodales) that combine vision and language, which is explicitly mentioned in the "temas_complementarios" category as "modelos multimodales (visión y… |
| 13 Sesgo, ética y evaluación robusta de modelos | `temas_complementarios` ✅ | 100% | This document is a perfect match for "temas_complementarios". The presentation is explicitly titled "Sesgo, ética y evaluación robusta de modelos" (Bias, ethics and robust evaluation of models), which directly… |

- **Biblioteca:** se sacaron y se volvieron a sumar las 14 corridas, así cada página toma el `tipo` nuevo, y se volvió a sincronizar: 410 páginas, 410 chunks, 0 créditos de LlamaCloud.
- **El filtro por unidad funciona:** *"¿Cómo funciona una red convolucional para clasificar imágenes?"* trae solo la clase 07 sin filtro y solo la 05 con `tipo = procesamiento_del_lenguaje_natural`.
- **Costo:** 0 créditos de LlamaCloud (14 Classify); embeddings de la sincronización y 4 búsquedas de Voyage dentro de los tokens gratis.

## 21/11 · El chat como página principal: pestañas y filtros en el navegador

- **Prueba en el navegador (pestaña Chat):** dos conversaciones en pestañas distintas. La primera, *"¿Qué es una función de activación?"*, sin filtros: citó páginas 3, 4, 6, 7 y 8 de la clase 01 y la 16 de la 07. La segunda, *"¿Cómo funciona una red convolucional para clasificar imágenes?"*, con la unidad **PLN**: las 6 páginas citadas son de la clase 05 (PLN - Redes neuronales).
- **Pestañas:** cada una tomó como título las primeras palabras de su pregunta. Se cerró la primera y se recargó la página: volvió solo la segunda, con su turno, y la carpeta de la cerrada sigue en `chats/local/` (no se borra nada).
- **Costo:** 0 créditos de LlamaCloud. OpenAI (`gpt-5-nano`): 2.954 tokens de entrada y 774 de salida en total, unos **USD 0,0005** (estimado con la lista de precios: 0,05 y 0,40 por millón). Las búsquedas de Voyage, dentro de los tokens gratis.

## 21/11 · Citas por documento y detrás de escena

- **Costo estimado por turno:** `total_usage` suma `costo_estimado_usd` = tokens × la lista de precios de OpenAI del 21/11 (USD 0,05 por millón de entrada y 0,40 de salida, en `settings.py`). OpenAI no informa el costo en la respuesta, por eso se marca "estimado". El evento de la búsqueda suma el `modo` (`default` o `mmr`).
- **Prueba en el navegador:** *"¿Qué tienen en común ResNet y U-Net?"*, sin filtros. Las páginas que llegaron al modelo, agrupadas: clase 07 (págs. 28, 27 y 32), clase 10 (págs. 12 y 13) y clase 00 (pág. 13). La captura y el texto de la página 12 de la clase 10 abren bien. Detrás de escena: 18 candidatos en modo `default`, 6 páginas después del reranker (puntajes de 0,64 a 0,50), `gpt-5-nano` con 2.409 tokens de entrada y 293 de salida.
- **Costo:** 0 créditos de LlamaCloud; OpenAI **USD 0,00024** (estimado, coincide con la cuenta a mano); Voyage dentro de los tokens gratis.

## 21/11 · Pruebas e2e de la app (antes de Docker)

Con el backend en :8000 y el frontend de desarrollo en :5173, manejando el navegador con Playwright (script `e2e-chat.js`, fuera de git). Antes de empezar se cerraron las conversaciones abiertas (quedan en disco).

| Prueba | Resultado |
|---|---|
| La app abre en Chat, con el recorrido y sus números | ✅ `#chat`; 14 documentos · 410 páginas, 7.250 créditos en 14 corridas, 410 chunks, `voyage-4 · rerank-2.5`, `gpt-5-nano` |
| Sin conversaciones abiertas, se crea una sola | ✅ 1 pestaña |
| Pregunta que cruza clases: *"¿Qué tienen en común ResNet y U-Net?"* | ✅ citas agrupadas: 07, 10 y 00; la captura de la clase 10 abre (3000 px de ancho) |
| Filtro de unidad PLN: *"¿Cómo funciona una red convolucional…?"* | ✅ solo la clase 05; la respuesta aclara que esas páginas son de PLN y no describen CNN para imágenes |
| Trampa: *"¿Cómo funciona Q-learning y la ecuación de Bellman?"* | ✅ dice que no aparece en los fragmentos; ⚠️ igual sugiere "fragmentos relevantes que podrías consultar" (01, 08 y 05) |
| Cerrar una pestaña y recargar | ✅ queda solo la otra, con sus 2 turnos |
| Filtros que no dejan páginas (unidad Temas complementarios + clase 03, por la API) | ✅ "No encontré páginas con esos filtros.", 0 llamadas al modelo, 0 tokens |
| Wizard: Classify sin Split | ✅ las 14 corridas tienen Classify hecho con Split pendiente; Classify no muestra bloqueo y Extract dice "Primero terminá el paso Schema" |
| Bibliotecas: los evals guardados | ✅ se ven las métricas de la última corrida (hit rate 1, MRR 0,966, cobertura 0,957, 24 de 31 correctas, 4,6 s promedio) |

- **Hallazgo:** el script falló dos veces por escribir antes de que la pestaña nueva terminara de cargar (el cuadro se deshabilita mientras carga y el texto se pierde). En la app real pasa lo mismo si se escribe muy rápido después del "+".
- **Costo:** 0 créditos de LlamaCloud. OpenAI: 5 respuestas (2 corridas del script, la segunda completa), menos de USD 0,002 estimado. Voyage, dentro de los tokens gratis.

## 22/11 · Segunda pasada e2e (chat, wizard y bibliotecas)

Con el backend en :8000 y el frontend de desarrollo en :5173, otra vez con Playwright (`e2e-chat.js` y pasos sueltos para el wizard y Bibliotecas, sin parsear nada nuevo).

| Prueba | Resultado |
|---|---|
| Script del chat (recorrido, cruce ResNet/U-Net, filtro PLN, trampa, cerrar y recargar) | ✅ igual que el 21/11; la captura de la clase 10 abre (3000 px). La trampa vuelve a sugerir clases para consultar |
| Wizard, corrida 09: lista de corridas | ✅ 14 corridas; la suma de créditos da 7.250 |
| Wizard, Parse: pestaña Páginas | ❌ → ✅ decía **"Páginas (0)"** y no se veían capturas ni cajas (ver hallazgo 1). Después del arreglo: 41 páginas, cajas sobre la página 6 y las de baja confianza en rojo |
| Wizard, Parse: tiempo | ❌ → ✅ decía **"0,0 segundos"** (ver hallazgo 2). Ahora: 19,3 s |
| Wizard, Classify / Extract / Biblioteca | ✅ `aprendizaje_profundo_en_imagenes` con 98 %, 0 créditos; Extract pide Schema; "Ya está en: Aprendizaje Automático II" |
| Bibliotecas: documentos, sincronización, evals guardados | ✅ 14 documentos con su tipo, 410 páginas en 410 chunks, evals del 21/11 |
| Bibliotecas: búsqueda de prueba | ❌ → ✅ decía "Cada búsqueda cuesta 1 crédito según la lista de precios de LlamaCloud", que es del motor de LlamaCloud. Con el motor local ahora dice que la hace Voyage AI con 0 créditos |

**Hallazgos y arreglos:**

1. **Rutas con `\` en Windows.** `RunStore.list_files` armaba la ruta con `str()`, y en Windows sale `2_parse\images\page_1.jpg`. El frontend busca `images/page_N.jpg`, así que no encontraba ninguna captura. Era también la causa del test que fallaba solo en Windows (`test_upload_parse_and_delete`). Arreglo: `as_posix()`. En Linux (Docker, CI) no pasaba.
2. **El tiempo del parse era 0.** La API ya no manda `job_metadata.latency.total_ms`: manda `state_transitions` (`running_at`, `completed_at`). Ahora el tiempo sale de esas dos horas; si no viene ninguno de los dos datos, la métrica dice "—" y la frase no menciona el tiempo. Se recalcularon los `metrics.json` de las 14 corridas desde su `response.json` guardado (local, sin llamar a la API; los anteriores quedaron respaldados fuera del repo). Test nuevo en `test_parse_summary.py`.
3. **Aviso de React en la consola** al mostrar el Markdown de la clase 09: LlamaParse devuelve una tabla HTML con texto suelto adentro ("One and two stage detectors"). No rompe nada; queda anotado.

- **Tests:** 29 pasan en Windows (antes 27 de 28).
- **Costo:** 0 créditos de LlamaCloud. OpenAI: 3 respuestas, menos de USD 0,001 estimado. Voyage, dentro de los tokens gratis.

## 22/11 · Auditoría para pulir el proyecto

Revisión solo de lectura de todo el código y la documentación, y después los arreglos. Sin llamadas pagas.

| # | Hallazgo | Qué se hizo |
|---|---|---|
| 1 | **Docker arranca sin los datos:** el volumen nuevo de `compose.yaml` solo trae `samples/`; sin las 14 corridas ni el índice, el Chat abre vacío (rehacer los parses cuesta 7.250 créditos) | Se decide al armar la imagen |
| 2 | 9 rutas de `library_router.py`, 15 funciones de `libraries/api.ts` y 3 funciones internas sin el comentario de arriba (regla del proyecto) | Comentadas; el chequeo automático da 0 funciones sin comentario |
| 3 | Las métricas de los evals en formato inglés (`0.966`, `282010`, `4.553 s`) | `decimal_es` y `number_es`: `0,966`, `282.010`, `4,6 s`. Se recalcularon los `metrics.json` de los evals guardados que tienen cobertura de clases (los 2 más viejos no la tienen y quedan como estaban); respaldo fuera del repo |
| 4 | El chat de Bibliotecas decía "Búsquedas del agente" con el motor local, que no tiene agente | Dice "Búsquedas" con el motor local |
| 5 | `s2_parse.py` remitía a `docs/verificacion-1-parse.md`, que ya no existe | Remite al informe de la fase 1 y a la bitácora |
| 6 | Parecía que el separador por defecto (`"oraciones"`) contradecía al de la configuración (`"pagina"`) | **Falso positivo:** las bibliotecas sin el dato se armaron con `"oraciones"` y el motor corta igual. Se agregó un comentario que lo explica |
| 7 | El encabezado del paso 7 (Biblioteca) tenía otro estilo | Igual a los demás pasos: "PASO 7" y el título grande |
| 8 | `.playwright-mcp/` y `.atl/` sin ignorar | Agregadas al `.gitignore` |

- **Verificado:** 29 tests pasan, el frontend compila y en el navegador se ven los evals en formato argentino, "Búsquedas (1)", el texto nuevo de la búsqueda de prueba y el paso 7.
- **Costo:** 0.

## 22/11 · Preguntas que cruzan clases (prueba manual)

Dos preguntas en el Chat, sin filtros. Se revisaron las páginas que llegaron al modelo (`turno_1.json` de cada conversación) contra el parse.

| Pregunta | Páginas que llegaron al modelo | Qué pasó |
|---|---|---|
| *"¿Cómo se usa el mecanismo de atención en texto, en imágenes y en los modelos multimodales?"* | Las 6 de la clase **12** (págs. 25, 22, 10, 27, 7 y 5) | ❌ **Falla de la búsqueda:** no llegó ninguna página de la 05 (Transformers), la 07 (ViT) ni la 10, que hablan de atención. ⚠️ El modelo además **estira** el contexto: dice que CLIP usa "atención en el espacio compartido" (la pág. 10 habla de distancia entre embeddings, no de atención) |
| *"¿Qué técnicas se mencionan en la materia para evitar el sobreajuste?"* | 08 pág. 15, 06 pág. 31, **02 pág. 6**, 13 págs. 24 y 30, 03 pág. 43 | ❌ **Falla del modelo:** la búsqueda trajo la 02 pág. 6 (tercera, rerank 0,71), que dice **"Regularización"** y **"Drop-out"**, y el modelo no las nombró. ⚠️ Puso como técnica contra el sobreajuste el learning rate bajo, que en la pág. 15 de la 08 es para el *catastrophic forgetting* |

- **Lectura:** son dos fallas distintas. En la primera, la consulta junta tres temas y la búsqueda se va toda hacia "multimodales". En la segunda, la página correcta llegó y `gpt-5-nano` con razonamiento `minimal` no la usó.
- **Costo:** 0 créditos de LlamaCloud. OpenAI: USD 0,000503 + 0,000163 (estimado). Voyage, dentro de los tokens gratis.

**Misma pregunta del sobreajuste con `LIBRARY_REASONING_EFFORT=low`** (variable de entorno solo para esta prueba; el `.env` no se tocó):

- **Llegaron las mismas 6 páginas** (06 pág. 31, 08 pág. 15, 02 pág. 6, 13 págs. 24 y 30, 03 pág. 43).
- ✅ Ahora nombra **"Regularización mediante Drop-out"** (02 pág. 6) y el aumento de datos (06 pág. 31). ✅ Ya no pone el learning rate bajo como técnica contra el sobreajuste.
- ⚠️ Le falta GlobalAveragePooling2D en lugar de Flatten (08 pág. 15 dice "menos sobreajuste").
- **Tokens:** 1.261 de entrada y 314 de salida (192 de razonamiento), contra 249 de salida y 0 de razonamiento con `minimal`. **Costo:** USD 0,000189 contra 0,000163.
- Es **una sola muestra** y el modelo no es determinístico: para decidir el valor por defecto hay que correr los evals con respuestas.
- Además se gastó un turno de prueba con la pregunta "x" por un error de codificación del script (la consola de Windows rompía los acentos del pedido): menos de USD 0,0001. Esa conversación se cerró.

## 22/11 · Evals con razonamiento `low`

Evals con respuestas, configuración por defecto (18 candidatos, 6 páginas, modo `default`), con `LIBRARY_REASONING_EFFORT=low` (variable de entorno; el `.env` no se tocó). Carpeta `evals/2026-11-22_115912`.

| | `minimal` (5 corridas del 21/11, misma configuración) | `low` (22/11) |
|---|---|---|
| Hit rate / MRR / cobertura de clases | 1 / 0,96 / 0,966 | 1 / 0,96 / 0,966 (la búsqueda es la misma) |
| Respuestas correctas (4 o más de 5) | 22 a 25 de 31 | **28 de 31** |
| Corrección promedio | 3,61 a 3,81 | **4,645** |
| Fieles a los fragmentos | 29 a 30 de 31 | 27 de 31 |
| Tiempo por respuesta (promedio) | 2,4 a 2,7 s | 3,7 s |
| Tokens de OpenAI (entrada / salida) | ~131.000 / ~9.000 | 135.601 / 26.134 |

- ⚠️ **La comparación no es limpia:** el juez usa la misma configuración que el chat (`library_evals.py`), así que también pasó a `low`. Cambiaron a la vez el que responde y el que corrige.
- **Ruido del juez, visto en sus explicaciones:** marcó como no fieles 4 respuestas que dice correctas (5 de 5), entre ellas la trampa de la fecha del parcial, que responde que el dato no está. `FaithfulnessEvaluator` solo devuelve YES/NO, sin el motivo. A *"¿Cómo se engaña a una red?"* le puso 2 de 5 por motivos de seguridad, aunque es el tema de la clase 13.
- **Costo:** 0 créditos de LlamaCloud. OpenAI: unos USD 0,017 (estimado con la lista de precios). Voyage, dentro de los tokens gratis.

## 22/11 · El juez de los evals, aparte del chat

- **Cambio:** `LIBRARY_JUDGE_REASONING_EFFORT` (por defecto `low`) para el juez, separado de `LIBRARY_REASONING_EFFORT` del chat. Cada corrida de evals anota los dos en su `request.json` (`razonamiento` y `juez_razonamiento`). Es una opción del cliente nativo de OpenAI de LlamaIndex. Tests: 30 pasan (uno nuevo verifica que cambiar el razonamiento del chat no cambia el del juez).
- **Evals con el mismo juez (`low`), misma configuración (18 candidatos, 6 páginas):**

| | Chat `minimal` (`evals/2026-11-22_121929`) | Chat `low` (`evals/2026-11-22_115912`) |
|---|---|---|
| Respuestas correctas (4 o más de 5) | **28 de 31** | **28 de 31** |
| Corrección promedio | 4,516 | 4,645 |
| Fieles a los fragmentos | **30 de 31** | 27 de 31 |
| Tiempo por respuesta (promedio / máximo) | **2,9 s / 4,1 s** | 3,7 s / 5,8 s |
| Tokens de OpenAI (entrada / salida) | 140.057 / 20.178 | 135.601 / 26.134 |

- **Conclusión:** la mejora de 22–25 a 28 de 31 era **del juez**, no del chat. Con el mismo juez, el chat en `minimal` acierta lo mismo, es más fiel y más rápido. **El chat queda en `minimal`**; la mejora de la pregunta del sobreajuste con `low` fue una sola muestra.
- **Costo:** 0 créditos de LlamaCloud. OpenAI: unos USD 0,015 (estimado). Voyage, dentro de los tokens gratis.

## 22/11 · Agente y búsqueda híbrida (BM25 + vectores)

- **Qué se probó:** si la configuración heredada de los documentos financieros conviene para los apuntes de clase. El parse y el corte por página se dejan como están (el corte por página se midió con estos apuntes). Se probó lo que falla en las preguntas que cruzan clases: **la búsqueda** y **cuántas veces se busca**.
- **Cambios (todo nativo de LlamaIndex):**
  - `LIBRARY_RETRIEVAL_MODE=hibrida`: `QueryFusionRetriever` junta vectores (voyage-4) y `BM25Retriever` (stemmer en español) con reciprocal rank fusion; `num_queries=1`, así no llama a ningún modelo. Paquete nuevo: `llama-index-retrievers-bm25` (integración oficial).
  - `LIBRARY_CHAT_ENGINE=agente`: `FunctionAgent` con la herramienta `buscar_en_la_biblioteca` (mismo buscador y reranker), hasta 6 pasos. Por ahora solo en los evals; el chat sigue con `contexto`.
  - Los evals anotan qué buscó y qué páginas vio el modelo, y la cobertura de clases **al responder** (con el agente puede ser más que una búsqueda).
- **Prueba suelta del agente** (pregunta de atención): 1 búsqueda, páginas de las clases 05, 10, 00 y 08 (antes, las 6 de la 12). USD 0,0006.
- **Evals con respuestas, juez `low`, chat `minimal`, 18 candidatos, 6 páginas:**

| | Contexto + vectores (`141208`) | Contexto + híbrida (`141600`) | Agente + vectores (`142039`) | Agente + híbrida (`142520`) |
|---|---|---|---|---|
| Correctas (4 o más de 5) | 26 de 31 | **29 de 31** | 29 de 31 | **30 de 31** |
| Corrección promedio | 4,484 | **4,629** | 4,484 | 4,597 |
| Fieles a los fragmentos | 25 de 31 | 27 de 31 | 25 de 31 | **28 de 31** |
| Cobertura de clases al responder | 0,966 | 0,966 | 0,922 | 0,931 |
| Búsquedas por respuesta (reales) | 1 | 1 | 1,48 | 1,29 |
| Tiempo por respuesta (promedio) | **3,0 s** | 3,1 s | 4,6 s | 4,6 s |

- **Búsqueda sola (sin modelo):** la híbrida cambia las páginas en 18 de 31 preguntas, pero hit rate (1), MRR (0,96) y cobertura (0,966) quedan iguales.
- **Ruido:** la misma configuración (contexto + vectores) dio 28 de 31 en `121929` y 26 de 31 hoy. Diferencias de ±2 son ruido del juez.
- **Lectura:**
  - La híbrida mejora las respuestas en los dos motores (+3 y +1 correctas, +2 y +3 fieles), sin costo ni demora extra. Es la mejora más consistente.
  - El agente **casi no reparte la pregunta**: con razonamiento `minimal` hace una sola búsqueda en 22 o 23 de 31 preguntas, y la cobertura de clases **baja** (0,966 → 0,93). Tarda 1,5 s más y usa ~60 % más tokens. Con estos datos no lo justifica.
  - Siguen fallando en cobertura `transformers-de-texto-a-imagen` y `clip-en-la-materia` (0,5) en todas las combinaciones.
- **Errores de medición encontrados y arreglados:** el registrador de llamadas seguía escuchando mientras juzgaba el juez, así que **los tokens de los evals (también los del 21/11 y 22/11) incluían los del juez**, y la búsqueda interna de `FaithfulnessEvaluator` se contaba como búsqueda del chat. Ahora se deja de escuchar antes del juez y las búsquedas se cuentan por las llamadas a la herramienta. Los tokens de la tabla de arriba siguen incluyendo al juez.
- **Costo:** 0 créditos de LlamaCloud. OpenAI: unos USD 0,075 las cuatro corridas (estimado con la lista de precios, con el juez incluido). Voyage, dentro de los tokens gratis.

## 22/11 · Búsqueda híbrida por defecto y backend reorganizado

- **La búsqueda híbrida queda por defecto** (`LIBRARY_RETRIEVAL_MODE=hibrida`), por los evals de la entrada anterior. El chat sigue con el motor de contexto; el agente queda como opción para comparar en los evals.
- **Error encontrado al ponerla por defecto (los tests lo detectaron):** `BM25Retriever` con `filters` no saca las páginas que no cumplen: les pone peso 0 y las sigue devolviendo con puntaje 0, y si ninguna cumple tira un error. Ahora BM25 se arma solo con las páginas que cumplen los filtros y, si no queda ninguna, se usa la búsqueda por vectores sola. Test nuevo: `test_busqueda_hibrida_respeta_los_filtros`.
- **Backend reorganizado** por wizard y bibliotecas, con nombres que dicen qué hacen. Solo se movió código (`git mv`); las rutas HTTP y las carpetas de `data/` no cambiaron.

| Antes (`pipelines/documents/`) | Ahora |
|---|---|
| `router.py` | `wizard/wizard_routes.py` (lo compartido pasó a `route_dependencies.py`) |
| `pipeline.py` | `wizard/wizard_flow.py` |
| `steps/s1_upload.py` … `s6_extract.py` | `wizard/steps/step1_upload.py` … `step6_extract.py` |
| `steps/jobs.py` | `wizard/steps/llamacloud_jobs.py` |
| `number_es` y `percent` (en `s2_parse.py`) | `number_format.py` |
| `client.py` | `llamacloud_client.py` |
| `library_router.py` | `libraries/library_routes.py` |
| `library.py` | `libraries/llamacloud_engine.py` (`identity_metadata` y `summarize_search` → `libraries/document_metadata.py`; `stamp` → `core/runs/store.py`) |
| `local_library.py` | `libraries/local/`: `local_engine.py` (entrada), `ai_models.py`, `index_builder.py`, `retrieval.py`, `chat_engine.py`, `turn_recorder.py`, `conversations.py` |
| `library_evals.py` | `libraries/local/rag_evals.py` |
| `tests/.../test_library.py` | `tests/.../test_llamacloud_library.py` |

- **Verificación:** 31 tests pasan, ruff sin avisos, `npm run build` compila. Con el backend reiniciado: `/api/config` y las 14 corridas responden, la búsqueda de prueba corre en modo `hibrida` (para la consulta sobre Bolukbasi trae las págs. 12 y 11 de la clase 13 y tres de la 04) y un turno real del chat ("¿Qué relación hay entre los embeddings de palabras de PLN y los problemas de sesgo?") usó páginas de las clases 13, 03 y 04. Esa conversación de prueba se cerró.
- **Costo:** 0 créditos de LlamaCloud. OpenAI: USD 0,000315 (el turno de prueba). Voyage, dentro de los tokens gratis.

## 22/11 · El CI falló en Ruff después del merge

- **Qué pasó:** la corrida [45051303785](https://github.com/javi2481/parla-rag/actions/runs/45051303785) falló en el paso de Ruff con 12 avisos. Los tests ni llegaron a correr.
- **Causa:** el CI usa `uvx ruff` (la última versión, 0.17.6) y en la máquina local estaba la 0.15.22. La versión nueva marca cosas que la vieja no: una línea en blanco de más entre imports (9 archivos de la reorganización), `.replace("Z", "+00:00")` innecesario en `fromisoformat` (desde Python 3.11 entiende la `Z`) y una variable desempaquetada sin usar en un test.
- **Arreglo:** imports ordenados con `ruff --fix`, se sacó el `.replace` en `step2_parse.py` y la variable quedó como `_settings`. Las dos versiones de Ruff pasan sin avisos y los 31 tests pasan.
- **Para no repetirlo:** correr `uvx ruff check .` en local antes del push, que es lo mismo que corre el CI.
