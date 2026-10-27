import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user, require_role
from app.db.models import Attachment, Model, Project, ProjectProfile, User
from app.db.session import get_db
from app.orchestrator.composer import team_composer
from app.orchestrator.extractor import extract_text_from_file
from app.schemas.project import (
    ApproveTeamRequest,
    ApproveTeamResponse,
    AttachmentResponse,
    ClarificationAnswersRequest,
    ClarificationQuestion,
    ProjectCreateRequest,
    ProjectProfileResponse,
    ProjectResponse,
    RecalculateEstimateRequest,
    RecalculateEstimateResponse,
    TeamProposalResponse,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def verify_project_ownership(project: Project, user: User) -> None:
    if user.role == "po" and project.po_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this project",
        )


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
    """List projects accessible to current user."""
    if current_user.role in ("admin", "viewer"):
        query = select(Project).order_by(Project.created_at.desc())
    else:
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
    """Create a new project from intake brief."""
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
    """Get project details."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    verify_project_ownership(project, current_user)
    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    project_id: str,
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> AttachmentResponse:
    """Upload project attachment (PDF, DOCX, CSV, BibTeX, RIS) with text extraction and summary."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_ownership(project, current_user)

    content = await file.read()
    filename = file.filename or "uploaded_file"
    full_text, summary = extract_text_from_file(filename, content)

    # Save to disk
    upload_dir = os.path.join(os.getcwd(), "workspaces", "uploads", project_id)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    attachment = Attachment(
        project_id=project.id,
        filename=filename,
        file_path=file_path,
        summary=summary,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return AttachmentResponse.model_validate(attachment)


@router.get("/{project_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[AttachmentResponse]:
    """List attachments for a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_ownership(project, current_user)

    att_res = await db.execute(select(Attachment).where(Attachment.project_id == project_id))
    attachments = att_res.scalars().all()
    return [AttachmentResponse.model_validate(a) for a in attachments]


@router.post("/{project_id}/clarify", response_model=list[ClarificationQuestion])
async def get_clarification_questions(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> list[ClarificationQuestion]:
    """Analis generates up to 7 clarification questions based on brief."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_ownership(project, current_user)

    questions = await team_composer.generate_clarification_questions(db, project)
    project.status = "clarification"
    await db.commit()
    return [ClarificationQuestion(**q) for q in questions]


@router.post("/{project_id}/clarify/answers")
async def submit_clarification_answers(
    project_id: str,
    payload: ClarificationAnswersRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> dict[str, Any]:
    """Record PO answers and assumed default answers for skipped questions."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_ownership(project, current_user)

    notes = []
    for item in payload.answers:
        if item.is_skipped or not item.answer.strip():
            notes.append(f"- **Pertanyaan**: {item.question}\n  - *Asumsi*: Tidak dijawab oleh PO, diasumsikan standar/fleksibel.")
        else:
            notes.append(f"- **Pertanyaan**: {item.question}\n  - **Jawaban PO**: {item.answer.strip()}")

    clarification_text = "\n\n".join(notes)
    # Save into profile_fields for persistence
    if not project.profile_fields:
        project.profile_fields = {}
    project.profile_fields["clarification_notes"] = clarification_text
    project.status = "team_proposed"
    await db.commit()

    return {"status": "ok", "message": "Clarification notes saved successfully"}


@router.post("/{project_id}/compose-team", response_model=TeamProposalResponse)
async def compose_team_endpoint(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
    package: Annotated[str, Query()] = "balanced",
) -> TeamProposalResponse:
    """Team Composer generates tailored agent team proposal based on brief and profile."""
    result = await db.execute(
        select(Project).options(selectinload(Project.profile)).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_ownership(project, current_user)

    proposal = await team_composer.compose_team(db, project, package=package)
    return TeamProposalResponse(**proposal)


@router.post("/{project_id}/recalculate-estimate", response_model=RecalculateEstimateResponse)
async def recalculate_estimate(
    project_id: str,
    payload: RecalculateEstimateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecalculateEstimateResponse:
    """Recalculate cost and duration range dynamically when user adjusts tier or model in UI."""
    models_res = await db.execute(select(Model).where(Model.is_active.is_(True)))
    models = models_res.scalars().all()

    cost_range, duration_range = team_composer.calculate_estimates(
        [a.model_dump() for a in payload.agents],
        payload.size,
        models,
    )

    has_reviewer = any(a.is_reviewer for a in payload.agents)
    warnings = []
    if not has_reviewer:
        warnings.append("Peringatan: Tim tidak memiliki agen reviewer independen. Risiko kualitas tinggi.")

    # Check against budget
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if project and project.budget > 0 and cost_range["max_idr"] > project.budget:
        warnings.append(f"Peringatan: Estimasi biaya maksimum ({cost_range['max_idr']:,.0f} IDR) melampaui pagu anggaran ({project.budget:,.0f} IDR).")

    return RecalculateEstimateResponse(
        cost_range=cost_range,
        duration_range=duration_range,
        has_reviewer=has_reviewer,
        warnings=warnings,
    )


@router.post("/{project_id}/approve-team", response_model=ApproveTeamResponse)
async def approve_team_endpoint(
    project_id: str,
    payload: ApproveTeamRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "po"]))],
) -> ApproveTeamResponse:
    """PO approves team proposal (Gate G1), creating Agent records and initializing Git workspace."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_ownership(project, current_user)

    clarification_notes = payload.clarification_notes or (
        project.profile_fields.get("clarification_notes", "") if project.profile_fields else ""
    )

    res = await team_composer.approve_team_g1(
        db=db,
        project_id=project.id,
        user_id=current_user.id,
        team_config=[a.model_dump() for a in payload.agents],
        clarification_notes=clarification_notes,
    )

    return ApproveTeamResponse(**res)
