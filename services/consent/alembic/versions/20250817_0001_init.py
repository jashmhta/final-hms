import sqlalchemy as sa
from alembic import op
revision = "20250817_0001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table(
        "consent_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
    )
    op.create_table(
        "consent_signatures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("signer_name", sa.String(length=100), nullable=False),
        sa.Column("signer_phone", sa.String(length=50), nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
    )
def downgrade() -> None:
    op.drop_table("consent_signatures")
    op.drop_table("consent_templates")