import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Sprint, UsageRecord

logger = logging.getLogger("timai.budget_guard")

# Default conversion rate from ModelGateway USD cost to IDR if project currency is IDR
USD_TO_IDR_RATE = 16_000.0


class BudgetExceededException(HTTPException):
    def __init__(self, detail: str, budget_data: dict[str, Any] | None = None) -> None:
        super().__init__(status_code=402, detail=detail)
        self.budget_data = budget_data or {}


class RiskyActionBlockedException(HTTPException):
    def __init__(self, detail: str, action_data: dict[str, Any] | None = None) -> None:
        super().__init__(status_code=403, detail=detail)
        self.action_data = action_data or {}


class BudgetGuard:
    """
    Enforces budget limits per discussion, sprint, and project.
    Triggers warnings at 50% and 80%, and hard pause at 100% (FR-11.3).
    Guards risky actions (file deletion, new domain access, push external) per FR-5.5.
    """

    def __init__(self) -> None:
        self.approved_risky_actions: set[str] = set()

    def normalize_cost_to_project_currency(self, cost_usd: float, currency: str) -> float:
        """Convert standard model cost in USD to project currency (default IDR)."""
        curr = (currency or "IDR").upper()
        if curr == "IDR":
            return cost_usd * USD_TO_IDR_RATE
        return cost_usd

    async def get_project_spent(self, db: AsyncSession, project_id: str, currency: str = "IDR") -> float:
        """Calculate total spent for the project across all usage records."""
        stmt = (
            select(func.coalesce(func.sum(UsageRecord.cost), 0.0))
            .where(UsageRecord.project_id == project_id)
        )
        res = await db.execute(stmt)
        total_usd = float(res.scalar() or 0.0)
        return self.normalize_cost_to_project_currency(total_usd, currency)

    async def get_budget_status(
        self,
        db: AsyncSession,
        project_id: str,
        sprint_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Inspects spent vs budget for project and optional sprint.
        Returns percentage, status (normal, warning_50, warning_80, exceeded_100), and limits.
        """
        proj_res = await db.execute(select(Project).where(Project.id == project_id))
        project = proj_res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

        currency = project.currency or "IDR"
        project_budget = float(project.budget or 0.0)
        total_spent = await self.get_project_spent(db, project_id, currency)

        sprint_budget = 0.0
        sprint_spent = 0.0
        if sprint_id:
            sp_res = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
            sprint = sp_res.scalar_one_or_none()
            if sprint:
                sprint_budget = float(sprint.budget_limit or 0.0)
                # In MVP, project spent is tracked directly; sprint spent is proportional or project spent
                sprint_spent = total_spent

        # Evaluate against active limit
        limit_to_check = sprint_budget if (sprint_budget > 0) else project_budget
        spent_to_check = sprint_spent if (sprint_budget > 0) else total_spent

        percent_used = 0.0
        if limit_to_check > 0:
            percent_used = (spent_to_check / limit_to_check) * 100.0

        if percent_used >= 100.0:
            status = "exceeded_100"
            warning_message = (
                f"Batas anggaran 100% tercapai ({currency} {spent_to_check:,.2f} / {currency} {limit_to_check:,.2f}). "
                "Eksekusi dijeda sampai PO menambah anggaran."
            )
        elif percent_used >= 80.0:
            status = "warning_80"
            warning_message = (
                f"Peringatan anggaran 80%: Penggunaan telah mencapai {percent_used:.1f}% "
                f"({currency} {spent_to_check:,.2f} / {currency} {limit_to_check:,.2f})."
            )
        elif percent_used >= 50.0:
            status = "warning_50"
            warning_message = (
                f"Peringatan anggaran 50%: Penggunaan telah mencapai {percent_used:.1f}% "
                f"({currency} {spent_to_check:,.2f} / {currency} {limit_to_check:,.2f})."
            )
        else:
            status = "normal"
            warning_message = None

        return {
            "project_id": project_id,
            "currency": currency,
            "project_budget": project_budget,
            "total_spent": total_spent,
            "sprint_id": sprint_id,
            "sprint_budget": sprint_budget,
            "percent_used": round(percent_used, 2),
            "status": status,
            "warning_message": warning_message,
            "is_paused": project.status == "paused" or status == "exceeded_100",
        }

    async def verify_can_execute(
        self,
        db: AsyncSession,
        project_id: str,
        sprint_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Pre-flight check before initiating agent task execution.
        Raises BudgetExceededException if 100% limit is reached or project is paused.
        """
        status_info = await self.get_budget_status(db, project_id, sprint_id)
        if status_info["status"] == "exceeded_100":
            # Auto-pause project if not already paused
            proj_res = await db.execute(select(Project).where(Project.id == project_id))
            proj = proj_res.scalar_one_or_none()
            if proj and proj.status != "paused":
                proj.status = "paused"
                await db.commit()

            logger.warning("Budget limit 100%% hit for project %s: pausing execution.", project_id)
            raise BudgetExceededException(
                detail=status_info["warning_message"],
                budget_data=status_info,
            )

        return status_info

    def check_risky_action(
        self,
        project_id: str,
        action_type: str,
        target_resource: str,
        is_pre_approved: bool = False,
    ) -> bool:
        """
        Guards risky actions:
        - delete_workspace_file
        - new_domain_access
        - push_external_repo
        Raises RiskyActionBlockedException if not approved by PO.
        """
        action_key = f"{project_id}:{action_type}:{target_resource}"
        if is_pre_approved or action_key in self.approved_risky_actions:
            return True

        detail_map = {
            "delete_workspace_file": f"Tindakan berisiko: Penghapusan berkas '{target_resource}' memerlukan persetujuan PO.",
            "new_domain_access": f"Tindakan berisiko: Akses domain luar baru '{target_resource}' memerlukan izin PO.",
            "push_external_repo": f"Tindakan berisiko: Push ke repositori eksternal '{target_resource}' memerlukan izin PO.",
        }
        msg = detail_map.get(
            action_type,
            f"Tindakan berisiko: '{action_type}' pada '{target_resource}' memerlukan persetujuan PO."
        )

        raise RiskyActionBlockedException(
            detail=f"{msg} Tunggu konfirmasi PO.",
            action_data={
                "project_id": project_id,
                "action_type": action_type,
                "target_resource": target_resource,
                "action_key": action_key,
            },
        )

    def approve_risky_action(self, project_id: str, action_type: str, target_resource: str) -> str:
        """Records PO explicit approval for a risky action."""
        action_key = f"{project_id}:{action_type}:{target_resource}"
        self.approved_risky_actions.add(action_key)
        logger.info("PO approved risky action: %s", action_key)
        return action_key


budget_guard = BudgetGuard()
