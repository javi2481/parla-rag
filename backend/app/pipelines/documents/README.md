# Pipeline de documentos (LlamaCloud)

Un **wizard** que recorre un documento paso por paso con los productos de LlamaCloud.
En cada paso se guarda **todo** lo que devolvió la plataforma, se mide y se interpreta.

Regla: no se implementa nada que LlamaCloud no haga de forma nativa. Nuestro código solo
pide, guarda, cuenta y explica.

## El flujo

```
1 Subir  →  2 Parse  →  (próximas fases: Split · Classify · Schema · Extract · Biblioteca)
```

| Paso | Archivo | Qué hace | Producto de LlamaCloud |
|---|---|---|---|
| 1 | `steps/s1_upload.py` | Sube el archivo y guarda una copia. Solo controla el tamaño. | `files.create` |
| 2 | `steps/s2_parse.py` | Lee el documento pidiendo **todo**: Markdown, texto, items con cajas, confianza por página, tablas en Excel, gráficos convertidos en tablas, capturas de página. | `parsing.create` / `parsing.get` |

Cada paso tiene:
- `EXPLICACION`: el texto para la clase.
- `start()`: arranca el job en LlamaCloud.
- `check()`: consulta el job y, cuando termina, guarda todo.
- `summarize()`: arma las métricas y la interpretación.

## Dónde se guarda

Cada corrida es una carpeta en `backend/data/documents/runs/<id>/` (ver `app/core/runs/store.py`):

```
run.json             estado de cada paso, IDs de LlamaCloud, créditos
1_upload/            original.pdf · request.json · response.json · metrics.json
2_parse/             request.json · response.json · document.md · text.txt · items.json
                     metadata.json · forms.json · job_metadata.json · tables.xlsx
                     grounded_items.jsonl · images/ · metrics.json
```

`request.json` es lo que se le pidió a LlamaCloud y `response.json`, su respuesta completa.
El resto son partes de esa respuesta separadas para leerlas fácil.

## Los archivos

| Archivo | Para qué |
|---|---|
| `pipeline.py` | La lista ordenada de pasos (**empezá a leer por acá**) |
| `steps/` | Un archivo por paso |
| `router.py` | Rutas HTTP: `/api/documents/runs/...` |
| `settings.py` | API key, región, tier y versión de Parse, máximos |
| `client.py` | Crea el cliente de LlamaCloud |
| `errors.py` | `DocumentError`: errores con mensaje para el usuario |
