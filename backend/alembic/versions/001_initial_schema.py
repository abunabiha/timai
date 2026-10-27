"""Initial schema for TimAI core entities and seed profiles

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-27 08:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="po"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # 2. project_profiles
    op.create_table(
        "project_profiles",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("default_team", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("inception_agenda", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("artifact_templates", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("dod", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("checks", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. projects
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("po_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("profile_id", sa.String(length=50), sa.ForeignKey("project_profiles.id"), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False, server_default=""),
        sa.Column("profile_fields", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="brief"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("budget", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="IDR"),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="id"),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("workspace_path", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_projects_po_id", "projects", ["po_id"])

    # 4. attachments
    op.create_table(
        "attachments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_attachments_project_id", "attachments", ["project_id"])

    # 5. role_templates
    op.create_table(
        "role_templates",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("competencies", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("tier_min", sa.String(length=20), nullable=False, server_default="low"),
        sa.Column("tier_default", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("tools", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("dod", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", "version"),
    )

    # 6. providers
    op.create_table(
        "providers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("base_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 7. models
    op.create_table(
        "models",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("provider_id", sa.String(length=36), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("model_identifier", sa.String(length=100), nullable=False),
        sa.Column("context_window", sa.Integer(), nullable=False, server_default="128000"),
        sa.Column("input_price", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("output_price", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("supports_tools", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_vision", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("competency_score", sa.Float(), nullable=False, server_default="3.0"),
        sa.Column("tier", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_models_provider_id", "models", ["provider_id"])

    # 8. agents
    op.create_table(
        "agents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("role_template_id", sa.String(length=50), nullable=False),
        sa.Column("role_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("model_id", sa.String(length=36), sa.ForeignKey("models.id"), nullable=True),
        sa.Column("fallback_model_id", sa.String(length=36), sa.ForeignKey("models.id"), nullable=True),
        sa.Column("runtime", sa.String(length=20), nullable=False, server_default="api"),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agents_project_id", "agents", ["project_id"])

    # 9. discussions
    op.create_table(
        "discussions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("discussion_type", sa.String(length=50), nullable=False, server_default="general"),
        sa.Column("agenda", sa.String(length=255), nullable=False),
        sa.Column("participants", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("speaker_order", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("round_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("synthesis", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_discussions_project_id", "discussions", ["project_id"])

    # 10. contributions
    op.create_table(
        "contributions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("discussion_id", sa.String(length=36), sa.ForeignKey("discussions.id"), nullable=False),
        sa.Column("agent_id", sa.String(length=36), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("round_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_contributions_discussion_id", "contributions", ["discussion_id"])

    # 11. confirmations
    op.create_table(
        "confirmations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("discussion_id", sa.String(length=36), sa.ForeignKey("discussions.id"), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("selected_option", sa.String(length=50), nullable=True),
        sa.Column("po_feedback", sa.Text(), nullable=True),
        sa.Column("decided_by_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_confirmations_discussion_id", "confirmations", ["discussion_id"])

    # 12. decisions
    op.create_table(
        "decisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("discussion_id", sa.String(length=36), sa.ForeignKey("discussions.id"), nullable=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("alternatives", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("decided_by", sa.String(length=100), nullable=False, server_default="PO"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_decisions_project_id", "decisions", ["project_id"])

    # 13. artifacts
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by_agent_id", sa.String(length=36), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("review_status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"])

    # 14. product_goals
    op.create_table(
        "product_goals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_product_goals_project_id", "product_goals", ["project_id"])

    # 15. epics
    op.create_table(
        "epics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_epics_project_id", "epics", ["project_id"])

    # 16. sprints
    op.create_table(
        "sprints",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("sprint_number", sa.Integer(), nullable=False),
        sa.Column("sprint_goal", sa.Text(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("budget_limit", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="planned"),
        sa.Column("velocity_achieved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sprints_project_id", "sprints", ["project_id"])

    # 17. backlog_items
    op.create_table(
        "backlog_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("epic_id", sa.String(length=36), sa.ForeignKey("epics.id"), nullable=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("item_type", sa.String(length=30), nullable=False, server_default="story"),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("story_points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("po_sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="product_backlog"),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="team_proposed"),
        sa.Column("sprint_id", sa.String(length=36), sa.ForeignKey("sprints.id"), nullable=True),
        sa.Column("is_po_task", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_backlog_items_project_id", "backlog_items", ["project_id"])

    # 18. tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("backlog_item_id", sa.String(length=36), sa.ForeignKey("backlog_items.id"), nullable=False),
        sa.Column("agent_id", sa.String(length=36), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("step_type", sa.String(length=50), nullable=False, server_default="execute"),
        sa.Column("branch_name", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="todo"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tasks_backlog_item_id", "tasks", ["backlog_item_id"])

    # 19. increments
    op.create_table(
        "increments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("sprint_id", sa.String(length=36), sa.ForeignKey("sprints.id"), nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("passed_pbi_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("artifact_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("po_decision", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_increments_sprint_id", "increments", ["sprint_id"])

    # 20. gates
    op.create_table(
        "gates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("gate_type", sa.String(length=10), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False, server_default=""),
        sa.Column("decision", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("comments", sa.Text(), nullable=False, server_default=""),
        sa.Column("decided_by_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gates_project_id", "gates", ["project_id"])

    # 21. usage_records
    op.create_table(
        "usage_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("agent_id", sa.String(length=36), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("requested_model", sa.String(length=100), nullable=False),
        sa.Column("actual_model", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usage_records_project_id", "usage_records", ["project_id"])

    # 22. lessons
    op.create_table(
        "lessons",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("layer", sa.String(length=50), nullable=False),
        sa.Column("scope", sa.String(length=50), nullable=False, server_default="global"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="suggested"),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 23. model_scorecards
    op.create_table(
        "model_scorecards",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("model_id", sa.String(length=36), sa.ForeignKey("models.id"), nullable=True),
        sa.Column("role_name", sa.String(length=100), nullable=False),
        sa.Column("profile_id", sa.String(length=50), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_revisions", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 24. example_libraries
    op.create_table(
        "example_libraries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("profile_id", sa.String(length=50), nullable=False),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("source_artifact_id", sa.String(length=36), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_cross_project_allowed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Seed 5 ProjectProfile records
    profiles_table = sa.table(
        "project_profiles",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("default_team", sa.JSON),
        sa.column("inception_agenda", sa.JSON),
        sa.column("artifact_templates", sa.JSON),
        sa.column("dod", sa.JSON),
        sa.column("checks", sa.JSON),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    op.bulk_insert(
        profiles_table,
        [
            {
                "id": "software",
                "name": "Software",
                "description": "Pengembangan perangkat lunak, web, mobile, dan API berbasis Scrum.",
                "default_team": [],
                "inception_agenda": [],
                "artifact_templates": [],
                "dod": [],
                "checks": [],
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "iot",
                "name": "IoT (Hardware + Firmware + Software)",
                "description": "Pengembangan sistem tertanam, firmware mikroprosesor/ESP32, dan integrasi cloud/dashboard.",
                "default_team": [],
                "inception_agenda": [],
                "artifact_templates": [],
                "dod": [],
                "checks": [],
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "proposal",
                "name": "Proposal Penelitian",
                "description": "Penyusunan usulan hibah riset, rencana anggaran biaya (RAB), dan metodologi penelitian.",
                "default_team": [],
                "inception_agenda": [],
                "artifact_templates": [],
                "dod": [],
                "checks": [],
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "jurnal",
                "name": "Artikel Jurnal",
                "description": "Penulisan manuskrip ilmiah terstandar untuk submisi jurnal bereputasi.",
                "default_team": [],
                "inception_agenda": [],
                "artifact_templates": [],
                "dod": [],
                "checks": [],
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "buku",
                "name": "Buku / Book Chapter",
                "description": "Penulisan buku monograf atau book chapter dwibahasa (Indonesia & Inggris).",
                "default_team": [],
                "inception_agenda": [],
                "artifact_templates": [],
                "dod": [],
                "checks": [],
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("example_libraries")
    op.drop_table("model_scorecards")
    op.drop_table("lessons")
    op.drop_table("usage_records")
    op.drop_table("gates")
    op.drop_table("increments")
    op.drop_table("tasks")
    op.drop_table("backlog_items")
    op.drop_table("sprints")
    op.drop_table("epics")
    op.drop_table("product_goals")
    op.drop_table("artifacts")
    op.drop_table("decisions")
    op.drop_table("confirmations")
    op.drop_table("contributions")
    op.drop_table("discussions")
    op.drop_table("agents")
    op.drop_table("models")
    op.drop_table("providers")
    op.drop_table("role_templates")
    op.drop_table("attachments")
    op.drop_table("projects")
    op.drop_table("project_profiles")
    op.drop_table("users")
