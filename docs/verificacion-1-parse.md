# Verificación 1 · Parse real del comunicado de BYMA

**Fecha:** 13/11/2026 · **Documento:** `backend/data/samples/byma/BYMA Comunicado de Prensa - 3T26.pdf` (10 páginas, 0,3 MB)
**Job:** `pjb-s4z0opy7i3qk91v52qsm2tk8okel` · **Todo lo que devolvió está en:** `backend/data/verificacion/2026-11-13_parse-comunicado/` (fuera de git)

La idea fue pedirle a Parse **todo lo que ofrece** en una sola llamada y ver qué devuelve, cuánto cuesta y cuánto tarda.

---

## 1. Lo que se pidió

| Opción | Valor | Para qué |
|---|---|---|
| `tier` | `agentic` | El parse con IA completo |
| `version` | `2026-10-16` | Fija, para que el resultado sea reproducible |
| `processing_options.specialized_chart_parsing` | `agentic` | Convertir los gráficos en tablas de datos |
| `processing_options.aggressive_table_extraction` | `true` | Detectar todas las tablas |
| `processing_options.confidence_score_effort` | `high` | Confianza por página más precisa |
| `processing_options.forms` | `enrich` | Detectar formularios |
| `processing_options.ocr_parameters.languages` | `["es"]` | OCR en español |
| `output_options.images_to_save` | `embedded`, `layout`, `screenshot` | Las imágenes del PDF, los recortes de cada tabla o gráfico y una captura de cada página |
| `output_options.granular_bboxes` | `cell`, `line`, `word` | Cajas por celda, por línea y por palabra |
| `output_options.markdown.tables` | unir tablas que siguen en otra página | |
| `output_options.tables_as_spreadsheet` | `true` | Todas las tablas en un Excel |
| `output_options.extract_printed_page_number` | `true` | El número de página impreso |
| `output_options.save_output_pdf` | `true` | Un PDF de salida |
| `expand` | text, markdown, items, metadata, forms, job_metadata, usage, imágenes, xlsx, PDF | Todas las salidas |

## 2. Costo y tiempo

| | |
|---|---|
| **Créditos** | **210**, o sea 21 por página |
| **Tiempo total** | 31 segundos: 3 para subir el archivo y 28 de espera |
| **Procesamiento en LlamaCloud** | 21,1 s: 8,3 de lectura del PDF, 11,9 del agente y 0,3 de armado de la salida |
| **Tokens del modelo** | 133.812 de entrada y 46.288 de salida |
| **OCR** | Corrió sobre 53 imágenes: 13 tenían texto y 40 estaban vacías |
| **Saldo estimado** | 29.443 − 210 = **unos 29.233 créditos** |

El costo de 21 por página es con **todas** las opciones prendidas. No sabemos todavía cuánto suma cada opción por separado (los gráficos con IA y la confianza "high" probablemente sean las más caras).

## 3. Lo que devolvió

| Salida | Qué trae | Archivo |
|---|---|---|
| **Markdown** | 22.053 caracteres, página por página. Las tablas vienen en HTML (`<table>`) con encabezados combinados | `document.md` |
| **Texto plano** | El texto de cada página | `text.txt` |
| **Items** | 65 elementos estructurados: 18 títulos, 15 textos, 10 pies de página, 9 tablas, 8 imágenes y 5 listas | `items.json` |
| **Grounded items** | Los mismos items con **cajas por línea y por palabra** sobre la página (en puntos, sobre una página de 612 × 792) | `grounded_items.jsonl` |
| **Metadata por página** | Confianza, número de página impreso, rotación, marca de agua, si se activó el *auto mode*, si se optimizó el costo | `metadata.json` |
| **Metadata del documento** | **Confianza 0,93**. La página con peor puntaje tiene 0,3 | `metadata.json` |
| **Imágenes** | 41 en total: **10 capturas** de página completa (2473 × 3200 px), 21 recortes de tablas, gráficos y logos, y 10 imágenes incrustadas | `images/` |
| **Excel** | **9 hojas**, una por tabla ("Resultados 3T", "Activos bajo custodia", "Ingresos operativos", "Margen EBITDA"…) | `tables.xlsx` |
| **Formularios** | Ninguno, como era de esperar en un comunicado | `forms.json` |
| **Job metadata** | Los tiempos de cada etapa, tokens y contadores de OCR | `job_metadata.json` |
| **Respuesta completa** | Todo junto, tal cual | `3_response_full.json` |

## 4. Lo que vale la pena mostrar en clase

**El hallazgo de la página 8.**
- Todas las páginas tienen confianza 1,0, menos la 8, que tiene **0,3**. Es la página con dos gráficos.
- Parse convirtió los dos gráficos en **tablas de datos**. Los valores coinciden con lo que muestra el gráfico.
- Encontró una **inconsistencia en el documento original**: el texto dice "el margen EBITDA de los últimos 12 meses fue de **74%**" y el gráfico muestra **75%** para el 3T26. Parse reprodujo las dos cosas tal cual; el error no es suyo.
- Una probable razón de la confianza baja: el gráfico tiene una línea punteada **sin valores**, que no se puede pasar a una tabla. Es una buena interpretación para mostrar: *"la página 8 tiene la confianza más baja porque tiene gráficos con datos que no se pueden leer"*.

**Del documento a los datos.**
- De un PDF de 10 páginas salen 9 tablas en Excel listas para usar, sin código nuestro.
- Cada palabra tiene su caja sobre la página, así que se puede marcar en la captura de dónde salió cada dato.

## 5. Respuestas a las dudas del plan

| Duda | Respuesta |
|---|---|
| ¿Qué valores acepta `images_to_save`? | `embedded` (imágenes del PDF), `layout` (recortes de cada tabla, gráfico o logo) y `screenshot` (captura de página completa) |
| ¿Las capturas sirven para reemplazar `pdfjs` y dibujar las cajas? | **Probablemente sí.** Las capturas son de 2473 × 3200 px y las cajas vienen en puntos sobre 612 × 792, la misma proporción. Para dibujarlas solo hay que pasarlas a fracciones de la página, que es lo mismo que ya hacemos hoy. Falta confirmar que las cajas de **Extract** usen la misma escala; eso se ve en la fase 3. |
| ¿Cuánto cuesta un parse? | 21 créditos por página con todas las opciones prendidas |
| ¿Si el índice deja listar todos los chunks? | Pendiente: se verifica en la fase 4 |
| ¿Si Split devuelve `usage`? | Pendiente: se verifica en la fase 3 |

## 6. Lo que aprendimos para la fase 2

1. **`save_output_pdf` no aporta nada.** El PDF de salida pesa exactamente lo mismo que el original. Se saca.
2. **Las imágenes incrustadas se repiten.** Las 10 son el mismo logo de BYMA, una por página. Conviene pedir solo `layout` y `screenshot`.
3. **Las cajas por palabra y por línea** vienen en un archivo aparte (`grounded_items`) que hay que descargar con una URL firmada. Lo mismo pasa con el Excel.
4. **El Markdown y el texto vienen página por página.** Pedir `markdown_full` y `text_full` en el `expand` debería traerlos completos: se prueba en la próxima llamada.
5. **`raw_words` no vino**, aunque se pidió.
6. **`wait_for_completion`**, la espera nativa del SDK, funciona bien. En el wizard igual conviene consultar el estado desde el navegador, para mostrar PENDING, RUNNING y COMPLETED en vivo.

## 7. Estimación para el resto de los documentos

Es una estimación con el mismo costo por página (21 créditos, todas las opciones prendidas):

| Documento | Páginas | Parse estimado |
|---|---|---|
| Comunicado (ya hecho) | 10 | 210 (real) |
| Presentación de resultados | 15 | ~315 |
| EEFF | 86 | ~1.800 |
| **Total de los tres parses** | 111 | **~2.300** |

Con unos 29.200 créditos libres, los tres parses entran con mucho margen y queda saldo para Split, Classify, Extract, el índice y el chat.

Para bajar el costo del EEFF hay dos caminos:
- **Elegir mejor las opciones:** por ejemplo, sin gráficos con IA ni confianza "high", ya que el EEFF tiene casi todo tablas y texto.
- **Bajar el tier:** usar `cost_effective`.

Antes de decidir conviene medir **una sola página** del EEFF con cada variante. Cuesta poco y dice exactamente cuánto suma cada opción.
