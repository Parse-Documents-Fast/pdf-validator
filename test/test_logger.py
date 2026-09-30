import io

from dev.logger import setup_logging


def test_json_logging():
    stream = io.StringIO()
    # Configure the logger to use the string stream instead of stdout for testing
    setup_logging(stream)
    
    import structlog
    logger = structlog.get_logger("pdf-validator")
    logger.info("test message", extra_field="value")
    
    output = stream.getvalue()
    assert "test message" in output
    assert "extra_field" in output
    assert "value" in output
    
    # Verify it is valid JSON
    import json
    data = json.loads(output)
    assert data["event"] == "test message"
    assert data["extra_field"] == "value"
