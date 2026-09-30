import os
from dev.config import Settings

def test_settings_defaults():
    # Remove env vars if they exist to test defaults
    os.environ.pop("HTTP_ADDR", None)
    os.environ.pop("MAX_FILE_SIZE_MB", None)
    
    settings = Settings(_env_file=None)
    assert settings.http_addr == ":8000"
    assert settings.max_file_size_mb == 10

def test_settings_env_overrides(monkeypatch):
    monkeypatch.setenv("HTTP_ADDR", ":9000")
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "20")
    
    settings = Settings(_env_file=None)
    assert settings.http_addr == ":9000"
    assert settings.max_file_size_mb == 20
