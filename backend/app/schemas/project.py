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


class ClarificationQuestion(BaseModel):
    id: str
    question: str


class ClarificationAnswerItem(BaseModel):
    id: str
    question: str
    answer: str = ""
    is_skipped: bool = False


class ClarificationAnswersRequest(BaseModel):
    answers: list[ClarificationAnswerItem]


class TeamAgentProposal(BaseModel):
    role_id: str
    role_name: str
    role_version: int = 1
    tier: str
    runtime: str = "api"
    model_id: str | None = None
    model_name: str = "Default LLM"
    fallback_model_id: str | None = None
    fallback_model_name: str = "Fallback LLM"
    is_reviewer: bool = False
    reason: str = ""


class TeamProposalResponse(BaseModel):
    project_id: str
    package: str
    brief_analysis: dict[str, Any]
    agents: list[TeamAgentProposal]
    cost_range: dict[str, Any]
    duration_range: dict[str, Any]
    has_reviewer: bool
    warnings: list[str]


class RecalculateEstimateRequest(BaseModel):
    agents: list[TeamAgentProposal]
    size: str = "M"


class RecalculateEstimateResponse(BaseModel):
    cost_range: dict[str, Any]
    duration_range: dict[str, Any]
    has_reviewer: bool
    warnings: list[str]


class ApproveTeamRequest(BaseModel):
    agents: list[TeamAgentProposal]
    clarification_notes: str | None = None


class ApproveTeamResponse(BaseModel):
    project_id: str
    gate_id: str
    status: str
    workspace_path: str
    team_charter_file: str
    agent_count: int


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    filename: str
    file_path: str
    summary: str
    created_at: datetime


class RoleTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: int
    name: str
    competencies: dict[str, Any]
    tier_min: str
    tier_default: str
    tools: list[Any]
    prompt: str
    dod: str


class ProjectCloseRequest(BaseModel):
    comments: str = "Proyek resmi ditutup dan hasil akhir disetujui oleh PO."


class ProjectCloseResponse(BaseModel):
    project_id: str
    status: str
    gate_g4_id: str
    laporan_penutupan: str
    paket_hasil_akhir_zip: str
    total_velocity: float
    avg_velocity: float
    total_cost: float
    done_items_count: int

