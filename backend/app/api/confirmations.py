from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user, require_role
from app.db.models import Confirmation, Decision, Discussion, User
from app.db.session import get_db
from app.orchestrator.meeting import meeting_engine
from app.schemas.discussion import (
    BatchDecisionRequest,
    ConfirmationResponse,
    DecisionActionRequest,
    DecisionResponse,
)

router = APIRouter(prefix="/confirmations", tags=["confirmations"])


@router.get("", response_model=list[ConfirmationResponse])
async def list_pending_confirmations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> list[ConfirmationResponse]:
    """
    List all pending confirmations waiting for PO action (Kotak Konfirmasi).
    - PO only sees confirmations for their own projects.
    - Admin sees all.
    """
    query = (
        select(Confirmation)
        .options(selectinload(Confirmation.discussion).selectinload(Discussion.project))
        .where(Confirmation.decided_at.is_(None))
        .order_by(Confirmation.created_at.desc())
    )
    result = await db.execute(query)
    confirmations = result.scalars().all()

    if current_user.role == "po":
        confirmations = [
            c for c in confirmations if c.discussion and c.discussion.project and c.discussion.project.po_id == current_user.id
        ]

    return [ConfirmationResponse.model_validate(c) for c in confirmations]


@router.post("/{confirmation_id}/decide")
async def decide_confirmation(
    confirmation_id: str,
    payload: DecisionActionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> dict[str, Any]:
    """PO submits decision for a Confirmation Point."""
    try:
        res = await meeting_engine.handle_po_confirmation(
            db=db,
            confirmation_id=confirmation_id,
            user_id=current_user.id,
            action=payload.action,
            selected_option=payload.selected_option,
            po_notes=payload.po_notes,
        )
        return res
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/batch-decide")
async def batch_decide_confirmations(
    payload: BatchDecisionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> dict[str, Any]:
    """Batch decide multiple confirmation points simultaneously (FR-6.9)."""
    results = []
    for item in payload.decisions:
        try:
            res = await meeting_engine.handle_po_confirmation(
                db=db,
                confirmation_id=item.confirmation_id,
                user_id=current_user.id,
                action=item.action,
                selected_option=item.selected_option,
                po_notes=item.po_notes,
            )
            results.append({"confirmation_id": item.confirmation_id, "status": "success", "detail": res})
        except Exception as exc:
            results.append({"confirmation_id": item.confirmation_id, "status": "error", "error": str(exc)})

    return {"processed_count": len(results), "results": results}


@router.get("/projects/{project_id}/decisions", response_model=list[DecisionResponse])
async def get_project_decisions(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[DecisionResponse]:
    """Retrieve full decision log for a project."""
    res = await db.execute(
        select(Decision).where(Decision.project_id == project_id).order_by(Decision.created_at.asc())
    )
    decisions = res.scalars().all()
    return [DecisionResponse.model_validate(d) for d in decisions]
