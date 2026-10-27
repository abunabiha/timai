import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user, require_role
from app.db.models import Discussion, Project, User
from app.db.session import get_db
from app.orchestrator.meeting import meeting_engine, register_listener, unregister_listener
from app.schemas.discussion import (
    DiscussionCreateRequest,
    DiscussionDetailResponse,
)

router = APIRouter(prefix="/discussions", tags=["discussions"])


@router.post("", response_model=DiscussionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_discussion(
    payload: DiscussionCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> DiscussionDetailResponse:
    """Create a new discussion topic in draft status."""
    proj_res = await db.execute(select(Project).where(Project.id == payload.project_id))
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role == "po" and project.po_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden: you do not own this project")

    disc = await meeting_engine.create_discussion(
        db=db,
        project_id=payload.project_id,
        agenda=payload.agenda,
        discussion_type=payload.discussion_type,
        participant_agent_ids=payload.participants,
    )
    res_full = await db.execute(
        select(Discussion)
        .options(
            selectinload(Discussion.contributions),
            selectinload(Discussion.confirmations),
        )
        .where(Discussion.id == disc.id)
    )
    return DiscussionDetailResponse.model_validate(res_full.scalar_one())


@router.get("/{discussion_id}", response_model=DiscussionDetailResponse)
async def get_discussion(
    discussion_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DiscussionDetailResponse:
    """Get discussion details, contributions, and confirmation state."""
    res = await db.execute(
        select(Discussion)
        .options(
            selectinload(Discussion.contributions),
            selectinload(Discussion.confirmations),
        )
        .where(Discussion.id == discussion_id)
    )
    disc = res.scalar_one_or_none()
    if not disc:
        raise HTTPException(status_code=404, detail="Discussion not found")

    return DiscussionDetailResponse.model_validate(disc)


@router.post("/{discussion_id}/start", response_model=DiscussionDetailResponse)
async def start_discussion_round(
    discussion_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> DiscussionDetailResponse:
    """Run one single round of discussion with all participants."""
    res = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    disc = res.scalar_one_or_none()
    if not disc:
        raise HTTPException(status_code=404, detail="Discussion not found")

    await meeting_engine.run_round(db, discussion_id)

    # Refresh full attributes
    res_full = await db.execute(
        select(Discussion)
        .options(
            selectinload(Discussion.contributions),
            selectinload(Discussion.confirmations),
        )
        .where(Discussion.id == discussion_id)
    )
    return DiscussionDetailResponse.model_validate(res_full.scalar_one())


@router.get("/{discussion_id}/events")
async def stream_discussion_events(
    discussion_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """SSE endpoint for live real-time contribution and synthesis streaming."""
    queue = register_listener(discussion_id)

    async def event_generator():
        try:
            # Initial ping
            yield f"data: {json.dumps({'event': 'connected', 'discussion_id': discussion_id})}\n\n"
            while True:
                # Wait for next event
                event_data = await queue.get()
                yield f"data: {json.dumps(event_data)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unregister_listener(discussion_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
