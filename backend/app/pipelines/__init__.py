"""Los pipelines de Parla. Cada carpeta es autocontenida: tiene su configuración,
su cliente del proveedor, sus pasos y sus rutas HTTP.

    documents/   documentos con LlamaCloud (validar, subir, extraer, post-procesar, limpiar)
    audio/       voz con ElevenLabs (texto a voz y voz a texto)

Para entender un pipeline: leé su README.md, después pipeline.py (o tts.py / stt.py) y por último sus pasos.
"""
