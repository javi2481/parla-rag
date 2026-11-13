"""Limpia una transcripción de voz: saca muletillas, tartamudeos y etiquetas de audio.

Solo se sacan las muletillas inequívocas ("eh", "mmm", "um"). Palabras como "este", "tipo",
"viste" u "o sea" suelen ser palabras reales ("quiero automatizar este proceso",
"¿qué tipo de servicio?"), así que se dejan.
"""
import regex as re

# Etiquetas de audio como [tos] o (risas).
TAGS = re.compile(r"\[[^\]]*\]|\([^)]*\)")
# Palabras cortadas con guion: "de--" → "de".
CUT_WORD = re.compile(r"(\p{L}+)-{1,2}(?=\s)")
# Muletillas: eh, eeeh, em, mmm, ah, um, uh...
FILLERS = re.compile(
    r"(^|[\s,.;¿¡])(e+h+|e+m+|m+h+|a+h+|ehm+|mmm+|um+|uh+)(?=[\s,.;!?]|$)",
    re.IGNORECASE,
)
# Palabras repetidas seguidas: "de, de" o "por por".
REPEATED = re.compile(r"\b(\p{L}+)(?:[,\s]+\1\b)+", re.IGNORECASE)
SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;!?])")
DOUBLE_PUNCT = re.compile(r"([,;])\s*([,;.!?])")
LEADING_PUNCT = re.compile(r"^[\s,;.]+")
EXTRA_SPACES = re.compile(r"\s{2,}")


# Devuelve la transcripción limpia, empezando con mayúscula.
def clean_transcript(text: str) -> str:
    t = TAGS.sub(" ", text)
    t = CUT_WORD.sub(r"\1", t)

    # Se pasa dos veces porque al sacar una muletilla puede quedar otra al lado.
    t = FILLERS.sub(r"\1", t)
    t = FILLERS.sub(r"\1", t)

    t = REPEATED.sub(r"\1", t)
    t = SPACE_BEFORE_PUNCT.sub(r"\1", t)
    t = DOUBLE_PUNCT.sub(r"\2", t)
    t = LEADING_PUNCT.sub("", t)
    t = EXTRA_SPACES.sub(" ", t).strip()

    if not t:
        return t
    return t[0].upper() + t[1:]
