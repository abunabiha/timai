"""Inception API endpoints: Agendas, Document Assembly, Backlog, G2 Review, and Export."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user
from app.db.models import (
    Artifact,
    BacklogItem,
    Discussion,
    Epic,
    Gate,
    ProductGoal,
    Project,
    User,
)
from app.db.session import get_db
from app.orchestrator.exporter import export_markdown_to_docx, export_markdown_to_pdf
from app.orchestrator.inception import (
    assemble_inception_document,
    get_project_workspace_path,
    init_inception_agendas,
    reorder_backlog_items,
    review_gate_g2,
)
from app.orchestrator.inception_agendas import get_agendas_for_profile
from app.schemas.inception import (
    AssembleInceptionResponse,
    BacklogItemSchema,
    EpicWithItemsSchema,
    GateG2DecisionRequest,
    GateG2DecisionResponse,
    InceptionAgendaItem,
    InceptionDocumentResponse,
    InceptionStatusResponse,
    ReorderBacklogRequest,
)

router = APIRouter(prefix="/inceptions", tags=["Inception"])


@router.get("/projects/{project_id}/status", response_model=InceptionStatusResponse)
async def get_inception_status(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.discussions).selectinload(Discussion.confirmations),
        )
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    profile_code = project.profile_id or "proposal"
    agenda_templates = get_agendas_for_profile(profile_code)

    disc_by_agenda: dict[str, Discussion] = {
        d.agenda: d for d in project.discussions if d.discussion_type == "inception"
    }

    agenda_items = []
    completed_count = 0
    for tpl in agenda_templates:
        key = f"Agenda {tpl['agenda_number']}: {tpl['title']}"
        disc = disc_by_agenda.get(key)
        is_completed = False
        selected_option = None
        disc_id = None
        if disc:
            disc_id = disc.id
            if disc.confirmations:
                latest_conf = disc.confirmations[-1]
                if latest_conf.selected_option:
                    is_completed = True
                    selected_option = latest_conf.selected_option
                    completed_count += 1

        agenda_items.append(
            InceptionAgendaItem(
                agenda_number=tpl["agenda_number"],
                title=tpl["title"],
                description=tpl["description"],
                lead_role=tpl["lead_role"],
                expected_output=tpl["expected_output"],
                discussion_id=disc_id,
                is_completed=is_completed,
                selected_option=selected_option,
            )
        )

    # Check G2 gate status
    gate_stmt = select(Gate).where(Gate.project_id == project_id, Gate.gate_type == "G2")
    g_res = await db.execute(gate_stmt)
    gate = g_res.scalar_one_or_none()
    g2_status = gate.decision if gate else None

    # Check if artifact exists
    art_stmt = select(Artifact).where(Artifact.project_id == project_id, Artifact.artifact_type == "dokumen_inception")
    art_res = await db.execute(art_stmt)
    has_assembled = art_res.scalar_one_or_none() is not None

    return InceptionStatusResponse(
        project_id=project.id,
        profile_id=profile_code,
        agendas=agenda_items,
        is_ready_for_assembly=(completed_count == len(agenda_templates) and completed_count > 0),
        has_assembled=has_assembled,
        gate_g2_status=g2_status,
    )


@router.post("/projects/{project_id}/init")
async def initialize_agendas(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    discussions = await init_inception_agendas(project, db)
    return {"message": f"{len(discussions)} agenda Inception disiapkan", "count": len(discussions)}


@router.post("/projects/{project_id}/assemble", response_model=AssembleInceptionResponse)
async def assemble_inception(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await assemble_inception_document(project_id, db, current_user)
    return AssembleInceptionResponse(
        artifact_id=result["artifact_id"],
        version=result["version"],
        product_goal=result["product_goal"],
        backlog_count=result["backlog_count"],
        files_generated=result["files_generated"],
    )


@router.get("/projects/{project_id}/document", response_model=InceptionDocumentResponse)
async def get_inception_document(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    workspace_path = get_project_workspace_path(project)
    doc_path = workspace_path / "02-inception" / "dokumen-inception.md"

    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Dokumen Inception belum dirakit. Silakan rakit dokumen terlebih dahulu.")

    content = doc_path.read_text(encoding="utf-8")

    # Get G2 Gate status
    gate_stmt = select(Gate).where(Gate.project_id == project_id, Gate.gate_type == "G2")
    g_res = await db.execute(gate_stmt)
    gate = g_res.scalar_one_or_none()
    gate_dict = None
    if gate:
        gate_dict = {
            "decision": gate.decision,
            "comments": gate.comments,
            "decided_at": gate.decided_at.isoformat() if gate.decided_at else None,
        }

    pg_stmt = select(ProductGoal).where(ProductGoal.project_id == project_id)
    pg_res = await db.execute(pg_stmt)
    pg = pg_res.scalar_one_or_none()
    product_goal_str = pg.statement if pg else ""

    # Parse version from artifact or content
    version = 1
    status_str = "menunggu PO"
    if "versi: " in content:
        try:
            version = int(content.split("versi: ")[1].split("\n")[0].strip())
        except Exception:
            pass
    if "status: " in content:
        try:
            status_str = content.split("status: ")[1].split("\n")[0].strip()
        except Exception:
            pass

    return InceptionDocumentResponse(
        version=version,
        content=content,
        status=status_str,
        product_goal=product_goal_str,
        gate_g2=gate_dict,
    )


@router.post("/projects/{project_id}/g2", response_model=GateG2DecisionResponse)
async def decide_gate_g2(
    project_id: str,
    req: GateG2DecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await review_gate_g2(
        project_id=project_id,
        decision=req.decision,
        comments=req.comments,
        current_user=current_user,
        db=db,
    )
    return GateG2DecisionResponse(**result)


@router.get("/projects/{project_id}/backlog", response_model=list[EpicWithItemsSchema])
async def get_project_backlog(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch epics and backlog items
    epics_stmt = (
        select(Epic)
        .where(Epic.project_id == project_id)
        .order_by(Epic.sort_order.asc())
    )
    ep_res = await db.execute(epics_stmt)
    epics = list(ep_res.scalars().all())

    items_stmt = (
        select(BacklogItem)
        .where(BacklogItem.project_id == project_id)
        .order_by(BacklogItem.po_sort_order.asc())
    )
    it_res = await db.execute(items_stmt)
    all_items = list(it_res.scalars().all())

    items_by_epic: dict[str, list[BacklogItem]] = {}
    for item in all_items:
        key = item.epic_id or "unassigned"
        items_by_epic.setdefault(key, []).append(item)

    result = []
    for ep in epics:
        ep_items = items_by_epic.get(ep.id, [])
        result.append(
            EpicWithItemsSchema(
                id=ep.id,
                title=ep.title,
                sort_order=ep.sort_order,
                items=[BacklogItemSchema.model_validate(it) for it in ep_items],
            )
        )
    return result


@router.post("/projects/{project_id}/backlog/reorder", response_model=list[BacklogItemSchema])
async def reorder_backlog(
    project_id: str,
    req: ReorderBacklogRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Security Rule: Only PO or Admin can reorder (FR-7.4 & PRD 5.1)
    if current_user.role not in ["po", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya Product Owner (PO) yang berhak mengubah urutan Product Backlog.",
        )

    updated_items = await reorder_backlog_items(
        project_id=project_id,
        ordered_item_ids=req.ordered_item_ids,
        current_user=current_user,
        db=db,
    )
    return [BacklogItemSchema.model_validate(it) for it in updated_items]


@router.get("/projects/{project_id}/export/docx")
async def export_inception_docx(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    workspace_path = get_project_workspace_path(project)
    doc_path = workspace_path / "02-inception" / "dokumen-inception.md"
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Dokumen Inception belum dirakit")

    content = doc_path.read_text(encoding="utf-8")
    export_dir = workspace_path / "02-inception" / "export"
    export_dir.mkdir(parents=True, exist_ok=True)
    slug_val = workspace_path.name
    docx_file = export_dir / f"dokumen-inception-{slug_val}.docx"

    export_markdown_to_docx(content, str(docx_file), title=f"Dokumen Inception - {project.title}")

    return FileResponse(
        path=str(docx_file),
        filename=f"dokumen-inception-{slug_val}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/projects/{project_id}/export/pdf")
async def export_inception_pdf(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    workspace_path = get_project_workspace_path(project)
    doc_path = workspace_path / "02-inception" / "dokumen-inception.md"
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Dokumen Inception belum dirakit")

    content = doc_path.read_text(encoding="utf-8")
    export_dir = workspace_path / "02-inception" / "export"
    export_dir.mkdir(parents=True, exist_ok=True)
    slug_val = workspace_path.name
    pdf_file = export_dir / f"dokumen-inception-{slug_val}.pdf"

    export_markdown_to_pdf(content, str(pdf_file), title=f"Dokumen Inception - {project.title}")

    return FileResponse(
        path=str(pdf_file),
        filename=f"dokumen-inception-{slug_val}.pdf",
        media_type="application/pdf",
    )
