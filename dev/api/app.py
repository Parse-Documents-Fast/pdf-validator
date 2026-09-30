from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from dev.api.router import router
from dev.core.errors import InvalidFileError
from dev.problem import problem_response


def create_app() -> FastAPI:
    app = FastAPI(title="PDF Validator")

    app.include_router(router)

    @app.exception_handler(InvalidFileError)
    async def invalid_file_handler(request: Request, exc: InvalidFileError):
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
        return problem_response(
            status=400,
            title="Bad Request",
            detail="Payload malformado o campos faltantes.",
            instance=request.url.path,
        )

    return app
