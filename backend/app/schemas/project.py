from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    default_team: list[Any]
    inception_agenda: list[Any]
    artifact_templates: list[Any]
    dod: list[Any]
    checks: list[Any]


class ProjectCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    profile_id: str = Field(..., min_length=2, max_length=50)
    brief: str = Field(..., min_length=5)
    profile_fields: dict[str, Any] = Field(default_factory=dict)
    deadline: datetime | None = None
    budget: float = 0.0
    currency: str = "IDR"
    language: str = "id"
    is_secret: bool = False


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    po_id: str
    title: str
    profile_id: str
    brief: str
    profile_fields: dict[str, Any]
    status: str
    deadline: datetime | None
    budget: float
    currency: str
    language: str
    is_secret: bool
    workspace_path: str
    created_at: datetime
    updated_at: datetime
