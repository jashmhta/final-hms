import sqlalchemy as sa
from alembic import op
revision = "20250817_0001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hospital_id", sa.Integer(), nullable=False, index=True),
        sa.Column("patient_id", sa.Integer(), nullable=False, index=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
def downgrade() -> None:
    op.drop_table("feedback")