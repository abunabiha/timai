import logging
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Lesson, Model, ModelScorecard, Project, UsageRecord

logger = logging.getLogger("timai.learning")


class LearningEngine:
    """
    Learning Engine Core (FR-14 & PRD 10.6):
    - System-level continuous learning (Prinsip Kejujuran)
    - PO Preference memory & lesson extraction
    - Lifecycle: suggested -> active -> inactive
    - Auto-promotion if lesson appears >= 2 times (FR-14.9)
    - Active lesson prompt injection with scope boundaries
    - ModelScorecard recording & Team Composer scoring
    - Estimation calibration
    """

    async def extract_or_update_lesson(
        self,
        db: AsyncSession,
        content: str,
        layer: str,  # preference, retro, role
        evidence: str,
        project: Project | None = None,
        preferred_scope: str = "global",
    ) -> Lesson:
        """
        Extracts a lesson from PO feedback or retro.
        If a similar lesson exists:
          - Increments occurrence_count
          - If occurrence_count >= 2 and status == 'suggested', automatically promotes to 'active'! (FR-14.9)
        If project is marked secret:
          - Scope is locked to 'project' (Privacy protection).
        """
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("Konten pelajaran tidak boleh kosong.")

        is_secret = project.is_secret if project else False
        if is_secret:
            scope = "project"
        elif preferred_scope in ("profile", "per_profil") and project and project.profile_id:
            scope = project.profile_id
        else:
            scope = preferred_scope
        project_id = project.id if project else None

        # Search for existing similar lesson
        # Keyword match
        words = [w for w in re.findall(r"\w+", clean_content.lower()) if len(w) > 4]
        stmt = select(Lesson).where(Lesson.layer == layer)
        if is_secret and project_id:
            stmt = stmt.where(Lesson.project_id == project_id)

        res = await db.execute(stmt)
        all_lessons = res.scalars().all()

        matched_lesson: Lesson | None = None
        for l in all_lessons:
            # Check exact match or high keyword overlap
            l_words = set(re.findall(r"\w+", l.content.lower()))
            if l.content.strip().lower() == clean_content.lower():
                matched_lesson = l
                break
            if words:
                overlap = sum(1 for w in words if w in l_words)
                if overlap >= max(2, len(words) * 0.7):
                    matched_lesson = l
                    break

        if matched_lesson:
            matched_lesson.occurrence_count += 1
            matched_lesson.updated_at = datetime.now(timezone.utc)
            # Auto-promote if appeared >= 2 times per FR-14.9
            if matched_lesson.status == "suggested" and matched_lesson.occurrence_count >= 2:
                matched_lesson.status = "active"
                logger.info("Lesson '%s' auto-promoted to active (occurrence >= 2).", matched_lesson.id)
            await db.commit()
            return matched_lesson

        # Create new suggested lesson
        new_lesson = Lesson(
            layer=layer,
            scope=scope,
            content=clean_content,
            evidence=evidence,
            status="suggested",
            occurrence_count=1,
            project_id=project_id,
        )
        db.add(new_lesson)
        await db.commit()
        await db.refresh(new_lesson)
        logger.info("New suggested lesson recorded: %s", new_lesson.id)
        return new_lesson

    async def approve_lesson(self, db: AsyncSession, lesson_id: str) -> Lesson:
        """PO explicitly approves a lesson ('suggested' -> 'active')."""
        stmt = select(Lesson).where(Lesson.id == lesson_id)
        res = await db.execute(stmt)
        lesson = res.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Pelajaran tidak ditemukan")
        lesson.status = "active"
        lesson.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return lesson

    async def deactivate_lesson(self, db: AsyncSession, lesson_id: str) -> Lesson:
        """PO deactivates a lesson ('active' -> 'inactive')."""
        stmt = select(Lesson).where(Lesson.id == lesson_id)
        res = await db.execute(stmt)
        lesson = res.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Pelajaran tidak ditemukan")
        lesson.status = "inactive"
        lesson.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return lesson

    async def activate_lesson(self, db: AsyncSession, lesson_id: str) -> Lesson:
        """PO reactivates an inactive lesson ('inactive' -> 'active')."""
        stmt = select(Lesson).where(Lesson.id == lesson_id)
        res = await db.execute(stmt)
        lesson = res.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Pelajaran tidak ditemukan")
        lesson.status = "active"
        lesson.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return lesson

    async def get_active_lessons_for_agent(
        self,
        db: AsyncSession,
        profile_id: str,
        project_id: str | None = None,
        max_lessons: int = 10,
    ) -> list[Lesson]:
        """
        Retrieves active lessons applicable to this agent context.
        Applies scope hierarchy: global, profile, and project.
        Excludes suggested and inactive lessons.
        """
        scopes = ["global", "profile", profile_id]
        if project_id:
            scopes.append("project")

        stmt = select(Lesson).where(
            Lesson.status == "active",
            or_(
                Lesson.scope.in_(["global", "profile", profile_id]),
                (Lesson.scope == "project") & (Lesson.project_id == project_id),
            ),
        ).order_by(Lesson.occurrence_count.desc(), Lesson.updated_at.desc()).limit(max_lessons)

        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def inject_active_lessons(
        self,
        db: AsyncSession,
        base_prompt: str,
        profile_id: str,
        project_id: str | None = None,
    ) -> str:
        """
        Injects active lessons into an agent prompt.
        If no active lessons exist, returns base_prompt unmodified.
        Suggested and inactive lessons are NEVER injected.
        """
        active_lessons = await self.get_active_lessons_for_agent(
            db=db,
            profile_id=profile_id,
            project_id=project_id,
        )

        if not active_lessons:
            return base_prompt

        lines = ["\n\n### Aturan & Pelajaran yang Dipelajari Sistem (Preferensi PO Aktif):"]
        for l in active_lessons:
            lines.append(f"- [Aturan]: {l.content}")

        return base_prompt + "\n".join(lines)

    # --- Model Scorecard (FR-14.4 & PRD 10.6) ---

    async def record_scorecard_entry(
        self,
        db: AsyncSession,
        model_id: str | None,
        role_name: str,
        profile_id: str,
        is_accepted: bool,
        revisions_count: int = 0,
        cost: float = 0.0,
    ) -> ModelScorecard:
        """
        Records completion outcome in ModelScorecard per PBI.
        Updates item_count, accepted_count, rejected_count, avg_revisions, avg_cost.
        """
        stmt = select(ModelScorecard).where(
            ModelScorecard.model_id == model_id,
            ModelScorecard.role_name == role_name,
            ModelScorecard.profile_id == profile_id,
        )
        res = await db.execute(stmt)
        scorecard = res.scalar_one_or_none()

        if not scorecard:
            scorecard = ModelScorecard(
                model_id=model_id,
                role_name=role_name,
                profile_id=profile_id,
                item_count=1,
                accepted_count=1 if is_accepted else 0,
                rejected_count=0 if is_accepted else 1,
                avg_revisions=float(revisions_count),
                avg_cost=float(cost),
            )
            db.add(scorecard)
        else:
            prev_items = scorecard.item_count
            new_items = prev_items + 1
            scorecard.item_count = new_items
            if is_accepted:
                scorecard.accepted_count += 1
            else:
                scorecard.rejected_count += 1

            scorecard.avg_revisions = (scorecard.avg_revisions * prev_items + revisions_count) / new_items
            scorecard.avg_cost = (scorecard.avg_cost * prev_items + cost) / new_items
            scorecard.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(scorecard)
        return scorecard

    async def calculate_model_score(
        self,
        db: AsyncSession,
        model: Model,
        role_id: str,
        profile_id: str,
    ) -> float:
        """
        Calculates model score using PRD Section 10 Step 6 formula:
        0.4 * competency_match + 0.3 * role_scorecard_rate + 0.3 * (1 - normalized_cost)
        If no history, weight transfers to competency:
        0.7 * competency_match + 0.3 * (1 - normalized_cost)
        """
        competency_match = min(1.0, max(0.0, (model.competency_score or 3.0) / 5.0))

        # Normalized cost (0.0 = free/cheap, 1.0 = expensive)
        # Cap price at $30/1M tokens
        price = (model.input_price or 0.0) + (model.output_price or 0.0)
        norm_cost = min(1.0, max(0.0, price / 30.0))
        cost_score = 1.0 - norm_cost

        # Inspect scorecard
        stmt = select(ModelScorecard).where(
            ModelScorecard.model_id == model.id,
            ModelScorecard.role_name == role_id,
            ModelScorecard.profile_id == profile_id,
        )
        res = await db.execute(stmt)
        scorecard = res.scalar_one_or_none()

        if scorecard and scorecard.item_count > 0:
            success_rate = scorecard.accepted_count / scorecard.item_count
            score = 0.4 * competency_match + 0.3 * success_rate + 0.3 * cost_score
        else:
            # No history: weight shifts to competency match per PRD 10.6
            score = 0.7 * competency_match + 0.3 * cost_score

        return round(score, 4)

    # --- Estimation Calibration (FR-14.6) ---

    async def get_calibration_factor(self, db: AsyncSession, profile_id: str) -> float:
        """
        Computes calibration ratio = actual_avg_cost / estimated_baseline.
        Returns multiplier (default 1.0) to correct subsequent estimates.
        """
        # Average cost across scorecards for this profile
        stmt = (
            select(func.coalesce(func.avg(ModelScorecard.avg_cost), 0.0))
            .where(ModelScorecard.profile_id == profile_id, ModelScorecard.item_count > 0)
        )
        res = await db.execute(stmt)
        avg_cost = float(res.scalar() or 0.0)
        if avg_cost > 0:
            # Baseline item cost is ~$0.005
            ratio = avg_cost / 0.005
            return round(min(2.5, max(0.5, ratio)), 2)
        return 1.0


learning_engine = LearningEngine()
