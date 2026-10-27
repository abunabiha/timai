from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models import RoleTemplate, User
from app.db.session import get_db
from app.orchestrator.role_catalog import seed_role_templates_if_needed
from app.schemas.project import RoleTemplateResponse

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleTemplateResponse])
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[RoleTemplateResponse]:
    """List all available role templates in the system catalog."""
    await seed_role_templates_if_needed(db)
    result = await db.execute(select(RoleTemplate).order_by(RoleTemplate.name.asc()))
    roles = result.scalars().all()
    return [RoleTemplateResponse.model_validate(r) for r in roles]


@router.get("/{role_id}", response_model=RoleTemplateResponse)
async def get_role(
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RoleTemplateResponse:
    """Get details of a specific role template."""
    result = await db.execute(select(RoleTemplate).where(RoleTemplate.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role template not found")
    return RoleTemplateResponse.model_validate(role)
