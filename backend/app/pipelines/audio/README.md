# Pipeline de audio (ElevenLabs)

Dos flujos: **texto a voz** (con la voz clonada) y **voz a texto** (transcripción limpia).

## Texto a voz: `tts.py`

```
texto  →  limpiar (to_speech)  →  ¿está en la caché?  ──sí──→  MP3
                                         │ no
                                         ↓
                              ElevenLabs text-to-speech  →  guardar en la caché  →  MP3
```

- Se limpia el texto (markdown, links, emojis) porque ElevenLabs cobra por carácter.
- La caché está en disco (`data/audio/cache/`). El mismo texto, con la misma voz y el mismo modelo, nunca se paga dos veces.

## Voz a texto: `stt.py`

```
audio  →  ElevenLabs Scribe  →  texto crudo  →  limpiar (clean_transcript)  →  texto limpio
```

## Los archivos

| Archivo | Para qué |
|---|---|
| `settings.py` | API key, voz, modelos, caché y límites |
| `client.py` | URL de ElevenLabs y cómo se explican sus errores (permisos, cuota) |
| `tts.py` | Texto a voz |
| `stt.py` | Voz a texto |
| `cache.py` | La caché en disco de los audios generados |
| `clean_transcript.py` | Saca muletillas, tartamudeos y etiquetas como [tos] |
| `router.py` | Rutas HTTP: `POST /api/audio/tts` y `POST /api/audio/transcribe` |
| `errors.py` | `AudioError`: errores con mensaje para el usuario |
