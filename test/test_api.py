import pytest
from fastapi.testclient import TestClient

from dev.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_validate_pdf_success(client):
    files = {"file": ("test.pdf", b"%PDF-1.4\ncontent", "application/pdf")}
    response = client.post("/validate", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["original_format"] == "pdf"
    assert "checksum" in data


def test_validate_markdown_success(client):
    files = {"file": ("test.md", b"# Markdown", "text/markdown")}
    response = client.post("/validate", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["original_format"] == "markdown"
    assert "checksum" in data


def test_validate_invalid_file(client):
    files = {"file": ("test.txt", b"just text", "text/plain")}
    response = client.post("/validate", files=files)
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["title"] == "Archivo inválido"
    assert "detail" in data


def test_validate_missing_file(client):
    response = client.post("/validate")
    assert response.status_code == 400  # Overridden to 400 with RFC 9457 shape
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert "title" in data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
