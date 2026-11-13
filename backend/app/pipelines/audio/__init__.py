"""Pipelines de audio con ElevenLabs.

    Texto → voz:  tts.py               limpia el texto (to_speech) → TTS con la voz clonada → MP3 (con caché)
    Voz → texto:  stt.py               Scribe → clean_transcript.py (muletillas, tartamudeos, [tos])
"""
