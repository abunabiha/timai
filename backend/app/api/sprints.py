"""Sprint and Kanban API: Planning, Daily Standup, Execution Simulation, Review (G3), Retro, Metrics."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user
from app.db.models import (
    BacklogItem,
    Project,
    Sprint,
    User,
)
from app.db.session import get_db
from app.orchestrator.scrum import scrum_engine
from app.schemas.inception import BacklogItemSchema
from app.schemas.scrum import (
    BurndownResponse,
    DailyStandupResponse,
    KanbanBoardResponse,
    KanbanCardMoveRequest,
    SprintCreateRequest,
    SprintResponse,
    SprintRetroRequest,
    SprintRetroResponse,
    SprintReviewRequest,
    SprintReviewResponse,
)

router = APIRouter(tags=["Sprints & Kanban"])


@router.get("/projects/{project_id}/sprints", response_model=list[SprintResponse])
async def list_project_sprints(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Sprint)
        .where(Sprint.project_id == project_id)
        .order_by(Sprint.sprint_number.asc())
    )
    res = await db.execute(stmt)
    sprints = list(res.scalars().all())
    return [SprintResponse.model_validate(s) for s in sprints]


@router.post("/projects/{project_id}/sprints/plan", response_model=SprintResponse)
async def plan_sprint(
    project_id: str,
    payload: SprintCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["po", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya Product Owner (PO) yang berhak merencanakan Sprint.",
        )

    sprint = await scrum_engine.plan_sprint(
        db=db,
        project_id=project_id,
        sprint_number=payload.sprint_number,
        sprint_goal=payload.sprint_goal,
        target_pbi_ids=payload.target_pbi_ids,
        budget_limit=payload.budget_limit,
        current_user=current_user,
    )
    return SprintResponse.model_validate(sprint)


@router.get("/sprints/{sprint_id}", response_model=SprintResponse)
async def get_sprint_detail(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Sprint).where(Sprint.id == sprint_id)
    res = await db.execute(stmt)
    sprint = res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")
    return SprintResponse.model_validate(sprint)


@router.post("/sprints/{sprint_id}/daily", response_model=DailyStandupResponse)
async def create_daily_standup(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s_stmt = select(Sprint).where(Sprint.id == sprint_id)
    s_res = await db.execute(s_stmt)
    sprint = s_res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

    result = await scrum_engine.generate_daily_standup(
        db=db,
        project_id=sprint.project_id,
        sprint_id=sprint.id,
    )
    return DailyStandupResponse(**result)


@router.post("/sprints/{sprint_id}/simulate")
async def simulate_sprint_work(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await scrum_engine.simulate_sprint_execution(db, sprint_id)
    return result


@router.post("/sprints/{sprint_id}/review", response_model=SprintReviewResponse)
async def review_sprint_endpoint(
    sprint_id: str,
    payload: SprintReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s_stmt = select(Sprint).where(Sprint.id == sprint_id)
    s_res = await db.execute(s_stmt)
    sprint = s_res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

    decisions_dict = {
        k: {"decision": v.decision, "notes": v.notes}
        for k, v in payload.decisions.items()
    }
    result = await scrum_engine.review_sprint_g3(
        db=db,
        project_id=sprint.project_id,
        sprint_id=sprint.id,
        decisions_per_pbi=decisions_dict,
        current_user=current_user,
    )
    return SprintReviewResponse(**result)


@router.post("/sprints/{sprint_id}/retro", response_model=SprintRetroResponse)
async def run_retro_endpoint(
    sprint_id: str,
    payload: SprintRetroRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s_stmt = select(Sprint).where(Sprint.id == sprint_id)
    s_res = await db.execute(s_stmt)
    sprint = s_res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

    lesson = await scrum_engine.run_retrospective(
        db=db,
        project_id=sprint.project_id,
        sprint_id=sprint.id,
        action_item=payload.action_item,
    )
    return SprintRetroResponse(
        lesson_id=lesson.id,
        content=lesson.content,
        layer=lesson.layer,
        status=lesson.status,
    )


@router.get("/sprints/{sprint_id}/burndown", response_model=BurndownResponse)
async def get_sprint_burndown(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s_stmt = select(Sprint).where(Sprint.id == sprint_id)
    s_res = await db.execute(s_stmt)
    sprint = s_res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

    result = await scrum_engine.get_burndown_and_velocity(
        db=db,
        project_id=sprint.project_id,
        sprint_id=sprint.id,
    )
    return BurndownResponse(**result)


@router.post("/sprints/{sprint_id}/pause", response_model=SprintResponse)
async def pause_sprint(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["po", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya PO yang berhak menjeda Sprint.")
    s_stmt = select(Sprint).where(Sprint.id == sprint_id)
    s_res = await db.execute(s_stmt)
    sprint = s_res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")
    sprint.status = "paused"
    await db.commit()
    await db.refresh(sprint)
    return SprintResponse.model_validate(sprint)


@router.post("/sprints/{sprint_id}/resume", response_model=SprintResponse)
async def resume_sprint(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["po", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya PO yang berhak melanjutkan Sprint.")
    s_stmt = select(Sprint).where(Sprint.id == sprint_id)
    s_res = await db.execute(s_stmt)
    sprint = s_res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")
    sprint.status = "active"
    await db.commit()
    await db.refresh(sprint)
    return SprintResponse.model_validate(sprint)


@router.post("/sprints/{sprint_id}/cancel", response_model=SprintResponse)
async def cancel_sprint(
    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["po", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya PO yang berhak membatalkan Sprint.")
    s_stmt = select(Sprint).where(Sprint.id == sprint_id)
    s_res = await db.execute(s_stmt)
    sprint = s_res.scalar_one_or_none()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint tidak ditemukan")

    sprint.status = "cancelled"
    # Return PBIs to product_backlog
    pbis_stmt = select(BacklogItem).where(BacklogItem.sprint_id == sprint.id)
    bi_res = await db.execute(pbis_stmt)
    for pbi in bi_res.scalars().all():
        if pbi.status != "done":
            pbi.status = "product_backlog"
            pbi.sprint_id = None

    await db.commit()
    await db.refresh(sprint)
    return SprintResponse.model_validate(sprint)


@router.get("/projects/{project_id}/kanban", response_model=KanbanBoardResponse)
async def get_kanban_board(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve Kanban board columns with all cards (FR-10.1 & FR-10.2)."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.backlog_items),
            selectinload(Project.sprints),
        )
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    # Define standard columns per PRD FR-10.1
    columns: dict[str, list[BacklogItemSchema]] = {
        "product_backlog": [],
        "sprint_backlog": [],
        "in_progress": [],
        "in_review": [],
        "waiting_po": [],
        "done": [],
        "blocked": [],
    }

    # Find active sprint if any
    active_sprint = next((s for s in project.sprints if s.status in ["active", "review", "paused"]), None)

    for item in project.backlog_items:
        col = item.status if item.status in columns else "product_backlog"
        columns[col].append(BacklogItemSchema.model_validate(item))

    # Sort each column by po_sort_order
    for col in columns:
        columns[col].sort(key=lambda x: x.po_sort_order)

    return KanbanBoardResponse(
        project_id=project.id,
        sprint_id=active_sprint.id if active_sprint else None,
        columns=columns,
    )


@router.patch("/backlog/{item_id}/status", response_model=BacklogItemSchema)
async def move_kanban_card(
    item_id: str,
    payload: KanbanCardMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(BacklogItem).where(BacklogItem.id == item_id)
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item backlog tidak ditemukan")

    allowed_statuses = [
        "product_backlog",
        "sprint_backlog",
        "in_progress",
        "in_review",
        "waiting_po",
        "done",
        "blocked",
    ]
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Status tidak valid.")

    item.status = payload.status
    await db.commit()
    await db.refresh(item)
    return BacklogItemSchema.model_validate(item)
