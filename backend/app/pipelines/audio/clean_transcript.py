"""Quita muletillas, tartamudeos y etiquetas de audio de una transcripción de voz.

Solo muletillas inequívocas: "este", "tipo", "viste", "o sea" suelen ser palabras reales
("quiero automatizar este proceso", "¿qué tipo de servicio?"), así que se conservan.
"""
import regex as re

_TAGS = re.compile(r"\[[^\]]*\]|\([^)]*\)")
_CUT_WORD = re.compile(r"(\p{L}+)-{1,2}(?=\s)")
_FILLERS = re.compile(
    r"(^|[\s,.;¿¡])(e+h+|e+m+|m+h+|a+h+|ehm+|mmm+|um+|uh+)(?=[\s,.;!?]|$)",
    re.IGNORECASE,
)
_REPEATED = re.compile(r"\b(\p{L}+)(?:[,\s]+\1\b)+", re.IGNORECASE)
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;!?])")
_DOUBLE_PUNCT = re.compile(r"([,;])\s*([,;.!?])")
_LEADING = re.compile(r"^[\s,;.]+")
_SPACES = re.compile(r"\s{2,}")


def clean_transcript(text: str) -> str:
    t = _TAGS.sub(" ", text)
    t = _CUT_WORD.sub(r"\1", t)
    for _ in range(2):
        t = _FILLERS.sub(r"\1", t)
    # Colapsa palabras repetidas: "de, de" / "por, por" → "de"
    t = _REPEATED.sub(r"\1", t)
    t = _SPACE_BEFORE_PUNCT.sub(r"\1", t)
    t = _DOUBLE_PUNCT.sub(r"\2", t)
    t = _SPACES.sub(" ", _LEADING.sub("", t)).strip()
    return t[:1].upper() + t[1:] if t else t
