"""Pipeline de extracción de facturas con LlamaCloud (LlamaExtract v2).

Orden de los pasos (ver pipeline.py):

    1. steps/validate.py     tipo real del archivo, tamaño y páginas (local, sin costo)
    2. steps/upload.py       sube el archivo a LlamaCloud Files (purpose="extract")
    3. steps/extract.py      crea el job de Extract con schema.py y lo consulta (polling)
    4. steps/postprocess.py  normaliza valores, convierte citas en cajas y confianza por campo
    5. steps/cleanup.py      borra el archivo y el job de LlamaCloud

schema.py tiene los campos, el JSON Schema y la configuración de Extract.
jobs.py guarda los tickets opacos que ve el navegador (nunca los IDs del proveedor).
"""
