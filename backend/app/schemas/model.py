from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ModelCreateRequest(BaseModel):
    provider_id: str
    name: str = Field(..., min_length=2, max_length=100)
    model_identifier: str = Field(..., min_length=2, max_length=100)
    context_window: int = 128000
    input_price: float = 0.0
    output_price: float = 0.0
    supports_tools: bool = True
    supports_vision: bool = False
    competency_score: float = Field(default=3.0, ge=1.0, le=5.0)
    tier: str = Field(default="medium")  # low, medium, high, xhigh


class ModelUpdateRequest(BaseModel):
    name: str | None = None
    model_identifier: str | None = None
    context_window: int | None = None
    input_price: float | None = None
    output_price: float | None = None
    supports_tools: bool | None = None
    supports_vision: bool | None = None
    competency_score: float | None = Field(default=None, ge=1.0, le=5.0)
    tier: str | None = None
    is_active: bool | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str
    name: str
    model_identifier: str
    context_window: int
    input_price: float
    output_price: float
    supports_tools: bool
    supports_vision: bool
    competency_score: float
    tier: str
    is_active: bool
    created_at: datetime


class ModelHealthCheckResponse(BaseModel):
    model_id: str
    model_name: str
    is_healthy: bool
    message: str
