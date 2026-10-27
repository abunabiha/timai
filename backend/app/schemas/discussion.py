from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DiscussionCreateRequest(BaseModel):
    project_id: str
    agenda: str = Field(..., min_length=3, max_length=255)
    discussion_type: str = "inception"
    participants: list[str] | None = None


class ContributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    discussion_id: str
    agent_id: str | None
    round_number: int
    content: str
    token_count: int
    created_at: datetime


class ConfirmationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    discussion_id: str
    options: list[Any]
    selected_option: str | None
    po_feedback: str | None
    decided_by_user_id: str | None
    decided_at: datetime | None
    created_at: datetime


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    discussion_id: str | None
    project_id: str
    summary: str
    rationale: str
    alternatives: list[Any]
    decided_by: str
    created_at: datetime


class DiscussionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    discussion_type: str
    agenda: str
    participants: list[Any]
    speaker_order: list[Any]
    round_number: int
    status: str
    synthesis: dict[str, Any]
    cost: float
    created_at: datetime
    updated_at: datetime
    contributions: list[ContributionResponse] = []
    confirmations: list[ConfirmationResponse] = []


class DecisionActionRequest(BaseModel):
    action: str = Field(..., pattern="^(approve_proposed|choose_option|redirect|continue_discussion)$")
    selected_option: str | None = None  # "A" or "B" when choose_option
    po_notes: str | None = None


class BatchDecisionItem(BaseModel):
    confirmation_id: str
    action: str = "approve_proposed"
    selected_option: str | None = None
    po_notes: str | None = None


class BatchDecisionRequest(BaseModel):
    decisions: list[BatchDecisionItem]
