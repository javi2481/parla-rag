import httpx
import pytest

from app.pipelines.audio.client import raise_for_error
from app.pipelines.audio.errors import AudioError


def test_missing_permission_is_explained():
    res = httpx.Response(401, json={"detail": {"status": "missing_permissions", "message": "..."}})
    with pytest.raises(AudioError, match="permiso «text_to_speech»"):
        raise_for_error(res, "text_to_speech", "x")


def test_ok_and_generic_errors():
    raise_for_error(httpx.Response(200), "text_to_speech", "x")
    with pytest.raises(AudioError, match="cuota"):
        raise_for_error(httpx.Response(429, text="busy"), "text_to_speech", "x")
    with pytest.raises(AudioError, match="^fallo$"):
        raise_for_error(httpx.Response(500, text="err"), "text_to_speech", "fallo")
