from datetime import datetime

from pydantic import BaseModel, Field


class LessonOut(BaseModel):
    id: str
    layer: str
    scope: str
    content: str
    evidence: str
    status: str
    occurrence_count: int
    project_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LessonCreate(BaseModel):
    layer: str = Field("preference", description="preference, retro, role")
    scope: str = Field("global", description="global, profile, project")
    content: str = Field(..., description="Isi pelajaran atau preferensi")
    evidence: str = Field("", description="Bukti asal pelajaran")
    project_id: str | None = Field(None, description="Opsional ID proyek jika scope project")


class LessonUpdate(BaseModel):
    content: str | None = None
    scope: str | None = None
    status: str | None = Field(None, description="suggested, active, inactive")


class ModelScorecardOut(BaseModel):
    id: str
    model_id: str | None = None
    model_name: str | None = None
    role_name: str
    profile_id: str
    item_count: int
    accepted_count: int
    rejected_count: int
    success_rate: float
    avg_revisions: float
    avg_cost: float

    model_config = {"from_attributes": True}


class CalibrationFactorOut(BaseModel):
    profile_id: str
    factor: float
    status: str
