from typing import Any

from pydantic import BaseModel, Field


class ActiveAgentOut(BaseModel):
    project_id: str
    agent_id: str
    agent_name: str
    role_name: str
    task_id: str
    pbi_title: str
    state: str
    current_tool: str | None = None
    tokens_used: int = 0
    cost_spent: float = 0.0
    updated_at: str


class BudgetStatusOut(BaseModel):
    project_id: str
    currency: str
    project_budget: float
    total_spent: float
    sprint_id: str | None = None
    sprint_budget: float
    percent_used: float
    status: str
    warning_message: str | None = None
    is_paused: bool


class IncreaseBudgetRequest(BaseModel):
    additional_budget: float = Field(..., gt=0, description="Nominal tambahan anggaran")
    sprint_id: str | None = Field(None, description="Opsional ID sprint jika menambah anggaran sprint")


class ApproveRiskyActionRequest(BaseModel):
    action_type: str = Field(..., description="delete_workspace_file, new_domain_access, atau push_external_repo")
    target_resource: str = Field(..., description="Target file path, domain, atau repo URL")


class TaskExecutionRequest(BaseModel):
    force_review_decision: str | None = Field(None, description="Simulasikan keputusan review: 'approved' atau 'needs_revision'")


class TaskExecutionResponse(BaseModel):
    task_id: str
    status: str
    revisions_performed: int
    final_decision: str
    message: str
    issue_summary: str | None = None
    quality_report: dict[str, Any] | None = None
