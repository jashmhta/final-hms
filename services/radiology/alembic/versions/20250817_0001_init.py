import sqlalchemy as sa
from alembic import op
revision = "20250817_0001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table(
        "radiology_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False, index=True),
        sa.Column("study_type", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
    )
    op.create_table(
        "radiology_reports",
        sa.Column("order_id", sa.Integer(), primary_key=True),
        sa.Column("impression", sa.Text(), nullable=False),
    )
def downgrade() -> None:
    op.drop_table("radiology_reports")
    op.drop_table("radiology_orders")