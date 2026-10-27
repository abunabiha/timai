"""Pydantic schemas for Inception stage and Backlog management."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class InceptionAgendaItem(BaseModel):
    agenda_number: str
    title: str
    description: str
    lead_role: str
    expected_output: str
    discussion_id: str | None = None
    is_completed: bool = False
    selected_option: str | None = None


class InceptionStatusResponse(BaseModel):
    project_id: str
    profile_id: str
    agendas: list[InceptionAgendaItem]
    is_ready_for_assembly: bool
    has_assembled: bool
    gate_g2_status: str | None = None


class AssembleInceptionResponse(BaseModel):
    artifact_id: str
    version: int
    product_goal: str
    backlog_count: int
    files_generated: list[str]


class GateG2DecisionRequest(BaseModel):
    decision: str  # approved, revision_requested, rejected
    comments: str = ""


class GateG2DecisionResponse(BaseModel):
    gate: str
    decision: str
    comments: str
    decided_by: str
    decided_at: str


class BacklogItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    epic_id: str | None = None
    project_id: str
    title: str
    item_type: str
    acceptance_criteria: list[Any]
    story_points: int
    po_sort_order: int
    status: str
    source: str
    is_po_task: bool
    created_at: datetime


class EpicWithItemsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    sort_order: int
    items: list[BacklogItemSchema] = []


class ReorderBacklogRequest(BaseModel):
    ordered_item_ids: list[str]


class InceptionDocumentResponse(BaseModel):
    version: int
    content: str
    status: str
    product_goal: str
    gate_g2: dict[str, Any] | None = None
