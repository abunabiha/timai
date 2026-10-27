from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.db.models import Project, ProjectProfile, User
from app.db.session import get_db
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectProfileResponse,
    ProjectResponse,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/profiles", response_model=list[ProjectProfileResponse])
async def list_profiles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ProjectProfileResponse]:
    """Retrieve all available project profiles (accessible to Admin, PO, Viewer)."""
    result = await db.execute(select(ProjectProfile).order_by(ProjectProfile.name))
    profiles = result.scalars().all()
    return [ProjectProfileResponse.model_validate(p) for p in profiles]


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ProjectResponse]:
    """
    List projects based on user role:
    - Admin: can see all projects
    - PO: only sees own projects
    - Viewer: sees all projects (read-only)
    """
    if current_user.role == "admin" or current_user.role == "viewer":
        query = select(Project).order_by(Project.created_at.desc())
    else:  # role == "po"
        query = select(Project).where(Project.po_id == current_user.id).order_by(Project.created_at.desc())

    result = await db.execute(query)
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> ProjectResponse:
    """
    Create a new project.
    - Allowed for Admin and PO.
    - Viewer is rejected with 403 Forbidden.
    """
    # Verify profile exists
    profile_result = await db.execute(
        select(ProjectProfile).where(ProjectProfile.id == payload.profile_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project profile id: '{payload.profile_id}'",
        )

    project = Project(
        po_id=current_user.id,
        title=payload.title,
        profile_id=payload.profile_id,
        brief=payload.brief,
        profile_fields=payload.profile_fields,
        deadline=payload.deadline,
        budget=payload.budget,
        currency=payload.currency,
        language=payload.language,
        is_secret=payload.is_secret,
        status="brief",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProjectResponse:
    """
    Get project details with role verification:
    - Admin / Viewer can view
    - PO can only view own project
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if current_user.role == "po" and project.po_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this project",
        )

    return ProjectResponse.model_validate(project)
