import pytest

from dev.core.classify import classify
from dev.core.errors import InvalidFileError
from dev.dto import Format


def test_classify_valid_pdf():
    content = b"%PDF-1.4\n..."
    assert classify(content, "document.pdf") == Format.PDF

def test_classify_invalid_pdf():
    content = b"Not a PDF"
    with pytest.raises(InvalidFileError) as exc_info:
        classify(content, "document.pdf")
    
    assert "inválido" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

def test_classify_file_too_large():
    from dev.config import settings
    
    # Create content larger than max_file_size_mb
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    content = b"0" * (max_bytes + 1)
    
    with pytest.raises(InvalidFileError) as exc_info:
        classify(content, "large.pdf")
        
    err_msg = str(exc_info.value)
    assert "large.pdf" in err_msg
    assert str(settings.max_file_size_mb) in err_msg
    # It should mention actual size
    actual_size_mb = (max_bytes + 1) / (1024 * 1024)
    assert f"{actual_size_mb:.2f}" in err_msg
