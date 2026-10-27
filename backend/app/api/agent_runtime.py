from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user, require_role
from app.db.models import BacklogItem, Project, Sprint, Task, User
from app.db.session import get_db
from app.orchestrator.agent_runtime import agent_runtime, agent_tracker
from app.orchestrator.budget_guard import budget_guard
from app.schemas.agent_runtime import (
    ActiveAgentOut,
    ApproveRiskyActionRequest,
    BudgetStatusOut,
    IncreaseBudgetRequest,
    TaskExecutionRequest,
    TaskExecutionResponse,
)

router = APIRouter(tags=["Agent Runtime & Budget Guard"])


@router.get("/projects/{project_id}/active-agents", response_model=list[ActiveAgentOut])
async def get_active_agents(
    project_id: str,
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Returns currently active agents for the project ('Agen Sekarang' panel)."""
    return agent_tracker.get_active_for_project(project_id)


@router.get("/projects/{project_id}/budget-status", response_model=BudgetStatusOut)
async def get_budget_status(
    project_id: str,
    sprint_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Inspects project and sprint budget vs consumption with 50/80/100% thresholds."""
    return await budget_guard.get_budget_status(db, project_id, sprint_id)


@router.post("/projects/{project_id}/increase-budget", response_model=BudgetStatusOut)
async def increase_budget(
    project_id: str,
    payload: IncreaseBudgetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> dict[str, Any]:
    """Increases project budget (PO/Admin action) to unpause execution."""
    p_res = await db.execute(select(Project).where(Project.id == project_id))
    project = p_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    project.budget = float(project.budget or 0.0) + payload.additional_budget
    if project.status == "paused":
        project.status = "sprint"

    if payload.sprint_id:
        sp_res = await db.execute(select(Sprint).where(Sprint.id == payload.sprint_id))
        sprint = sp_res.scalar_one_or_none()
        if sprint:
            sprint.budget_limit = float(sprint.budget_limit or 0.0) + payload.additional_budget

    await db.commit()
    return await budget_guard.get_budget_status(db, project_id, payload.sprint_id)


@router.post("/projects/{project_id}/approve-risky-action")
async def approve_risky_action(
    project_id: str,
    payload: ApproveRiskyActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> dict[str, Any]:
    """Approves a high-risk action (delete file, new domain access, push external repo)."""
    key = budget_guard.approve_risky_action(
        project_id=project_id,
        action_type=payload.action_type,
        target_resource=payload.target_resource,
    )
    return {
        "status": "approved",
        "action_key": key,
        "message": f"Tindakan berisiko '{payload.action_type}' pada '{payload.target_resource}' disetujui oleh PO.",
    }


@router.post("/tasks/{task_id}/execute", response_model=TaskExecutionResponse)
async def execute_single_task(
    task_id: str,
    payload: TaskExecutionRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> dict[str, Any]:
    """Executes a single task with agent runtime, automated quality check, and cross-review."""
    force_decision = payload.force_review_decision if payload else None
    return await agent_runtime.execute_task_with_cross_review(
        db=db,
        task_id=task_id,
        force_review_decision=force_decision,
    )


@router.post("/sprints/{sprint_id}/execute-all")
async def execute_all_sprint_tasks(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> dict[str, Any]:
    """
    Executes all pending tasks in the sprint sequentially through Agent Runtime with cross-review.
    Replaces simulated execution with real runtime API execution!
    """
    sprint_stmt = select(Sprint).where(Sprint.id == sprint_id)
    s_res = await db.execute(sprint_stmt)
    sprint = s_res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

    pbis_stmt = (
        select(BacklogItem)
        .where(BacklogItem.sprint_id == sprint.id)
        .options(selectinload(BacklogItem.tasks))
    )
    bi_res = await db.execute(pbis_stmt)
    pbis = list(bi_res.scalars().all())

    executed_results = []
    for pbi in pbis:
        for t in pbi.tasks:
            if t.status in ("todo", "in_progress"):
                res = await agent_runtime.execute_task_with_cross_review(db=db, task_id=t.id)
                executed_results.append(res)

    sprint.status = "review"
    await db.commit()

    return {
        "sprint_id": sprint.id,
        "tasks_executed": len(executed_results),
        "results": executed_results,
        "sprint_status": sprint.status,
    }
