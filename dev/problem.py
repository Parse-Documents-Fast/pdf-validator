from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str

def problem_response(status: int, title: str, detail: str, type: str = "about:blank", instance: str = "") -> JSONResponse:
    problem = ProblemDetails(
        type=type,
        title=title,
        status=status,
        detail=detail,
        instance=instance
    )
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(),
        media_type="application/problem+json"
    )
