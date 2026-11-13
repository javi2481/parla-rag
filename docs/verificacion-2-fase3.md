# Verificación 2 · Split, Classify, Schema automático, Extract y costo por página

**Fecha:** 13/11/2026 · **Base:** el parse del comunicado de la verificación 1 (`pjb-s4z0opy7i3qk91v52qsm2tk8okel`)
**Datos crudos:** `backend/data/verificacion/2026-11-13_fase3/` (fuera de git). Cada prueba tiene su `request.json` y su `response.json`.

La idea fue **encadenar** los pasos de la fase 3 sobre un parse ya hecho: a LlamaCloud solo se le manda el ID del parse, no el documento.

---

## 1. Split · ❌ rechazado

- **Pedido:** 5 categorías (resumen, ingresos, gastos y eficiencia, estados contables, otros), permitiendo partes sin categoría.
- **Respuesta:** error 400, sin costo:
  > *"Parse job … was restricted to a subset of the document's pages (max_pages), which is not supported for split jobs: split results number pages relative to the full document."*
- **Qué significa:** Split numera las páginas respecto del documento completo, así que necesita un parse **sin** límite de páginas. Nuestro paso Parse mandaba siempre `max_pages=100`.
- **Corrección:** se sacó `max_pages` del paso Parse.
- **Pendiente:** probar Split de verdad. Hace falta un parse nuevo sin límite; propuesta: los EEFF, que es donde Split tiene sentido.
- **Otra cosa que aprendimos:** la respuesta de Split **no tiene campo `usage`**, así que no informa créditos.

## 2. Classify · ✅

| | |
|---|---|
| **Pedido** | 4 reglas (estados financieros, comunicado de prensa, presentación, factura), modo `FAST` |
| **Tiempo** | 10 s |
| **Resultado** | `comunicado_de_prensa`, confianza **0,95** |
| **Créditos** | no informados (`usage: null`) |

El **razonamiento** (`reasoning`) explica la decisión punto por punto: el encabezado típico de comunicado, la estructura narrativa con tablas resumen, las comparaciones interanuales. También explica por qué **no** es un estado financiero auditado: *"falta el informe del auditor, notas extensas, y la estructura formal"*. Se puede mostrar tal cual en la clase.

## 3. Schema automático · ✅ con observaciones

| | |
|---|---|
| **Pedido** | `generate_schema` con el `file_id` del comunicado y una indicación en español (período, ingresos, gastos, resultado neto, EBITDA, márgenes y variaciones) |
| **Tiempo** | 24 s |
| **Resultado** | Un schema con datos de la empresa (nombre, ticker, fechas, moneda) y los resultados **separados en históricos y ajustados por inflación**, cada uno con su valor y su variación interanual |
| **Validación** (`validate_schema`) | ✅ válido |
| **Guardado** (`configurations.create`) | `cfg-robwbsz63f6isxhbrowp4elqc90g` |
| **Créditos** | no informados |

**Observaciones:**
- **Los nombres y las descripciones vienen en inglés** (`companyName`, `netIncome`…), aunque la indicación estaba en español.
- **Los valores por defecto son pobres:** tier `cost_effective` y sin citas ni confianza. Al guardar la configuración se cambiaron a `agentic`, con `cite_sources`, `advanced_citations` y `confidence_scores`.
- **La API pide `file_id`, no el parse.** Es posible que lea el documento de nuevo por su cuenta.

## 4. Extract · ✅

| | |
|---|---|
| **Pedido** | `file_input` = el parse del comunicado, `configuration_id` = la configuración del punto 3 |
| **Tiempo** | 27 s |
| **Créditos** | no informados (`usage: null`) |
| **Metadata** | `document_metadata`, `page_metadata` y `row_metadata`, con citas (página, texto encontrado, cajas) y confianza por campo |

**Comparación contra el documento:**

| Campo | Extraído | En el comunicado |
|---|---|---|
| Ingresos (histórico) | 78124 · +24% | 78,124 · 24% ✅ |
| Gastos (histórico) | 27548 · +56% | 27,548 · 56% ✅ |
| Resultado neto (histórico) | 52414 · −8% | 52,414 · −8% ✅ |
| EBITDA | 63036 · +27% | 63,036 · 27% ✅ |
| Margen EBITDA del trimestre | 71 · −3 | 71% (era 74%) ✅ |
| Ingresos (ajustado por inflación) | 81148 · −4% | 81,148 · −4% ✅ |
| Gastos (ajustado) | 31406 · +13% | 31,406 · 13% ✅ |
| Resultado neto (ajustado) | 22162 · −43% | 22,162 · −43% ✅ |

**Otros datos:**
- Los valores vienen **como números** y no como texto, porque el schema usa `type: number`. Por eso ya no hace falta la limpieza de importes que teníamos antes.
- **Las citas vienen en puntos de página (612 × 792)**, la misma escala que las capturas de Parse. Se pueden dibujar sobre las capturas **sin `pdfjs`**.
- Hay una confianza baja para revisar: `reportDate` (0,72) tiene una cita que apunta al texto "reportDate", es decir al nombre del campo y no a la fecha. Buen ejemplo para la clase de por qué existe la confianza.

## 5. Costo de una página de los EEFF · ✅

Misma página (la 4: el estado de resultados, pura tabla), dos variantes:

| Variante | Créditos | Tiempo | Contenido | Confianza |
|---|---|---|---|---|
| Todas las opciones | **15** | 10 s | 1 tabla · 27 filas · 95 números | 1,0 |
| Sin `specialized_chart_parsing` ni `confidence_score_effort: high` | **10** | 7 s | **los mismos 95 números** (solo cambia `º` por `°` en 2 líneas) | 0,6 |

- **Conclusión:** en páginas sin gráficos, las dos opciones caras no cambian el contenido; cambian la **confianza informada**. Como la confianza es la base de la interpretación, se mantiene "high" por defecto.
- **Estimación para los EEFF (86 págs.):** entre ~860 y ~1.290 créditos.

## 6. Decisiones

1. **Sacar `max_pages` del paso Parse.** Hecho.
2. **Opciones caras como interruptores en el wizard:** "Gráficos con IA" y "Confianza precisa", prendidos por defecto. Así en clase se puede mostrar cuánto cambia el costo.
3. **Al guardar un schema generado, forzar citas, confianza y tier `agentic`.**
4. **Ofrecer traducir el schema generado al español** en el editor. Es una edición manual: se cambian los nombres y las guías, sin código que lo haga solo.
5. **Para saber el costo de Classify, Schema y Extract** hay que comparar con el saldo del panel de LlamaCloud (ver la [bitácora](bitacora.md#registro-de-créditos)).
