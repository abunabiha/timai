from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ProviderCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    provider_type: str = Field(..., min_length=2, max_length=50)  # openai, anthropic, google, openrouter, fake
    base_url: str = Field(default="")
    api_key: str = Field(default="")


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    provider_type: str
    base_url: str
    is_active: bool
    has_api_key: bool = False
    api_key_masked: str = "******"
    created_at: datetime


class ProviderTestResponse(BaseModel):
    provider_id: str
    success: bool
    message: str
    latency_ms: int = 0
