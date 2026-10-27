import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Base model class with standard type mappings."""
    type_annotation_map = {
        dict[str, Any]: JSON,
        list[Any]: JSON,
    }


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="po")  # admin, po, viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="po", cascade="all, delete-orphan")


class ProjectProfile(Base):
    __tablename__ = "project_profiles"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # software, iot, proposal, jurnal, buku
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    default_team: Mapped[list[Any]] = mapped_column(JSON, default=list)
    inception_agenda: Mapped[list[Any]] = mapped_column(JSON, default=list)
    artifact_templates: Mapped[list[Any]] = mapped_column(JSON, default=list)
    dod: Mapped[list[Any]] = mapped_column(JSON, default=list)
    checks: Mapped[list[Any]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    po_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(50), ForeignKey("project_profiles.id"), nullable=False)
    brief: Mapped[str] = mapped_column(Text, nullable=False, default="")
    profile_fields: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="brief", nullable=False)  # brief, clarification, team_proposed, inception, sprint, closed
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    budget: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="IDR")
    language: Mapped[str] = mapped_column(String(10), default="id")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    workspace_path: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    po: Mapped["User"] = relationship("User", back_populates="projects")
    profile: Mapped["ProjectProfile"] = relationship("ProjectProfile")
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="project", cascade="all, delete-orphan")
    discussions: Mapped[list["Discussion"]] = relationship("Discussion", back_populates="project", cascade="all, delete-orphan")
    backlog_items: Mapped[list["BacklogItem"]] = relationship("BacklogItem", back_populates="project", cascade="all, delete-orphan")
    sprints: Mapped[list["Sprint"]] = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class RoleTemplate(Base):
    __tablename__ = "role_templates"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    competencies: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    tier_min: Mapped[str] = mapped_column(String(20), default="low")  # low, medium, high, xhigh
    tier_default: Mapped[str] = mapped_column(String(20), default="medium")
    tools: Mapped[list[Any]] = mapped_column(JSON, default=list)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    dod: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)  # openai, anthropic, google, openrouter, fake
    base_url: Mapped[str] = mapped_column(String(255), default="")
    api_key_encrypted: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    models: Mapped[list["Model"]] = relationship("Model", back_populates="provider", cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id: Mapped[str] = mapped_column(String(36), ForeignKey("providers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_identifier: Mapped[str] = mapped_column(String(100), nullable=False)
    context_window: Mapped[int] = mapped_column(Integer, default=128000)
    input_price: Mapped[float] = mapped_column(Float, default=0.0)  # price per 1M tokens
    output_price: Mapped[float] = mapped_column(Float, default=0.0)
    supports_tools: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False)
    competency_score: Mapped[float] = mapped_column(Float, default=3.0)  # 1 to 5
    tier: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, xhigh
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    provider: Mapped["Provider"] = relationship("Provider", back_populates="models")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    role_template_id: Mapped[str] = mapped_column(String(50), nullable=False)
    role_version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("models.id"), nullable=True)
    fallback_model_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("models.id"), nullable=True)
    runtime: Mapped[str] = mapped_column(String(20), default="api")  # api, cli
    permissions: Mapped[list[Any]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    project: Mapped["Project"] = relationship("Project", back_populates="agents")


class Discussion(Base):
    __tablename__ = "discussions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    discussion_type: Mapped[str] = mapped_column(String(50), default="general")  # inception, planning, retro, clarification
    agenda: Mapped[str] = mapped_column(String(255), nullable=False)
    participants: Mapped[list[Any]] = mapped_column(JSON, default=list)
    speaker_order: Mapped[list[Any]] = mapped_column(JSON, default=list)
    round_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="draft")  # draft, running, synthesis, waiting_po, finished
    synthesis: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    project: Mapped["Project"] = relationship("Project", back_populates="discussions")
    contributions: Mapped[list["Contribution"]] = relationship("Contribution", back_populates="discussion", cascade="all, delete-orphan")
    confirmations: Mapped[list["Confirmation"]] = relationship("Confirmation", back_populates="discussion", cascade="all, delete-orphan")


class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discussion_id: Mapped[str] = mapped_column(String(36), ForeignKey("discussions.id"), nullable=False, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id"), nullable=True)
    round_number: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    discussion: Mapped["Discussion"] = relationship("Discussion", back_populates="contributions")


class Confirmation(Base):
    __tablename__ = "confirmations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discussion_id: Mapped[str] = mapped_column(String(36), ForeignKey("discussions.id"), nullable=False, index=True)
    options: Mapped[list[Any]] = mapped_column(JSON, default=list)  # e.g. [{"id": "A", "label": "..."}, {"id": "B", "label": "..."}]
    selected_option: Mapped[str | None] = mapped_column(String(50), nullable=True)
    po_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    discussion: Mapped["Discussion"] = relationship("Discussion", back_populates="confirmations")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discussion_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("discussions.id"), nullable=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, default="")
    alternatives: Mapped[list[Any]] = mapped_column(JSON, default=list)
    decided_by: Mapped[str] = mapped_column(String(100), default="PO")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)  # prd, docx, charter, code, etc.
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by_agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id"), nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), default="draft")  # draft, under_review, accepted, rejected
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class ProductGoal(Base):
    __tablename__ = "product_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class Epic(Base):
    __tablename__ = "epics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class BacklogItem(Base):
    __tablename__ = "backlog_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    epic_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("epics.id"), nullable=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), default="story")  # story, chapter, task, bug
    acceptance_criteria: Mapped[list[Any]] = mapped_column(JSON, default=list)
    story_points: Mapped[int] = mapped_column(Integer, default=1)
    po_sort_order: Mapped[int] = mapped_column(Integer, default=0)  # only PO can reorder
    status: Mapped[str] = mapped_column(String(30), default="product_backlog")  # product_backlog, sprint_backlog, in_progress, in_review, waiting_po, done, blocked
    source: Mapped[str] = mapped_column(String(30), default="team_proposed")  # po, team_proposed
    sprint_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sprints.id"), nullable=True)
    is_po_task: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    project: Mapped["Project"] = relationship("Project", back_populates="backlog_items")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="backlog_item", cascade="all, delete-orphan")


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    sprint_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sprint_goal: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    budget_limit: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="planned")  # planned, active, review, completed, cancelled
    velocity_achieved: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    project: Mapped["Project"] = relationship("Project", back_populates="sprints")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backlog_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("backlog_items.id"), nullable=False, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id"), nullable=True)
    step_type: Mapped[str] = mapped_column(String(50), default="execute")  # execute, review, verify
    branch_name: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(30), default="todo")  # todo, in_progress, review, waiting_po, done
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    backlog_item: Mapped["BacklogItem"] = relationship("BacklogItem", back_populates="tasks")


class Increment(Base):
    __tablename__ = "increments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sprint_id: Mapped[str] = mapped_column(String(36), ForeignKey("sprints.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    passed_pbi_ids: Mapped[list[Any]] = mapped_column(JSON, default=list)
    artifact_ids: Mapped[list[Any]] = mapped_column(JSON, default=list)
    po_decision: Mapped[str] = mapped_column(String(30), default="pending")  # pending, accepted, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class Gate(Base):
    __tablename__ = "gates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    gate_type: Mapped[str] = mapped_column(String(10), nullable=False)  # G1, G2, G3, G4
    target_id: Mapped[str] = mapped_column(String(36), default="")
    decision: Mapped[str] = mapped_column(String(30), default="pending")  # pending, approved, rejected, revision_requested
    comments: Mapped[str] = mapped_column(Text, default="")
    decided_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id"), nullable=True)
    requested_model: Mapped[str] = mapped_column(String(100), nullable=False)
    actual_model: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    layer: Mapped[str] = mapped_column(String(50), nullable=False)  # preference, retro, role
    scope: Mapped[str] = mapped_column(String(50), default="global")  # global, profile, project
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="suggested")  # suggested, active, inactive
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class ModelScorecard(Base):
    __tablename__ = "model_scorecards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("models.id"), nullable=True)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(50), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_revisions: Mapped[float] = mapped_column(Float, default=0.0)
    avg_cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class ExampleLibrary(Base):
    __tablename__ = "example_libraries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(50), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_artifact_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_cross_project_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
