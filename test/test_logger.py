import io
import json
import logging

from dev.logger import setup_logging


def test_json_logging():
    stream = io.StringIO()
    setup_logging(log_level="INFO", stream=stream)

    logger = logging.getLogger("pdf-validator-test")
    logger.info(
        "file validated", extra={"fields": {"checksum": "abc123", "size_bytes": 1024}}
    )

    output = stream.getvalue().strip()
    data = json.loads(output)

    assert data["level"] == "INFO"
    assert data["service"] == "pdf-validator"
    assert data["msg"] == "file validated"
    assert data["checksum"] == "abc123"
    assert data["size_bytes"] == 1024
    assert data["time"].endswith("Z")
    assert "T" in data["time"]


def test_invalid_log_level_fallback():
    stream = io.StringIO()
    effective = setup_logging(log_level="INVALID_XYZ", stream=stream)

    assert effective == "INFO"
    output = stream.getvalue()
    assert "invalid log level, fallback to info" in output
    assert "INVALID_XYZ" in output


def test_debug_level_filtering():
    stream_info = io.StringIO()
    setup_logging(log_level="INFO", stream=stream_info)
    logger = logging.getLogger("pdf-validator-filter-test")
    logger.debug("debug message that should be ignored")
    assert stream_info.getvalue() == ""

    stream_debug = io.StringIO()
    setup_logging(log_level="DEBUG", stream=stream_debug)
    logger.debug("debug message that should be visible")
    data = json.loads(stream_debug.getvalue().strip())
    assert data["level"] == "DEBUG"
    assert data["msg"] == "debug message that should be visible"
