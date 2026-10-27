import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lesson, Model, Project, Provider, User
from app.orchestrator.learning import learning_engine


@pytest.mark.asyncio
async def test_lesson_lifecycle_and_auto_promotion(db_session: AsyncSession):
    """
    Verify Lesson lifecycle:
    - Initially suggested
    - Auto-promoted to active if it appears >= 2 times (FR-14.9)
    - Manual PO approval and deactivation
    """
    # 1. First occurrence: creates suggested lesson
    lesson1 = await learning_engine.extract_or_update_lesson(
        db=db_session,
        content="Gunakan format sitasi APA 7 untuk seluruh daftar pustaka",
        layer="preference",
        evidence="Koreksi PO di sprint review",
        preferred_scope="global",
    )
    assert lesson1.status == "suggested"
    assert lesson1.occurrence_count == 1

    # 2. Second occurrence with identical/similar content: auto-promoted to active!
    lesson2 = await learning_engine.extract_or_update_lesson(
        db=db_session,
        content="Gunakan format sitasi APA 7 untuk seluruh daftar pustaka",
        layer="preference",
        evidence="Koreksi PO berulang di sprint review",
        preferred_scope="global",
    )
    assert lesson2.id == lesson1.id
    assert lesson2.occurrence_count == 2
    assert lesson2.status == "active"

    # 3. Deactivate by PO
    deactivated = await learning_engine.deactivate_lesson(db_session, lesson1.id)
    assert deactivated.status == "inactive"

    # 4. Reactivate by PO
    reactivated = await learning_engine.activate_lesson(db_session, lesson1.id)
    assert reactivated.status == "active"


@pytest.mark.asyncio
async def test_lesson_prompt_injection_rules(db_session: AsyncSession):
    """
    Verify:
    - Suggested lessons DO NOT affect prompt
    - Active lessons DO affect prompt
    - Inactive lessons DO NOT affect prompt
    """
    base_prompt = "Instruksi dasar: Anda adalah Academic Writer."

    # Create suggested lesson
    sug_lesson = Lesson(
        layer="preference",
        scope="proposal",
        content="Hindari kalimat pembuka klise seperti 'Pada era globalisasi ini'",
        status="suggested",
        occurrence_count=1,
    )
    db_session.add(sug_lesson)
    await db_session.commit()

    # Injected prompt with only suggested lesson: NO CHANGE!
    prompt_sug = await learning_engine.inject_active_lessons(
        db=db_session,
        base_prompt=base_prompt,
        profile_id="proposal",
    )
    assert "Hindari kalimat pembuka klise" not in prompt_sug
    assert prompt_sug == base_prompt

    # Promote to active: MUST BE INJECTED!
    sug_lesson.status = "active"
    await db_session.commit()

    prompt_active = await learning_engine.inject_active_lessons(
        db=db_session,
        base_prompt=base_prompt,
        profile_id="proposal",
    )
    assert "Hindari kalimat pembuka klise" in prompt_active
    assert "### Aturan & Pelajaran yang Dipelajari Sistem" in prompt_active

    # Deactivate to inactive: MUST NOT BE INJECTED!
    sug_lesson.status = "inactive"
    await db_session.commit()

    prompt_inactive = await learning_engine.inject_active_lessons(
        db=db_session,
        base_prompt=base_prompt,
        profile_id="proposal",
    )
    assert "Hindari kalimat pembuka klise" not in prompt_inactive
    assert prompt_inactive == base_prompt


@pytest.mark.asyncio
async def test_secret_project_privacy_isolation(db_session: AsyncSession):
    """Verify lessons from secret projects are scoped strictly to project (FR-14.9)."""
    user = User(email=f"po_{uuid.uuid4().hex[:6]}@timai.local", name="PO Secret", role="po", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    secret_project = Project(
        po_id=user.id,
        title="Proyek Rahasia Pertahanan",
        brief="Pengembangan radar rahasia",
        profile_id="software",
        is_secret=True,
    )
    db_session.add(secret_project)
    await db_session.commit()
    await db_session.refresh(secret_project)

    # Extract lesson from secret project
    secret_lesson = await learning_engine.extract_or_update_lesson(
        db=db_session,
        content="Protokol enkripsi wajib menggunakan AES-256-GCM khusus",
        layer="preference",
        evidence="Arahan rahasia",
        project=secret_project,
        preferred_scope="global",  # Attempt global, but must be forced to project!
    )

    assert secret_lesson.scope == "project"
    assert secret_lesson.project_id == secret_project.id

    # Active lesson in secret project must NOT be injected into a different project!
    secret_lesson.status = "active"
    await db_session.commit()

    other_project_prompt = await learning_engine.inject_active_lessons(
        db=db_session,
        base_prompt="Instruksi umum",
        profile_id="software",
        project_id="other-project-id",
    )
    assert "Protokol enkripsi wajib" not in other_project_prompt

    # BUT MUST BE INJECTED into the secret project itself!
    secret_project_prompt = await learning_engine.inject_active_lessons(
        db=db_session,
        base_prompt="Instruksi umum",
        profile_id="software",
        project_id=secret_project.id,
    )
    assert "Protokol enkripsi wajib" in secret_project_prompt


@pytest.mark.asyncio
async def test_model_scorecard_and_scoring_formula(db_session: AsyncSession):
    """Verify ModelScorecard recording and PRD Section 10 Step 6 formula."""
    # Setup Provider & Model
    prov = Provider(name="Test Provider", provider_type="fake", is_active=True)
    db_session.add(prov)
    await db_session.flush()

    model = Model(
        provider_id=prov.id,
        name="Test Model High",
        model_identifier="test-model-high",
        tier="high",
        competency_score=4.5,
        input_price=5.0,
        output_price=10.0,
        is_active=True,
    )
    db_session.add(model)
    await db_session.commit()
    await db_session.refresh(model)

    # Initial score with no history (0.7*comp + 0.3*(1 - norm_cost))
    # comp = 4.5/5.0 = 0.9; price = 15.0; norm_cost = 15/30 = 0.5; cost_score = 0.5
    # score = 0.7*0.9 + 0.3*0.5 = 0.63 + 0.15 = 0.78
    initial_score = await learning_engine.calculate_model_score(
        db=db_session,
        model=model,
        role_id="grant_writer",
        profile_id="proposal",
    )
    assert initial_score == 0.78

    # Record 4 accepted PBIs and 1 rejected PBI (success rate = 4/5 = 0.8)
    for _ in range(4):
        await learning_engine.record_scorecard_entry(
            db=db_session,
            model_id=model.id,
            role_name="grant_writer",
            profile_id="proposal",
            is_accepted=True,
            revisions_count=0,
            cost=0.005,
        )
    await learning_engine.record_scorecard_entry(
        db=db_session,
        model_id=model.id,
        role_name="grant_writer",
        profile_id="proposal",
        is_accepted=False,
        revisions_count=1,
        cost=0.007,
    )

    # Score with history: 0.4*comp + 0.3*success_rate + 0.3*(1 - norm_cost)
    # score = 0.4*0.9 + 0.3*0.8 + 0.3*0.5 = 0.36 + 0.24 + 0.15 = 0.75
    calibrated_score = await learning_engine.calculate_model_score(
        db=db_session,
        model=model,
        role_id="grant_writer",
        profile_id="proposal",
    )
    assert calibrated_score == 0.75


@pytest.mark.asyncio
async def test_two_consecutive_projects_demo(db_session: AsyncSession):
    """
    CRITERIA DEMO:
    Two consecutive projects: PO correction in Project 1 appears as suggested,
    is approved by PO, and then visibly affects agent prompt in Project 2!
    """
    user = User(email=f"po_{uuid.uuid4().hex[:6]}@timai.local", name="PO Demo", role="po", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 1. Project 1 is created
    project1 = Project(
        po_id=user.id,
        title="Proyek Riset Pertama",
        brief="Penelitian skema dasar",
        profile_id="proposal",
        status="sprint",
    )
    db_session.add(project1)
    await db_session.commit()
    await db_session.refresh(project1)

    # PO makes correction in Project 1: "Sertakan nomor kontak penanggung jawab di lembar pengesahan"
    correction_text = "Sertakan nomor kontak penanggung jawab di lembar pengesahan proposal"
    lesson_p1 = await learning_engine.extract_or_update_lesson(
        db=db_session,
        content=correction_text,
        layer="preference",
        evidence=f"Koreksi PO di Proyek {project1.title}",
        project=project1,
        preferred_scope="profile",
    )

    # Verify lesson appears as suggested
    assert lesson_p1.status == "suggested"

    # Verify Project 2 before approval: prompt does NOT contain the lesson
    base_prompt = "Instruksi: Susun naskah proposal sesuai standar."
    prompt_p2_before = await learning_engine.inject_active_lessons(
        db=db_session,
        base_prompt=base_prompt,
        profile_id="proposal",
    )
    assert correction_text not in prompt_p2_before

    # 2. PO explicitly approves the lesson
    approved_lesson = await learning_engine.approve_lesson(db_session, lesson_p1.id)
    assert approved_lesson.status == "active"

    # 3. Project 2 is created
    project2 = Project(
        po_id=user.id,
        title="Proyek Riset Kedua",
        brief="Penelitian skema lanjutan",
        profile_id="proposal",
        status="brief",
    )
    db_session.add(project2)
    await db_session.commit()
    await db_session.refresh(project2)

    # Verify Project 2 prompt: the approved lesson IS visibly injected!
    prompt_p2_after = await learning_engine.inject_active_lessons(
        db=db_session,
        base_prompt=base_prompt,
        profile_id="proposal",
        project_id=project2.id,
    )
    assert correction_text in prompt_p2_after
    assert "### Aturan & Pelajaran yang Dipelajari Sistem" in prompt_p2_after
