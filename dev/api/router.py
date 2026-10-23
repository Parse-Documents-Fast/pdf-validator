import base64
import binascii
import logging
import time

import anyio
from fastapi import APIRouter

from dev.core.checksum import calculate_checksum
from dev.core.classify import classify
from dev.core.errors import InvalidFileError
from dev.dto import ValidateRequest, ValidateResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/validate", response_model=ValidateResponse)
async def validate_file(req: ValidateRequest):
    start = time.perf_counter()

    # Decode base64 payload (contract: pdf-docs/contracts/contracts-validator.md)
    try:
        content = base64.b64decode(req.content_base64, validate=True)
    except (binascii.Error, ValueError):
        raise InvalidFileError(
            f"content_base64 inválido para '{req.filename}'.",
            reason="invalid base64",
        )

    checksum_val = await anyio.to_thread.run_sync(calculate_checksum, content)

    # Run classification in threadpool to avoid blocking event loop
    try:
        format_type = await anyio.to_thread.run_sync(classify, content, req.filename)
    except InvalidFileError as err:
        err.checksum = checksum_val
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "file validated",
        extra={
            "fields": {
                "checksum": checksum_val,
                "original_format": format_type.value,
                "size_bytes": len(content),
                "duration_ms": duration_ms,
            }
        },
    )

    return ValidateResponse(original_format=format_type, checksum=checksum_val)


@router.get("/health")
async def health_check():
    return {"status": "ok"}
