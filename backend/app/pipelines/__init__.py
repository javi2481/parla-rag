"""Los pipelines de Parla RAG. Cada carpeta es autocontenida: tiene su configuración,
su cliente del proveedor, sus pasos y sus rutas HTTP.

    documents/   documentos con LlamaCloud (wizard Subir → Parse → Split → Classify → Schema → Extract)
                 y bibliotecas (índice compartido, búsqueda y chat)

Para entender un pipeline: leé su README.md, después wizard/wizard_flow.py y por último sus pasos (wizard/steps/).
"""
