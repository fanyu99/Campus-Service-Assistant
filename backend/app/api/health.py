from fastapi import APIRouter

from app.core.responses import UTF8JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api")


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get("/health", response_model=HealthResponse, response_class=UTF8JSONResponse)
async def health() -> HealthResponse:
    return HealthResponse()
