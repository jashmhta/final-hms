from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0004_alter_patient_medical_record_number"),
    ]
    operations = [
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "status", "created_at"],
                name="patients_pa_hospita_8adb46_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "primary_care_physician", "status"],
                name="patients_pa_hospita_8d2d3e_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "date_of_birth"],
                name="patients_pa_hospita_b87851_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "gender", "status"],
                name="patients_pa_hospita_c5aff8_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "city", "state"],
                name="patients_pa_hospita_e4853b_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "vip_status"], name="patients_pa_hospita_55b0fe_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "confidential"],
                name="patients_pa_hospita_2732ab_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "patient_portal_enrolled"],
                name="patients_pa_hospita_cea495_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "last_name", "first_name", "status"],
                name="patients_pa_hospita_eb2f7c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "medical_record_number", "status"],
                name="patients_pa_hospita_8d78f1_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(
                fields=["hospital", "primary_care_physician", "created_at"],
                name="patients_pa_hospita_c04f61_idx",
            ),
        ),
    ]
