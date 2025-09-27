"""
646cb7430fc8_init_housekeeping_maintenance module
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "646cb7430fc8"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asset_upkeep",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_name", sa.String(), nullable=False),
        sa.Column("last_maintenance_date", sa.DateTime(), nullable=True),
        sa.Column("next_due_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asset_upkeep_id"), "asset_upkeep", ["id"], unique=False)
    op.create_index("ix_asset_upkeep_status", "asset_upkeep", ["status"], unique=False)
    op.create_table(
        "maintenance_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("description", models.models.EncryptedString(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_maintenance_requests_id"), "maintenance_requests", ["id"], unique=False
    )
    op.create_index(
        "ix_maintenance_requests_status",
        "maintenance_requests",
        ["status"],
        unique=False,
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cleaning_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("description", models.models.EncryptedString(), nullable=False),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("scheduled_date", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", name="taskstatus"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_cleaning_tasks_id"), "cleaning_tasks", ["id"], unique=False
    )
    op.create_index(
        "ix_cleaning_tasks_status", "cleaning_tasks", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_cleaning_tasks_status", table_name="cleaning_tasks")
    op.drop_index(op.f("ix_cleaning_tasks_id"), table_name="cleaning_tasks")
    op.drop_table("cleaning_tasks")
    op.drop_table("users")
    op.drop_index("ix_maintenance_requests_status", table_name="maintenance_requests")
    op.drop_index(op.f("ix_maintenance_requests_id"), table_name="maintenance_requests")
    op.drop_table("maintenance_requests")
    op.drop_index("ix_asset_upkeep_status", table_name="asset_upkeep")
    op.drop_index(op.f("ix_asset_upkeep_id"), table_name="asset_upkeep")
    op.drop_table("asset_upkeep")
