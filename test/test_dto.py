from dev.dto import Format, ValidateResponse


def test_format_enum():
    assert Format.PDF.value == "pdf"
    assert Format.MARKDOWN.value == "markdown"


def test_validate_response_dto():
    response = ValidateResponse(original_format=Format.PDF, checksum="fake_checksum")
    assert response.original_format == Format.PDF
    assert response.checksum == "fake_checksum"
