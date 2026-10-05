import base64
import binascii

import anyio
from fastapi import APIRouter

from dev.core.checksum import calculate_checksum
from dev.core.classify import classify
from dev.core.errors import InvalidFileError
from dev.dto import ValidateRequest, ValidateResponse

router = APIRouter()


@router.post("/validate", response_model=ValidateResponse)
async def validate_file(req: ValidateRequest):
    # Decode base64 payload (contract: pdf-docs/contracts/contracts-validator.md)
    try:
        content = base64.b64decode(req.content_base64, validate=True)
    except (binascii.Error, ValueError):
        raise InvalidFileError(f"content_base64 inválido para '{req.filename}'.")

    # Run classification in threadpool to avoid blocking event loop
    format_type = await anyio.to_thread.run_sync(classify, content, req.filename)
    checksum_val = await anyio.to_thread.run_sync(calculate_checksum, content)

    return ValidateResponse(original_format=format_type, checksum=checksum_val)


@router.get("/health")
async def health_check():
    return {"status": "ok"}
