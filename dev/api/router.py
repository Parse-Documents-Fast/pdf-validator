import anyio
from fastapi import APIRouter, File, UploadFile

from dev.core.checksum import calculate_checksum
from dev.core.classify import classify
from dev.dto import ValidateResponse

router = APIRouter()


@router.post("/validate", response_model=ValidateResponse)
async def validate_file(file: UploadFile = File(...)):  # noqa: B008
    # Read content
    content = await file.read()

    # Run classification in threadpool to avoid blocking event loop
    format_type = await anyio.to_thread.run_sync(classify, content, file.filename)
    checksum_val = await anyio.to_thread.run_sync(calculate_checksum, content)

    return ValidateResponse(original_format=format_type, checksum=checksum_val)


@router.get("/health")
async def health_check():
    return {"status": "ok"}
