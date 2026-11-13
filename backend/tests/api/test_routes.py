from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


def test_config_and_missing_keys():
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    with TestClient(app) as client:
        cfg = client.get("/api/config").json()
        assert cfg["invoice"]["ready"] is False and "total" in cfg["invoice"]["fields"]
        assert client.post("/api/audio/tts", json={"text": "hola"}).status_code == 503
        assert client.post("/api/invoice/extract", files={"file": ("f.pdf", b"%PDF-", "application/pdf")}).status_code == 503
    app.dependency_overrides.clear()


def test_rejects_fake_pdf_with_400():
    app.dependency_overrides[get_settings] = lambda: Settings(llama_cloud_api_key="x", _env_file=None)
    with TestClient(app) as client:
        r = client.post("/api/invoice/extract", files={"file": ("f.pdf", b"MZ......not a pdf", "application/pdf")})
        assert r.status_code == 400 and "no es un PDF" in r.json()["detail"]
    app.dependency_overrides.clear()
