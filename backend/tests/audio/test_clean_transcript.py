from app.pipelines.audio.clean_transcript import clean_transcript


def test_removes_fillers_in_the_users_example():
    assert clean_transcript("mi cuello de botella son, eh, 5.000 facturas por mes") == "Mi cuello de botella son, 5.000 facturas por mes"


def test_collapses_stutters_and_tags():
    assert clean_transcript("Eeeh, no quiero por, por el tema de, de-- [tos] natación") == "No quiero por el tema de natación"


def test_keeps_real_words_like_este_and_tipo():
    assert clean_transcript("quiero automatizar este proceso") == "Quiero automatizar este proceso"
    assert clean_transcript("¿qué tipo de servicio ofrecen?") == "¿qué tipo de servicio ofrecen?"


def test_still_removes_unambiguous_fillers():
    assert clean_transcript("hola, eh, buen día, mmm, cómo estás") == "Hola, buen día, cómo estás"
