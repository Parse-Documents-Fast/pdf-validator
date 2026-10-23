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


def test_validate_structured_logs(monkeypatch):
    import io
    import json

    from dev.logger import setup_logging

    log_stream = io.StringIO()
    setup_logging(log_level="INFO", stream=log_stream)

    app = create_app()
    with TestClient(app) as test_client:
        secret_content = b"%PDF-1.4\nSUPER_SECRET_PAYLOAD"
        resp = test_client.post(
            "/validate", json=_payload("invoice.pdf", secret_content)
        )
        assert resp.status_code == 200

        output = log_stream.getvalue()
        # Assert secret content is NEVER logged
        assert "SUPER_SECRET_PAYLOAD" not in output

        # Assert JSON structured logs
        lines = [
            json.loads(line) for line in output.strip().split("\n") if line.strip()
        ]
        msgs = [item.get("msg") for item in lines]
        assert "file validated" in msgs
        assert "http request completed" in msgs

        validated_log = next(
            item for item in lines if item.get("msg") == "file validated"
        )
        assert validated_log["service"] == "pdf-validator"
        assert validated_log["level"] == "INFO"
        assert "checksum" in validated_log
        assert validated_log["size_bytes"] == len(secret_content)
        assert validated_log["original_format"] == "pdf"


def test_validation_failed_warn_log(monkeypatch):
    import io
    import json

    from dev.logger import setup_logging

    log_stream = io.StringIO()
    setup_logging(log_level="INFO", stream=log_stream)

    app = create_app()
    with TestClient(app) as test_client:
        resp = test_client.post(
            "/validate",
            json={"filename": "doc.pdf", "content_base64": "invalid_base64!!!"},
        )
        assert resp.status_code == 400

        output = log_stream.getvalue()
        lines = [
            json.loads(line) for line in output.strip().split("\n") if line.strip()
        ]
        fail_log = next(
            item for item in lines if item.get("msg") == "validation failed"
        )
        assert fail_log["level"] == "WARN"
        assert fail_log["reason"] == "invalid base64"
