import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Agent, Confirmation, Contribution, Decision, Discussion, Project
from app.gateway.gateway import model_gateway

logger = logging.getLogger("timai.meeting")

# In-memory pub/sub queues for live SSE per discussion
_discussion_listeners: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}


def register_listener(discussion_id: str) -> asyncio.Queue[dict[str, Any]]:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    if discussion_id not in _discussion_listeners:
        _discussion_listeners[discussion_id] = []
    _discussion_listeners[discussion_id].append(queue)
    return queue


def unregister_listener(discussion_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
    if discussion_id in _discussion_listeners:
        if queue in _discussion_listeners[discussion_id]:
            _discussion_listeners[discussion_id].remove(queue)
        if not _discussion_listeners[discussion_id]:
            del _discussion_listeners[discussion_id]


async def broadcast_event(discussion_id: str, event_type: str, data: dict[str, Any]) -> None:
    if discussion_id in _discussion_listeners:
        payload = {"event": event_type, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()}
        for queue in _discussion_listeners[discussion_id]:
            await queue.put(payload)


class MeetingEngine:
    """
    Core Meeting Engine:
    - Enforces strictly ONE ROUND per discussion session (Rule K5).
    - Exactly one contribution per participant per round.
    - Word limit (default 400 words) and round token ceiling.
    - Scrum Master synthesis with options A/B.
    - PO Confirmation Point with Decision Log & Notulen generation.
    - Idempotent and restart-resilient via PostgreSQL state machine.
    """

    MAX_WORDS_PER_CONTRIBUTION = 400
    ROUND_TOKEN_CEILING = 4000  # Default max round token limit

    async def create_discussion(
        self,
        db: AsyncSession,
        project_id: str,
        agenda: str,
        discussion_type: str = "inception",
        participant_agent_ids: list[str] | None = None,
    ) -> Discussion:
        """Initialize a new discussion in 'draft' status."""
        res_proj = await db.execute(
            select(Project).options(selectinload(Project.agents)).where(Project.id == project_id)
        )
        project = res_proj.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        agents = project.agents
        if not participant_agent_ids:
            participant_agent_ids = [a.id for a in agents]

        # Order participants: Scrum Master first or as moderator
        sm_agents = [a.id for a in agents if "scrum_master" in a.role_template_id.lower() or "moderator" in a.name.lower()]
        other_agents = [a_id for a_id in participant_agent_ids if a_id not in sm_agents]

        # Speaker order: participants speak in turn, SM synthesizes at the end
        speaker_order = other_agents if other_agents else participant_agent_ids

        discussion = Discussion(
            project_id=project.id,
            discussion_type=discussion_type,
            agenda=agenda,
            participants=participant_agent_ids,
            speaker_order=speaker_order,
            round_number=1,
            status="draft",
            synthesis={},
            cost=0.0,
        )
        db.add(discussion)
        await db.commit()
        await db.refresh(discussion)
        return discussion

    async def run_round(
        self,
        db: AsyncSession,
        discussion_id: str,
        token_ceiling: int = ROUND_TOKEN_CEILING,
    ) -> Discussion:
        """
        Executes one single round of discussion.
        Transitions: draft -> running -> synthesis -> waiting_po.
        """
        res = await db.execute(
            select(Discussion)
            .options(
                selectinload(Discussion.project).selectinload(Project.agents),
                selectinload(Discussion.contributions),
            )
            .where(Discussion.id == discussion_id)
        )
        disc = res.scalar_one_or_none()
        if not disc:
            raise ValueError("Discussion not found")

        if disc.status in ("waiting_po", "finished"):
            return disc

        disc.status = "running"
        await db.commit()
        await broadcast_event(disc.id, "discussion_started", {"agenda": disc.agenda, "round": disc.round_number})

        project = disc.project
        agents_map = {a.id: a for a in project.agents}

        # Find already completed contributions for this round (idempotency against worker restarts!)
        existing_agent_ids = {c.agent_id for c in disc.contributions if c.round_number == disc.round_number}

        total_round_tokens = sum(c.token_count for c in disc.contributions if c.round_number == disc.round_number)

        # Build rolling conversation history
        prior_messages_text = []
        for c in disc.contributions:
            agent_name = agents_map.get(c.agent_id).name if c.agent_id in agents_map else "Agen"
            prior_messages_text.append(f"{agent_name}: {c.content}")

        # Iterate through speaker order: each agent speaks EXACTLY ONCE
        for agent_id in disc.speaker_order:
            if agent_id in existing_agent_ids:
                logger.info("Agent %s already spoke in round %s, skipping", agent_id, disc.round_number)
                continue

            if total_round_tokens >= token_ceiling:
                logger.warning("Round token ceiling of %s reached for discussion %s", token_ceiling, disc.id)
                await broadcast_event(disc.id, "token_ceiling_reached", {"total_tokens": total_round_tokens})
                break

            agent = agents_map.get(agent_id)
            if not agent:
                continue

            await broadcast_event(disc.id, "speaker_started", {"agent_id": agent.id, "agent_name": agent.name})

            # Prompt agent to contribute
            prompt_content = f"""Agenda Diskusi: {disc.agenda}
Proyek: {project.title} ({project.profile_id})
Peran Anda: {agent.name} ({agent.role_template_id})

Riwayat Diskusi Sebelumnya:
{chr(10).join(prior_messages_text[-5:]) if prior_messages_text else '(Belum ada pembicara sebelumnya)'}

Instruksi:
Tanggapi agenda dan masukan rekan tim sebelumnya secara kritis dan konstruktif.
Batas panjang: maksimal {self.MAX_WORDS_PER_CONTRIBUTION} kata.
Jangan mengulang apa yang sudah disepakati tanpa menambahkan sudut pandang baru."""

            messages = [{"role": "user", "content": prompt_content}]
            gateway_res = await model_gateway.complete(
                agent_context=f"Discussion Round {disc.round_number} - {agent.name}",
                messages=messages,
                model=agent.model_id,
                fallback_model=agent.fallback_model_id,
                db=db,
                project_id=project.id,
                agent_id=agent.id,
            )

            # Limit word count
            content = gateway_res.content
            words = content.split()
            if len(words) > self.MAX_WORDS_PER_CONTRIBUTION:
                content = " ".join(words[: self.MAX_WORDS_PER_CONTRIBUTION]) + "..."

            token_count = gateway_res.input_tokens + gateway_res.output_tokens
            total_round_tokens += token_count
            disc.cost += gateway_res.cost

            # Record Contribution in DB
            contrib = Contribution(
                discussion_id=disc.id,
                agent_id=agent.id,
                round_number=disc.round_number,
                content=content,
                token_count=token_count,
            )
            db.add(contrib)
            await db.commit()

            prior_messages_text.append(f"{agent.name}: {content}")
            await broadcast_event(
                disc.id,
                "contribution_received",
                {
                    "contribution_id": contrib.id,
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "content": content,
                    "tokens": token_count,
                },
            )

        # Transition to Synthesis
        disc.status = "synthesis"
        await db.commit()
        await broadcast_event(disc.id, "synthesis_started", {})

        # Scrum Master synthesizes the round
        synthesis_data = await self._synthesize_discussion(
            db, disc, project, agents_map, prior_messages_text
        )
        disc.synthesis = synthesis_data

        # Transition to Waiting PO
        disc.status = "waiting_po"

        # Create Confirmation record for PO
        conf = Confirmation(
            discussion_id=disc.id,
            options=[
                {"id": "A", "label": synthesis_data.get("disagreements", {}).get("option_a", "Pilihan Pendekatan A")},
                {"id": "B", "label": synthesis_data.get("disagreements", {}).get("option_b", "Pilihan Pendekatan B")},
            ],
            selected_option=None,
            po_feedback=None,
        )
        db.add(conf)
        await db.commit()

        await broadcast_event(
            disc.id,
            "waiting_po",
            {
                "synthesis": synthesis_data,
                "confirmation_id": conf.id,
                "options": conf.options,
            },
        )

        return disc

    async def _synthesize_discussion(
        self,
        db: AsyncSession,
        disc: Discussion,
        project: Project,
        agents_map: dict[str, Agent],
        contributions: list[str],
    ) -> dict[str, Any]:
        """Scrum Master writes balanced synthesis with proposed decision, agreed points, and A/B options."""
        # Find Scrum Master agent
        sm_agent = next((a for a in agents_map.values() if "scrum_master" in a.role_template_id.lower()), None)
        model_id = sm_agent.model_id if sm_agent else None

        prompt = f"""Anda adalah Scrum Master. Rangkum diskusi satu putaran berikut ini:
Agenda: {disc.agenda}
Proyek: {project.title}

Daftar Kontribusi Peserta:
{chr(10).join(contributions)}

Buat sintesis berimbang dalam format JSON dengan kunci:
- proposed_decision: Usulan keputusan paling rasional
- agreed_points: Daftar 2-3 hal yang disepakati bersama
- disagreements: Objek berisi 'option_a' dan 'option_b' bila ada perbedaan sudut pandang
- questions_for_po: Pertanyaan klarifikasi kritis untuk PO
- estimated_continuation_cost: Estimasi biaya bila diskusi dilanjutkan satu putaran lagi (dalam IDR/USD)"""

        res = await model_gateway.complete(
            agent_context="Scrum Master Synthesis",
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            db=db,
            project_id=project.id,
            agent_id=sm_agent.id if sm_agent else None,
        )

        # Fallback structured synthesis if response is non-JSON
        try:
            parsed = json.loads(res.content)
            if isinstance(parsed, dict) and "proposed_decision" in parsed:
                return parsed
        except Exception:
            pass

        return {
            "proposed_decision": f"Fokus pada implementasi metodologi utama untuk agenda {disc.agenda}.",
            "agreed_points": [
                "Ruang lingkup pengujian awal perlu didefinisikan secara bertahap.",
                "Rujukan ilmiah wajib diverifikasi sebelum integrasi.",
            ],
            "disagreements": {
                "option_a": "Prioritaskan kelayakan teknis dan percepatan rilis draf.",
                "option_b": "Prioritaskan ketelitian verifikasi data sekunder dan validitas empiris.",
            },
            "questions_for_po": [
                "Apakah pendekatan Option A atau Option B yang lebih selaras dengan visi strategis Anda?",
            ],
            "estimated_continuation_cost": "Rp 15.000 (±1 putaran)",
        }

    async def handle_po_confirmation(
        self,
        db: AsyncSession,
        confirmation_id: str,
        user_id: str,
        action: str,  # "approve_proposed", "choose_option", "redirect", "continue_discussion"
        selected_option: str | None = None,
        po_notes: str | None = None,
    ) -> dict[str, Any]:
        """
        PO interacts with Confirmation Point:
        - approve_proposed: accepts SM synthesis
        - choose_option: selects option A or B directly
        - redirect: PO inputs own direction
        - continue_discussion: triggers exactly one more round with PO guidance
        """
        conf_res = await db.execute(
            select(Confirmation)
            .options(
                selectinload(Confirmation.discussion).selectinload(Discussion.project),
                selectinload(Confirmation.discussion).selectinload(Discussion.contributions),
            )
            .where(Confirmation.id == confirmation_id)
        )
        conf = conf_res.scalar_one_or_none()
        if not conf:
            raise ValueError("Confirmation not found")

        disc = conf.discussion
        project = disc.project

        now = datetime.now(timezone.utc)
        conf.decided_by_user_id = user_id
        conf.decided_at = now
        conf.po_feedback = po_notes

        if action == "continue_discussion":
            # Start another single round with PO direction
            conf.selected_option = "continue_discussion"
            disc.round_number += 1
            disc.status = "running"
            await db.commit()

            # Async trigger next round
            asyncio.create_task(self.run_round(db, disc.id))
            return {
                "status": "continued",
                "message": f"Diskusi dilanjutkan ke putaran {disc.round_number} dengan arahan PO.",
                "discussion_id": disc.id,
            }

        # Otherwise, a final decision is made
        decision_text = ""
        rationale = po_notes or "Disetujui oleh PO tanpa catatan tambahan."
        alternatives = conf.options

        if action == "approve_proposed":
            conf.selected_option = "proposed"
            decision_text = disc.synthesis.get("proposed_decision", "Usulan Scrum Master diterima.")
        elif action == "choose_option":
            conf.selected_option = selected_option or "A"
            opt_map = {o.get("id"): o.get("label") for o in conf.options if isinstance(o, dict)}
            decision_text = opt_map.get(selected_option, f"Opsi {selected_option}")
        elif action == "redirect":
            conf.selected_option = "redirect"
            decision_text = po_notes or "PO menetapkan arah alternatif tersendiri."

        # 1. Insert Decision entity into DB
        decision = Decision(
            discussion_id=disc.id,
            project_id=project.id,
            summary=decision_text,
            rationale=rationale,
            alternatives=alternatives,
            decided_by="PO",
            created_at=now,
        )
        db.add(decision)

        # 2. Transition discussion to finished
        disc.status = "finished"

        # 3. Write Decision to decision-log.md & Minutes (notulen/agenda-NN.md)
        if project.workspace_path and os.path.exists(project.workspace_path):
            self._write_decision_and_minutes(project, disc, decision, conf)

        await db.commit()

        await broadcast_event(
            disc.id,
            "decision_made",
            {
                "decision_id": decision.id,
                "summary": decision.summary,
                "action": action,
            },
        )

        return {
            "status": "finished",
            "decision_id": decision.id,
            "decision_summary": decision.summary,
            "discussion_id": disc.id,
        }

    def _write_decision_and_minutes(
        self,
        project: Project,
        disc: Discussion,
        decision: Decision,
        conf: Confirmation,
    ) -> None:
        """Saves minutes to 02-inception/notulen/agenda-NN.md and appends to decision-log.md."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # 1. Append to 02-inception/decision-log.md
        dec_log_path = os.path.join(project.workspace_path, "02-inception", "decision-log.md")
        os.makedirs(os.path.dirname(dec_log_path), exist_ok=True)
        dec_entry = f"""
## [{now_str}] Keputusan Agenda: {disc.agenda}
- **Keputusan**: {decision.summary}
- **Alasan**: {decision.rationale}
- **Alternatif**: {json.dumps(decision.alternatives, ensure_ascii=False)}
- **Diputuskan Oleh**: PO (Konfirmasi {conf.selected_option})
---
"""
        with open(dec_log_path, "a", encoding="utf-8") as f:
            f.write(dec_entry)

        # 2. Write Notulen agenda-NN.md with PRD 5.2d metadata
        clean_agenda = "".join(c if c.isalnum() else "-" for c in disc.agenda.lower())[:30].strip("-")
        minutes_dir = os.path.join(project.workspace_path, "02-inception", "notulen")
        os.makedirs(minutes_dir, exist_ok=True)
        minutes_path = os.path.join(minutes_dir, f"agenda-{clean_agenda}.md")

        contrib_text = []
        for c in disc.contributions:
            contrib_text.append(f"### Putaran {c.round_number}\n{c.content}\n")

        minutes_content = f"""---
proyek: {project.title}
tahap: 3 Inception
dokumen: Notulen Diskusi
versi: 1
dibuat_oleh: Scrum Master
direview_oleh: PO
status: disetujui
disetujui_oleh: PO · {now_str}
---

# Notulen Diskusi: {disc.agenda}

## Kontribusi Peserta (Satu Putaran)
{chr(10).join(contrib_text)}

## Sintesis Scrum Master
- **Usulan Keputusan**: {disc.synthesis.get('proposed_decision', '-')}
- **Poin Disepakati**: {', '.join(disc.synthesis.get('agreed_points', []))}
- **Beda Pendapat**:
  - Opsi A: {disc.synthesis.get('disagreements', {}).get('option_a', '-')}
  - Opsi B: {disc.synthesis.get('disagreements', {}).get('option_b', '-')}

## Keputusan Titik Konfirmasi PO
- **Pilihan PO**: {conf.selected_option}
- **Keputusan Final**: {decision.summary}
- **Catatan PO**: {decision.rationale}
"""
        with open(minutes_path, "w", encoding="utf-8") as f:
            f.write(minutes_content)


meeting_engine = MeetingEngine()
