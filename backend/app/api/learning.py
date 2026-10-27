from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user, require_role
from app.db.models import Lesson, Model, ModelScorecard, User
from app.db.session import get_db
from app.orchestrator.learning import learning_engine
from app.schemas.learning import (
    CalibrationFactorOut,
    LessonCreate,
    LessonOut,
    LessonUpdate,
    ModelScorecardOut,
)

router = APIRouter(prefix="/learning", tags=["Learning Engine (FR-14)"])


@router.get("/lessons", response_model=list[LessonOut])
async def list_lessons(
    status_filter: str | None = Query(None, alias="status"),
    scope: str | None = Query(None),
    project_id: str | None = Query(None),
    layer: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Lesson]:
    """Lists system lessons with optional filters (FR-14.8)."""
    stmt = select(Lesson).order_by(Lesson.created_at.desc())
    if status_filter:
        stmt = stmt.where(Lesson.status == status_filter)
    if scope:
        stmt = stmt.where(Lesson.scope == scope)
    if project_id:
        stmt = stmt.where(Lesson.project_id == project_id)
    if layer:
        stmt = stmt.where(Lesson.layer == layer)

    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("/lessons", response_model=LessonOut)
async def create_lesson(
    payload: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> Lesson:
    """Manually creates a new lesson (defaults to 'suggested')."""
    return await learning_engine.extract_or_update_lesson(
        db=db,
        content=payload.content,
        layer=payload.layer,
        evidence=payload.evidence or f"Ditambahkan secara manual oleh {current_user.name}",
        preferred_scope=payload.scope,
    )


@router.patch("/lessons/{lesson_id}", response_model=LessonOut)
async def update_lesson(
    lesson_id: str,
    payload: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> Lesson:
    """Updates lesson content, scope, or status."""
    stmt = select(Lesson).where(Lesson.id == lesson_id)
    res = await db.execute(stmt)
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Pelajaran tidak ditemukan")

    if payload.content is not None:
        lesson.content = payload.content.strip()
    if payload.scope is not None:
        lesson.scope = payload.scope
    if payload.status is not None:
        lesson.status = payload.status

    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.post("/lessons/{lesson_id}/approve", response_model=LessonOut)
async def approve_lesson(
    lesson_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> Lesson:
    """Approves a suggested lesson, promoting it to active (FR-14.1)."""
    return await learning_engine.approve_lesson(db, lesson_id)


@router.post("/lessons/{lesson_id}/deactivate", response_model=LessonOut)
async def deactivate_lesson(
    lesson_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> Lesson:
    """Deactivates an active lesson ('active' -> 'inactive')."""
    return await learning_engine.deactivate_lesson(db, lesson_id)


@router.post("/lessons/{lesson_id}/activate", response_model=LessonOut)
async def activate_lesson(
    lesson_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> Lesson:
    """Reactivates an inactive lesson ('inactive' -> 'active')."""
    return await learning_engine.activate_lesson(db, lesson_id)


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["po", "admin"])),
) -> None:
    """Deletes a lesson from the system learning repository."""
    stmt = select(Lesson).where(Lesson.id == lesson_id)
    res = await db.execute(stmt)
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Pelajaran tidak ditemukan")
    await db.delete(lesson)
    await db.commit()


@router.get("/scorecards", response_model=list[ModelScorecardOut])
async def list_model_scorecards(
    profile_id: str | None = Query(None),
    role_name: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Returns model performance scorecards across roles and profiles (FR-14.4)."""
    stmt = select(ModelScorecard).order_by(ModelScorecard.item_count.desc())
    if profile_id:
        stmt = stmt.where(ModelScorecard.profile_id == profile_id)
    if role_name:
        stmt = stmt.where(ModelScorecard.role_name == role_name)

    res = await db.execute(stmt)
    cards = res.scalars().all()

    # Load model names
    model_ids = [c.model_id for c in cards if c.model_id]
    models_map = {}
    if model_ids:
        m_stmt = select(Model).where(Model.id.in_(model_ids))
        m_res = await db.execute(m_stmt)
        for m in m_res.scalars().all():
            models_map[m.id] = m.name

    result = []
    for c in cards:
        total = c.item_count or 1
        rate = round((c.accepted_count / total) * 100.0, 1)
        result.append({
            "id": c.id,
            "model_id": c.model_id,
            "model_name": models_map.get(c.model_id, "Default LLM"),
            "role_name": c.role_name,
            "profile_id": c.profile_id,
            "item_count": c.item_count,
            "accepted_count": c.accepted_count,
            "rejected_count": c.rejected_count,
            "success_rate": rate,
            "avg_revisions": round(c.avg_revisions, 2),
            "avg_cost": round(c.avg_cost, 4),
        })

    return result


@router.get("/calibration/{profile_id}", response_model=CalibrationFactorOut)
async def get_calibration(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Returns estimation calibration factor for a profile (FR-14.6)."""
    factor = await learning_engine.get_calibration_factor(db, profile_id)
    return {
        "profile_id": profile_id,
        "factor": factor,
        "status": "calibrated" if factor != 1.0 else "baseline",
    }
