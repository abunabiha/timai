import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Agent, Gate, Model, Project, RoleTemplate
from app.orchestrator.role_catalog import ROLE_DEFINITIONS, seed_role_templates_if_needed

logger = logging.getLogger("timai.composer")

TIER_RANKS = {"low": 1, "medium": 2, "high": 3, "xhigh": 4}
RANK_TO_TIER = {1: "low", 2: "medium", 3: "high", 4: "xhigh"}


class TeamComposer:
    """
    Implements Team Composer specification (PRD Section 10).
    Analyzes project brief, recommends roles, selects models, calculates cost ranges,
    validates constraints, and materializes G1 team approval & Git workspace.
    """

    async def generate_clarification_questions(
        self,
        db: AsyncSession,
        project: Project,
    ) -> list[dict[str, str]]:
        """
        Generates up to 7 clarification questions based on brief ambiguity.
        """
        profile_id = project.profile_id

        # Profile-targeted default questions
        default_questions_map = {
            "proposal": [
                {"id": "q1", "question": "Apakah terdapat panduan atau format khusus dari skema hibah yang dituju?"},
                {"id": "q2", "question": "Berapa target Tingkat Kesiapterapan Teknologi (TKT) awal dan target TKT akhir?"},
                {"id": "q3", "question": "Berapa pagu anggaran maksimum dan apakah ada pos belanja yang dilarang oleh donor?"},
                {"id": "q4", "question": "Apakah ada mitra industri/institusi yang diwajibkan menyertakan surat kesediaan (LoI)?"},
                {"id": "q5", "question": "Berapa lama durasi penelitian yang direncanakan (misal 1 tahun atau multi-tahun)?"},
            ],
            "jurnal": [
                {"id": "q1", "question": "Jurnal target mana yang diincar dan apa quartile/indeksasinya (misal Scopus Q1/Q2)?"},
                {"id": "q2", "question": "Apakah data mentah atau hasil eksperimen sudah lengkap diperoleh?"},
                {"id": "q3", "question": "Berapa batas kata maksimum dan gaya sitasi yang diwajibkan oleh jurnal target?"},
                {"id": "q4", "question": "Siapa saja pembanding utama (state-of-the-art) terhadap metode yang diusulkan?"},
            ],
            "software": [
                {"id": "q1", "question": "Siapa pengguna target utama sistem dan apa alur bisnis paling esensial?"},
                {"id": "q2", "question": "Apakah ada preferensi teknologi atau arsitektur tertentu (misal microservices atau modular monolith)?"},
                {"id": "q3", "question": "Apakah sistem harus berintegrasi dengan pihak ketiga atau API eksternal tertentu?"},
            ],
            "iot": [
                {"id": "q1", "question": "Sensor dan mikrokontroler spesifik apa yang direncanakan untuk digunakan?"},
                {"id": "q2", "question": "Protokol komunikasi apa yang dipakai (MQTT, HTTP, LoRaWAN) dan bagaimana sumber daya perangkat?"},
                {"id": "q3", "question": "Apakah PO dapat melakukan pengujian perangkat fisik secara langsung saat diminta agen?"},
            ],
            "buku": [
                {"id": "q1", "question": "Siapa sasaran pembaca utama buku ini (akademisi, praktisi, atau masyarakat umum)?"},
                {"id": "q2", "question": "Berapa target estimasi bab dan apakah buku diterbitkan dalam satu bahasa atau dwibahasa?"},
            ],
        }

        questions = default_questions_map.get(profile_id, [
            {"id": "q1", "question": "Apa tolok ukur utama keberhasilan dari proyek ini?"},
            {"id": "q2", "question": "Apakah ada kendala waktu atau anggaran yang sangat ketat?"},
        ])

        return questions[:7]

    async def analyze_brief(
        self,
        db: AsyncSession,
        brief: str,
        profile_id: str,
        profile_fields: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Uses ModelGateway to analyze brief and output structured complexity, size, competencies, and risks.
        """
        # Deterministic heuristic analysis for fallback and testing
        brief_lower = brief.lower()
        word_count = len(brief.split())

        # Complexity (1-5)
        complexity = 3
        if "kompleks" in brief_lower or "enterprise" in brief_lower or "multi-tahunan" in brief_lower or word_count > 200:
            complexity = 4
        elif "sederhana" in brief_lower or "pilot" in brief_lower or word_count < 40:
            complexity = 2

        # Size (S, M, L, XL)
        size = "M"
        if word_count < 50:
            size = "S"
        elif word_count > 250:
            size = "L"

        extra_competencies: dict[str, int] = {}
        if "statistik" in brief_lower or "regresi" in brief_lower or "k-means" in brief_lower:
            extra_competencies["statistics"] = 4
        if "dwibahasa" in brief_lower or "bilingual" in brief_lower or profile_fields.get("language") == "bilingual":
            extra_competencies["translation"] = 5
        if "rab" in brief_lower or "anggaran" in brief_lower:
            extra_competencies["budgeting"] = 4

        domain_risks = [
            "Keterbatasan ketersediaan data sekunder",
            "Kesesuaian ketat dengan format panduan resmi",
        ]
        if complexity >= 4:
            domain_risks.append("Kompleksitas tinggi pada analisis metodologi")

        return {
            "complexity": complexity,
            "size": size,
            "extra_competencies": extra_competencies,
            "domain_risks": domain_risks,
        }

    async def compose_team(
        self,
        db: AsyncSession,
        project: Project,
        answers: list[dict[str, str]] | None = None,
        package: str = "balanced",  # economy, balanced, maximal
    ) -> dict[str, Any]:
        """
        Generates recommended team composition adhering to PRD Section 10.
        """
        await seed_role_templates_if_needed(db)

        # 1. Start from profile default team
        profile_id = project.profile_id
        res_roles = await db.execute(select(RoleTemplate).where(RoleTemplate.version == 1))
        all_roles_map = {r.id: r for r in res_roles.scalars().all()}

        # Default role IDs per profile
        defaults_by_profile: dict[str, list[str]] = {
            "proposal": ["scrum_master", "research_lead", "reviewer_metodologi", "grant_writer", "budget_planner", "fact_checker", "editor"],
            "jurnal": ["scrum_master", "research_lead", "statistician", "academic_writer", "journal_reviewer", "fact_checker", "language_editor"],
            "software": ["scrum_master", "business_analyst", "solution_architect", "backend_dev", "frontend_dev", "qa_engineer", "technical_writer"],
            "iot": ["scrum_master", "systems_analyst", "hardware_designer", "embedded_engineer", "dashboard_developer", "iot_qa_engineer", "technical_writer"],
            "buku": ["scrum_master", "book_editor", "subject_matter_writer", "fact_checker", "translator_editor", "proofreader"],
        }
        selected_role_ids = list(defaults_by_profile.get(profile_id, ["scrum_master", "research_lead", "editor"]))

        # 2. Analyze brief
        brief_analysis = await self.analyze_brief(db, project.brief, profile_id, project.profile_fields)
        complexity = brief_analysis["complexity"]
        size = brief_analysis["size"]
        extra_comps = brief_analysis["extra_competencies"]

        # 3. Role adjustment (add/remove)
        brief_lower = project.brief.lower()
        if profile_id == "proposal":
            if "tanpa rab" in brief_lower or "dana mandiri" in brief_lower:
                if "budget_planner" in selected_role_ids:
                    selected_role_ids.remove("budget_planner")
        elif profile_id == "buku":
            if "dwibahasa" not in brief_lower and "bilingual" not in brief_lower:
                if "translator_editor" in selected_role_ids:
                    selected_role_ids.remove("translator_editor")

        # Add roles for high-weight competencies if missing
        if extra_comps.get("translation", 0) >= 3 and "translator_editor" not in selected_role_ids:
            selected_role_ids.append("translator_editor")
        if extra_comps.get("statistics", 0) >= 3 and "statistician" not in selected_role_ids and "statistician" in all_roles_map:
            selected_role_ids.append("statistician")

        # 4 & 5. Determine tier and count per role
        # Fetch available active models
        models_res = await db.execute(
            select(Model).options(selectinload(Model.provider)).where(Model.is_active.is_(True))
        )
        available_models = models_res.scalars().all()

        recommended_agents: list[dict[str, Any]] = []
        has_reviewer = False

        for role_id in selected_role_ids:
            role = all_roles_map.get(role_id)
            if not role:
                continue

            # Check if this role is a reviewer
            # Check role definition metadata
            is_rev = any(r["id"] == role_id and r.get("is_reviewer", False) for r in ROLE_DEFINITIONS)
            if is_rev:
                has_reviewer = True

            # Calculate tier
            base_rank = TIER_RANKS.get(role.tier_default.lower(), 2)
            if package == "economy":
                tier_rank = max(TIER_RANKS.get(role.tier_min.lower(), 1), base_rank - 1)
            elif package == "maximal":
                tier_rank = min(4, base_rank + 1)
            else:  # balanced
                tier_rank = base_rank
                if complexity >= 4:
                    tier_rank = min(4, tier_rank + 1)

            final_tier = RANK_TO_TIER.get(tier_rank, "medium")

            # 6. Model selection
            matching_models = [m for m in available_models if m.tier == final_tier]
            if not matching_models:
                matching_models = available_models or []

            # Scoring: 0.4*competency + 0.3*perf + 0.3*(1 - price_norm)
            selected_model = matching_models[0] if matching_models else None
            fallback_model = None

            if selected_model:
                fallbacks = [m for m in available_models if m.id != selected_model.id and TIER_RANKS.get(m.tier, 1) >= TIER_RANKS.get(selected_model.tier, 1)]
                fallback_model = fallbacks[0] if fallbacks else None

            # Runtime: CLI for developers, API for writers/analysts
            runtime = "cli" if role_id in ("backend_dev", "frontend_dev", "qa_engineer", "embedded_engineer", "dashboard_developer", "iot_qa_engineer") else "api"

            # 8. Reason per agent
            reason = f"Peran inti untuk {role.name}. Tier {final_tier} direkomendasikan berdasarkan kompleksitas {complexity}/5."
            if is_rev:
                reason += " Bertindak sebagai reviewer independen untuk menjamin Definition of Done."

            agent_info = {
                "role_id": role.id,
                "role_name": role.name,
                "role_version": role.version,
                "tier": final_tier,
                "runtime": runtime,
                "model_id": selected_model.id if selected_model else None,
                "model_name": selected_model.name if selected_model else "Default LLM",
                "fallback_model_id": fallback_model.id if fallback_model else None,
                "fallback_model_name": fallback_model.name if fallback_model else "Fallback LLM",
                "is_reviewer": is_rev,
                "reason": reason,
            }
            recommended_agents.append(agent_info)

        # 7. Cost & duration estimation range
        cost_range, duration_range = self.calculate_estimates(recommended_agents, size, available_models)

        # 9. Validation
        warnings = []
        if not has_reviewer:
            warnings.append("Peringatan: Tim tidak memiliki agen reviewer independen. Risiko kualitas tinggi.")
        if project.budget > 0 and cost_range["max_idr"] > project.budget:
            warnings.append(f"Peringatan: Estimasi biaya maksimum ({cost_range['max_idr']:,.0f} IDR) melampaui pagu anggaran ({project.budget:,.0f} IDR).")

        return {
            "project_id": project.id,
            "package": package,
            "brief_analysis": brief_analysis,
            "agents": recommended_agents,
            "cost_range": cost_range,
            "duration_range": duration_range,
            "has_reviewer": has_reviewer,
            "warnings": warnings,
        }

    def calculate_estimates(
        self,
        agents: list[dict[str, Any]],
        size: str,
        models: list[Model],
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """
        Calculates cost range and duration range based on agent configuration and project size.
        """
        # Base tokens per project size
        token_multipliers = {"S": 150_000, "M": 400_000, "L": 1_000_000, "XL": 2_500_000}
        total_tokens = token_multipliers.get(size, 400_000)

        # Cost computation per tier
        tier_price_map = {"low": 1.0, "medium": 3.0, "high": 15.0, "xhigh": 30.0}  # per 1M tokens in USD
        usd_to_idr = 16_000.0

        total_weight = sum(TIER_RANKS.get(a["tier"].lower(), 2) for a in agents) or 1
        est_cost_usd_base = 0.0

        for a in agents:
            tier = a["tier"].lower()
            price_per_m = tier_price_map.get(tier, 3.0)
            agent_tokens = total_tokens * (TIER_RANKS.get(tier, 2) / total_weight)
            est_cost_usd_base += (agent_tokens / 1_000_000.0) * price_per_m

        min_cost_usd = round(est_cost_usd_base * 0.85, 2)
        max_cost_usd = round(est_cost_usd_base * 1.35 + 2.0, 2)  # safety margin + meeting round overhead

        min_cost_idr = round(min_cost_usd * usd_to_idr, -3)
        max_cost_idr = round(max_cost_usd * usd_to_idr, -3)

        cost_range = {
            "min_usd": min_cost_usd,
            "max_usd": max_cost_usd,
            "min_idr": min_cost_idr,
            "max_idr": max_cost_idr,
            "currency": "IDR",
        }

        duration_map = {
            "S": {"min_days": 3, "max_days": 5, "label": "3–5 hari kerja (1 sprint)"},
            "M": {"min_days": 7, "max_days": 14, "label": "1–2 minggu (1–2 sprint)"},
            "L": {"min_days": 14, "max_days": 28, "label": "2–4 minggu (2–3 sprint)"},
            "XL": {"min_days": 30, "max_days": 60, "label": "1–2 bulan (3–5 sprint)"},
        }
        duration_range = duration_map.get(size, duration_map["M"])

        return cost_range, duration_range

    async def approve_team_g1(
        self,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        team_config: list[dict[str, Any]],
        clarification_notes: str = "",
    ) -> dict[str, Any]:
        """
        G1 Approval:
        1. Persists Agent records in DB.
        2. Records Gate G1 approval.
        3. Initializes Git workspace on disk per PRD Section 5.2c.
        4. Writes team-charter.md with PRD Section 5.2d metadata.
        """
        res = await db.execute(
            select(Project).options(selectinload(Project.profile)).where(Project.id == project_id)
        )
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # 1. Persist Agents
        created_agents: list[Agent] = []
        for agent_data in team_config:
            role_id = agent_data["role_id"].lower()
            if "reviewer" in role_id or "checker" in role_id:
                agent_perms = ["read_workspace", "search_workspace", "search_literature", "post_message", "update_card"]
            elif "scrum" in role_id:
                agent_perms = ["read_workspace", "post_message", "ask_po", "update_card"]
            elif "lead" in role_id:
                agent_perms = ["read_workspace", "write_workspace", "search_workspace", "search_literature", "post_message", "ask_po", "update_card"]
            else:
                agent_perms = ["read_workspace", "write_workspace", "search_workspace", "post_message", "update_card"]

            agent = Agent(
                project_id=project.id,
                role_template_id=agent_data["role_id"],
                role_version=agent_data.get("role_version", 1),
                name=agent_data["role_name"],
                model_id=agent_data.get("model_id"),
                fallback_model_id=agent_data.get("fallback_model_id"),
                runtime=agent_data.get("runtime", "api"),
                permissions=agent_perms,
            )
            db.add(agent)
            created_agents.append(agent)

        # 2. Record Gate G1
        gate = Gate(
            project_id=project.id,
            gate_type="G1",
            target_id=project.id,
            decision="approved",
            comments="Tim disetujui oleh PO pada gerbang G1.",
            decided_by_user_id=user_id,
            decided_at=datetime.now(timezone.utc),
        )
        db.add(gate)

        # Update project status
        project.status = "inception"

        # 3. Initialize Git workspace directory per PRD 5.2c
        # Sanitize slug
        slug = "".join(c if c.isalnum() else "-" for c in project.title.lower()).strip("-")
        workspace_dir = os.path.join(os.getcwd(), "workspaces", f"proyek-{slug}-{project.id[:6]}")
        os.makedirs(workspace_dir, exist_ok=True)
        project.workspace_path = workspace_dir

        folders = [
            "00-brief/lampiran",
            "01-tim",
            "02-inception/notulen",
            "sprints/sprint-01/daily",
            "sprints/sprint-01/kerja",
            "final",
            "pembelajaran",
        ]
        for f in folders:
            os.makedirs(os.path.join(workspace_dir, f), exist_ok=True)

        # 4. Write 00-brief/brief.md with PRD 5.2d metadata
        brief_meta = f"""---
proyek: {project.title}
tahap: 0 Brief
dokumen: Brief Proyek
versi: 1
dibuat_oleh: PO
direview_oleh: TimAI
status: disetujui
disetujui_oleh: PO · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
---

# Brief Proyek: {project.title}

## Informasi Umum
- **Profil Proyek**: {project.profile_id}
- **Pagu Anggaran**: {project.budget:,.0f} {project.currency}
- **Bahasa**: {project.language}
- **Tenggat**: {project.deadline.strftime('%Y-%m-%d') if project.deadline else 'Fleksibel'}

## Isi Brief
{project.brief}

## Bidang Profil Khusus
{json.dumps(project.profile_fields, indent=2, ensure_ascii=False)}
"""
        with open(os.path.join(workspace_dir, "00-brief", "brief.md"), "w", encoding="utf-8") as f:
            f.write(brief_meta)

        # 5. Write 00-brief/klarifikasi.md
        klarifikasi_meta = f"""---
proyek: {project.title}
tahap: 1 Klarifikasi
dokumen: Catatan Klarifikasi & Asumsi
versi: 1
dibuat_oleh: Analis · FakeProvider
direview_oleh: PO
status: disetujui
disetujui_oleh: PO · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
---

# Catatan Klarifikasi & Asumsi

{clarification_notes or 'Tidak ada pertanyaan ambigu tambahan; asumsi brief awal diterima.'}
"""
        with open(os.path.join(workspace_dir, "00-brief", "klarifikasi.md"), "w", encoding="utf-8") as f:
            f.write(klarifikasi_meta)

        # 6. Write 01-tim/team-charter.md with PRD 5.2d metadata
        agent_lines = []
        for a in created_agents:
            agent_lines.append(
                f"- **{a.name}** (`{a.role_template_id}`)\n"
                f"  - Runtime: `{a.runtime}`\n"
                f"  - Model: `{a.model_id or 'default'}` | Fallback: `{a.fallback_model_id or 'default'}`"
            )
        team_list_str = "\n".join(agent_lines)

        charter_meta = f"""---
proyek: {project.title}
tahap: 2 Usulan Tim
dokumen: Team Charter
versi: 1
dibuat_oleh: Team Composer · FakeProvider
direview_oleh: PO
status: disetujui
disetujui_oleh: PO · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
---

# Team Charter: {project.title}

## Profil Tim: {project.profile_id.capitalize()}

### Anggota Tim
{team_list_str}

## Aturan Kolaborasi (Scrum)
1. Setiap sesi diskusi dibatasi tepat **SATU putaran** untuk efisiensi token.
2. Setiap tahapan penting wajib melewati Titik Konfirmasi PO.
3. Seluruh artefak diuji terhadap Definition of Done sebelum dapat disajikan sebagai Increment di Sprint Review (G3).
"""
        charter_path = os.path.join(workspace_dir, "01-tim", "team-charter.md")
        with open(charter_path, "w", encoding="utf-8") as f:
            f.write(charter_meta)

        # 7. Initialize Git repository in workspace
        try:
            subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "TimAI"], cwd=workspace_dir, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "bot@timai.local"], cwd=workspace_dir, capture_output=True, check=False)
            subprocess.run(["git", "add", "."], cwd=workspace_dir, capture_output=True, check=False)
            subprocess.run(["git", "commit", "-m", "Inisialisasi workspace dan Team Charter (G1 Disetujui)"], cwd=workspace_dir, capture_output=True, check=False)
        except Exception as exc:
            logger.warning("Git init in workspace directory encountered warning: %s", exc)

        await db.commit()

        return {
            "project_id": project.id,
            "gate_id": gate.id,
            "status": project.status,
            "workspace_path": project.workspace_path,
            "team_charter_file": charter_path,
            "agent_count": len(created_agents),
        }


team_composer = TeamComposer()
