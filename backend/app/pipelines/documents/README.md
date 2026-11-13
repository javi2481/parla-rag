# Pipeline de documentos (LlamaCloud)

Un **wizard** que recorre un documento paso por paso con los productos de LlamaCloud.
En cada paso se guarda **todo** lo que devolvió la plataforma, se mide y se interpreta.

Regla: no se implementa nada que LlamaCloud no haga de forma nativa. Nuestro código solo
pide, guarda, cuenta y explica.

## El flujo

```
1 Subir → 2 Parse → 3 Split → 4 Classify → 5 Schema → 6 Extract     (fase 4: Biblioteca)
             │ pjb-...  ↑         ↑                        ↑
             └──────────┴─────────┴────────────────────────┘
       el documento se parsea UNA vez: los pasos siguientes reciben solo el ID del parse
```

| Paso | Archivo | Qué hace | Producto de LlamaCloud | Créditos |
|---|---|---|---|---|
| 1 | `steps/s1_upload.py` | Sube el archivo y guarda una copia. Solo controla el tamaño. | `files.create` | 0 |
| 2 | `steps/s2_parse.py` | Lee el documento pidiendo **todo**: Markdown, texto, items con cajas, confianza por página, tablas en Excel, gráficos convertidos en tablas, capturas de página y 3 salidas extra. | `parsing.create` / `get` | los informa |
| 3 | `steps/s3_split.py` | Divide el documento en partes según categorías editables. | `split.create` / `get` | no los informa |
| 4 | `steps/s4_classify.py` | Elige el tipo de documento según reglas editables, con confianza y razonamiento. | `classify.create` / `get` | 0 sobre un parse |
| 5 | `steps/s5_schema.py` | Arma el schema: manual (tabla, plantilla o JSON) o automático (lo propone el agente). Lo valida y lo guarda con citas, confianza y tier agentic. | `extract.generate_schema`, `validate_schema`, `configurations` | no los informa |
| 6 | `steps/s6_extract.py` | Saca los datos del schema con la cita (página, texto, caja) y la confianza de cada uno. Puede limitarse a una parte del Split. | `extract.create` / `get` | los informa (`extract_credits`) |

Cada paso tiene:
- `EXPLICACION`: el texto para la clase.
- `start()`: arranca el job en LlamaCloud (Schema responde en el momento y no tiene `check()`).
- `check()`: consulta el job y, cuando termina, guarda todo.
- `summarize()`: arma las métricas y la interpretación, solo con lo que devolvió la API.
- `DEFAULTS` (Split, Classify, Schema): las opciones con las que arranca el editor del wizard.

`steps/jobs.py` tiene lo que comparten los pasos con job: consultar el estado y leer las opciones.

**Configuraciones nativas:** Parse (`parse_v2`), Split (`split_v1`), Classify (`classify_v2`) y el schema (`extract_v2`)
se guardan en `configurations` de LlamaCloud. LlamaCloud crea una versión nueva cada vez que se guarda con el mismo nombre.

## Repetir un paso

Repetir un paso no borra nada:
- la carpeta de la ejecución anterior se mueve a `historial/<carpeta>_<fecha>`;
- los pasos siguientes vuelven a pendiente (usaban el resultado anterior) y su carpeta también pasa al historial;
- el estado anterior de cada paso (con su `job_id`) queda en `run.json`, en la lista `historial`.

Al borrar una corrida se borran en LlamaCloud el archivo y **todos** los jobs, incluso los del historial.
Las configuraciones no se borran: son plantillas que pueden usar otras corridas.

## Dónde se guarda

Cada corrida es una carpeta en `backend/data/documents/runs/<id>/` (ver `app/core/runs/store.py`):

```
run.json        estado de cada paso, IDs de LlamaCloud, créditos e historial
1_upload/       original.pdf · request.json · response.json · metrics.json
2_parse/        request.json · configuration.json · response.json · document.md · text.txt · items.json
                metadata.json · forms.json · job_metadata.json · tables.xlsx · grounded_items.jsonl
                images/ · archivos/ · metrics.json
3_split/        request.json · configuration.json · response.json · segments.json · metrics.json
4_classify/     request.json · configuration.json · response.json · result.json · metrics.json
5_schema/       request.json · generated.json (solo automático) · schema.json · validation.json
                configuration.json · metrics.json
6_extract/      request.json · response.json · result.json · metadata.json · fields.json · boxes.json · metrics.json
historial/      las ejecuciones anteriores de cada paso
```

`request.json` es lo que se le pidió a LlamaCloud y `response.json`, su respuesta completa.
El resto son partes de esa respuesta separadas para leerlas fácil:
- `fields.json`: cada campo de Extract con su valor, confianza y citas (los que LlamaCloud no devolvió figuran como vacíos).
- `boxes.json`: una caja por renglón, lista para dibujar sobre la captura de su página (en puntos de la página, por ejemplo 612 × 792).

## Los archivos

| Archivo | Para qué |
|---|---|
| `pipeline.py` | La lista ordenada de pasos (**empezá a leer por acá**) |
| `steps/` | Un archivo por paso, más `jobs.py` |
| `router.py` | Rutas HTTP: `/api/documents/runs/...` |
| `settings.py` | API key, región, tier y versión de Parse, máximos |
| `client.py` | Crea el cliente de LlamaCloud |
| `errors.py` | `DocumentError`: errores con mensaje para el usuario |
