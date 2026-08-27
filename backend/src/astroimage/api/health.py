from fastapi import APIRouter
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, operation_id="health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
