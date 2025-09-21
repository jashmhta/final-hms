from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("appointments", "0004_surgerytype_otslot_otbooking_and_more"),
    ]
    operations = [
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "status", "start_at"],
                name="appointment_hospita_399297_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "primary_provider", "status", "start_at"],
                name="appointment_hospita_b03d0f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "patient", "status"],
                name="appointment_hospita_7e533e_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "appointment_type", "status"],
                name="appointment_hospita_61a71a_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "is_telehealth", "start_at"],
                name="appointment_hospita_ef7928_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "priority", "start_at"],
                name="appointment_hospita_d22273_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["hospital", "created_at"], name="appointment_hospita_d3f55e_idx"),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "start_at", "end_at"],
                name="appointment_hospita_f978f8_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "primary_provider", "start_at", "status"],
                name="appointment_hospita_a68a7f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "patient", "start_at", "status"],
                name="appointment_hospita_16cc22_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "appointment_type", "start_at", "status"],
                name="appointment_hospita_e6a61d_idx",
            ),
        ),
    ]
