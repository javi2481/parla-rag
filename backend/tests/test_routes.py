"""Pruebas de las rutas HTTP: configuración pública y respuestas cuando faltan las API keys."""
from fastapi.testclient import TestClient

from app.main import app
from app.pipelines.audio.settings import AudioSettings, get_audio_settings
from app.pipelines.documents.settings import DocumentsSettings, get_documents_settings


# Reemplaza la configuración real (.env) por una de prueba.
def use_settings(llama_key: str = "", elevenlabs_key: str = "") -> None:
    app.dependency_overrides[get_documents_settings] = lambda: DocumentsSettings(llama_cloud_api_key=llama_key, _env_file=None)
    app.dependency_overrides[get_audio_settings] = lambda: AudioSettings(elevenlabs_api_key=elevenlabs_key, _env_file=None)


# Sin API keys: la config dice que no están listos y las rutas responden 503.
def test_config_and_missing_keys():
    use_settings()
    with TestClient(app) as client:
        config = client.get("/api/config").json()
        assert config["documents"]["ready"] is False
        assert "total" in config["documents"]["fields"]
        assert config["audio"]["ready"] is False

        assert client.post("/api/audio/tts", json={"text": "hola"}).status_code == 503
        pdf = {"file": ("f.pdf", b"%PDF-", "application/pdf")}
        assert client.post("/api/documents/extract", files=pdf).status_code == 503
    app.dependency_overrides.clear()


# Un archivo que dice ser PDF pero no lo es se rechaza con 400, sin llegar a LlamaCloud.
def test_rejects_fake_pdf_with_400():
    use_settings(llama_key="x")
    with TestClient(app) as client:
        fake = {"file": ("f.pdf", b"MZ......not a pdf", "application/pdf")}
        response = client.post("/api/documents/extract", files=fake)
        assert response.status_code == 400
        assert "no es un PDF" in response.json()["detail"]
    app.dependency_overrides.clear()
