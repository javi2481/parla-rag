from app.pipelines.audio.cache import AudioCache


def test_roundtrip_and_key_depends_on_all_parts(tmp_path):
    c = AudioCache(tmp_path, max_mb=1)
    k1 = AudioCache.key(text="hola", model="a")
    assert k1 != AudioCache.key(text="hola", model="b")
    assert c.get(k1) is None
    c.put(k1, b"mp3")
    assert c.get(k1) == b"mp3"


def test_evicts_oldest_when_over_limit(tmp_path):
    c = AudioCache(tmp_path, max_mb=1)
    big = b"x" * (600 * 1024)
    c.put("old", big)
    c.put("new", big)
    assert c.get("old") is None and c.get("new") == big
