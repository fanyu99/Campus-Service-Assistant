from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api")


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get("/health", response_model=HealthResponse, response_class=UTF8JSONResponse)
async def health() -> HealthResponse:
    return HealthResponse()