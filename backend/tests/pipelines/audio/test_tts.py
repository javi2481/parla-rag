from app.pipelines.audio.tts import to_speech


def test_to_speech_strips_markdown_links_and_emojis():
    assert to_speech("**Hola** 👋 [mirá](https://x.com)\n- uno\n- dos") == "Hola mirá. uno. dos"


def test_to_speech_drops_chars_that_would_cost_credits():
    assert to_speech("Total: | $ 100 |\n\n\n✅ Listo!!") == "Total: $ 100. Listo!"
