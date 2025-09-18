import sqlalchemy as sa
from alembic import op
revision = "initial"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table(
        "ipd_admissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("admission_date", sa.DateTime(), nullable=True),
        sa.Column("admission_type", sa.String(), nullable=True),
        sa.Column("admitting_doctor", sa.Integer(), nullable=True),
        sa.Column("primary_diagnosis", sa.String(), nullable=True),
        sa.Column("estimated_stay", sa.Integer(), nullable=True),
        sa.Column("actual_stay", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ipd_admissions_id"), "ipd_admissions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_ipd_admissions_patient_id"),
        "ipd_admissions",
        ["patient_id"],
        unique=False,
    )
    op.create_table(
        "ipd_beds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("bed_number", sa.String(), nullable=True),
        sa.Column("bed_type", sa.String(), nullable=True),
        sa.Column("is_occupied", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ipd_beds_id"), "ipd_beds", ["id"], unique=False)
    op.create_table(
        "nursing_care",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("nursing_notes", sa.Text(), nullable=True),
        sa.Column("vital_signs", sa.String(), nullable=True),
        sa.Column("medication_administered", sa.String(), nullable=True),
        sa.Column("care_plan", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_nursing_care_id"), "nursing_care", ["id"], unique=False)
    op.create_table(
        "discharge_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("discharge_date", sa.DateTime(), nullable=True),
        sa.Column("discharge_diagnosis", sa.String(), nullable=True),
        sa.Column("followup_instructions", sa.Text(), nullable=True),
        sa.Column("medications_prescribed", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_discharge_summaries_id"), "discharge_summaries", ["id"], unique=False
    )
def downgrade() -> None:
    op.drop_index(op.f("ix_discharge_summaries_id"), table_name="discharge_summaries")
    op.drop_table("discharge_summaries")
    op.drop_index(op.f("ix_nursing_care_id"), table_name="nursing_care")
    op.drop_table("nursing_care")
    op.drop_index(op.f("ix_ipd_beds_id"), table_name="ipd_beds")
    op.drop_table("ipd_beds")
    op.drop_index(op.f("ix_ipd_admissions_id"), table_name="ipd_admissions")
    op.drop_index(op.f("ix_ipd_admissions_patient_id"), table_name="ipd_admissions")
    op.drop_table("ipd_admissions")