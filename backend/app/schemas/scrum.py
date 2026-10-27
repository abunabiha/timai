"""Pydantic schemas for Scrum Engine, Sprints, Daily Standup, and Kanban."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.inception import BacklogItemSchema


class SprintCreateRequest(BaseModel):
    sprint_number: int = 1
    sprint_goal: str | None = None
    target_pbi_ids: list[str] | None = None
    budget_limit: float = 0.0


class SprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    sprint_number: int
    sprint_goal: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    budget_limit: float
    status: str
    velocity_achieved: int
    created_at: datetime


class PbiReviewDecision(BaseModel):
    decision: str  # accept, reject
    notes: str = ""


class SprintReviewRequest(BaseModel):
    decisions: dict[str, PbiReviewDecision]  # pbi_id -> PbiReviewDecision


class SprintReviewResponse(BaseModel):
    sprint_id: str
    gate_decision: str
    velocity_achieved: int
    accepted_count: int
    rejected_count: int


class SprintRetroRequest(BaseModel):
    action_item: str = "Tingkatkan koordinasi antara Writer dan Reviewer pada fase awal drafting."


class SprintRetroResponse(BaseModel):
    lesson_id: str
    content: str
    layer: str
    status: str


class DailyStandupResponse(BaseModel):
    date: str
    sprint_number: int
    done_count: int
    active_count: int
    blocked_count: int
    file_path: str


class BurndownResponse(BaseModel):
    sprint_number: int
    total_planned_points: int
    completed_points: int
    remaining_points: int
    velocity_achieved: int
    burndown: list[dict[str, Any]]


class KanbanCardMoveRequest(BaseModel):
    status: str


class KanbanBoardResponse(BaseModel):
    project_id: str
    sprint_id: str | None = None
    columns: dict[str, list[BacklogItemSchema]]
