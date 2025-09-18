import sqlalchemy as sa
from alembic import op
revision = "20250817_0001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table(
        "bed_stats",
        sa.Column("hospital_id", sa.String(), primary_key=True),
        sa.Column("total", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("available", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("occupied", sa.Integer(), nullable=False, server_default="10"),
    )
def downgrade() -> None:
    op.drop_table("bed_stats")