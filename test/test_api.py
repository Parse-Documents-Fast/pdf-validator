import base64

import pytest
from fastapi.testclient import TestClient

from dev.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def _payload(filename: str, content: bytes) -> dict:
    return {
        "filename": filename,
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


def test_validate_pdf_success(client):
    response = client.post("/validate", json=_payload("test.pdf", b"%PDF-1.4\ncontent"))
    assert response.status_code == 200
    data = response.json()
    assert data["original_format"] == "pdf"
    assert "checksum" in data


def test_validate_markdown_success(client):
    response = client.post("/validate", json=_payload("test.md", b"# Markdown"))
    assert response.status_code == 200
    data = response.json()
    assert data["original_format"] == "markdown"
    assert "checksum" in data


def test_validate_invalid_file(client):
    response = client.post("/validate", json=_payload("test.txt", b"just text"))
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["title"] == "Archivo inválido"
    assert "detail" in data


def test_validate_invalid_base64(client):
    response = client.post(
        "/validate", json={"filename": "test.pdf", "content_base64": "%%%no-base64%%%"}
    )
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"


def test_validate_missing_field(client):
    response = client.post("/validate", json={"filename": "test.pdf"})
    assert response.status_code == 400  # Overridden to 400 with RFC 9457 shape
    assert response.headers["content-type"] == "application/problem+json"


def test_validate_missing_body(client):
    response = client.post("/validate")
    assert response.status_code == 400  # Overridden to 400 with RFC 9457 shape
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert "title" in data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
