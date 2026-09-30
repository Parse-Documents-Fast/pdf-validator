from dev.config import settings
from dev.core.errors import InvalidFileError
from dev.dto import Format


def classify(content: bytes, filename: str) -> Format:
    """Classify the content of a file as PDF or Markdown."""
    
    # 1. Size check
    actual_size_mb = len(content) / (1024 * 1024)
    if actual_size_mb > settings.max_file_size_mb:
        raise InvalidFileError(
            f"El archivo '{filename}' excede el límite de tamaño. "
            f"Esperado: <={settings.max_file_size_mb} MB. "
            f"Actual: {actual_size_mb:.2f} MB."
        )
        
    # 2. PDF check
    if content.startswith(b"%PDF-"):
        return Format.PDF
        
    # Markdown check will be implemented in Task 5
    raise InvalidFileError(f"Formato de archivo inválido para '{filename}'.")
