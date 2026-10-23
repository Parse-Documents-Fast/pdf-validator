import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from dev.api.router import router
from dev.config import settings
from dev.core.errors import InvalidFileError
from dev.problem import problem_response

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    host, port = settings.http_addr.split(":")
    logger.info(
        "service started",
        extra={
            "fields": {
                "http_addr": f"{host if host else '0.0.0.0'}:{port}",
                "log_level": settings.log_level.upper(),
            }
        },
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="PDF Validator", lifespan=lifespan)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Healthcheck endpoint at DEBUG level to avoid log flooding
        if request.url.path == "/health" and response.status_code == 200:
            logger.debug(
                "http request completed",
                extra={
                    "fields": {
                        "http_method": request.method,
                        "http_path": request.url.path,
                        "http_status": response.status_code,
                        "duration_ms": duration_ms,
                    }
                },
            )
            return response

        level = logging.INFO
        if response.status_code >= 500:
            level = logging.ERROR
        elif response.status_code >= 400:
            level = logging.WARNING

        logger.log(
            level,
            "http request completed",
            extra={
                "fields": {
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "http_status": response.status_code,
                    "duration_ms": duration_ms,
                }
            },
        )
        return response

    app.include_router(router)

    @app.exception_handler(InvalidFileError)
    async def invalid_file_handler(request: Request, exc: InvalidFileError):
        fields = {"reason": exc.reason}
        if exc.checksum:
            fields["checksum"] = exc.checksum
        logger.warning(
            "validation failed",
            extra={"fields": fields},
        )
        return problem_response(
            status=400,
            title="Archivo inválido",
            detail=str(exc),
            instance=request.url.path,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.warning(
            "validation failed",
            extra={"fields": {"reason": "malformed request payload"}},
        )
        return problem_response(
            status=400,
            title="Bad Request",
            detail="Payload malformado o campos faltantes.",
            instance=request.url.path,
        )

    return app
