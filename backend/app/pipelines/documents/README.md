# Pipeline de documentos (LlamaCloud)

Recibe un PDF o una foto de un comprobante y devuelve sus datos (fecha, proveedor, CUIT, importes, IVA…),
con la confianza de cada campo y el lugar del documento de donde salió cada dato.

Todo el trabajo pesado lo hace **LlamaCloud** con su SDK oficial (`llama-cloud`).

## El flujo

```
start()                                       poll()  (el navegador consulta cada tanto)
  1 validar  →  2 subir  →  3 crear job   ···   3 ¿terminó?  →  4 post-procesar  →  5 limpiar
```

| Paso | Archivo | Qué hace | ¿Usa LlamaCloud? |
|---|---|---|---|
| 1 | `steps/validate.py` | Revisa el tipo real del archivo, el tamaño (5 MB) y las páginas (3). Si falla, no se gasta nada. | No |
| 2 | `steps/upload.py` | Sube el archivo a LlamaCloud Files. | Sí: `files.create` |
| 3 | `steps/extract.py` | Crea el job de LlamaExtract con el schema y consulta su estado. | Sí: `extract.create` / `extract.get` |
| 4 | `steps/postprocess.py` | Deja solo los campos conocidos y convierte las citas en cajas para dibujar. | No |
| 5 | `steps/cleanup.py` | Borra el archivo y el job en LlamaCloud. | Sí: `files.delete` / `extract.delete` |

## Los archivos

| Archivo | Para qué |
|---|---|
| `settings.py` | API key, región, tier y versión de LlamaExtract, límite diario |
| `client.py` | Crea el cliente de LlamaCloud |
| `schema.py` | Qué campos se extraen, la guía de cada uno y la configuración de LlamaExtract |
| `pipeline.py` | Encadena los pasos en orden (**empezá a leer por acá**) |
| `jobs.py` | Tickets en memoria: el navegador nunca ve los IDs de LlamaCloud |
| `router.py` | Rutas HTTP: `POST /api/documents/extract` y `GET /api/documents/status/{ticket}` |
| `errors.py` | `DocumentError`: errores con mensaje para el usuario |

## Para cambiar qué se extrae

Se edita `schema.py`. La guía de cada campo va en su `description`, como recomienda la documentación de LlamaExtract.
