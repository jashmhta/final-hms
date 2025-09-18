import uuid
import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("hospitals", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Patient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                (
                    "gender",
                    models.CharField(
                        choices=[
                            ("MALE", "Male"),
                            ("FEMALE", "Female"),
                            ("OTHER", "Other"),
                            ("UNKNOWN", "Unknown"),
                        ],
                        default="UNKNOWN",
                        max_length=16,
                    ),
                ),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.TextField(blank=True)),
                ("insurance_provider", models.CharField(blank=True, max_length=255)),
                ("insurance_number", models.CharField(blank=True, max_length=255)),
                ("active", models.BooleanField(default=True)),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)ss",
                        to="hospitals.hospital",
                    ),
                ),
            ],
            options={
                "ordering": ["last_name", "first_name"],
                "indexes": [
                    models.Index(
                        fields=["hospital", "last_name", "first_name"],
                        name="patients_pa_hospita_285e8f_idx",
                    ),
                    models.Index(fields=["uuid"], name="patients_pa_uuid_6d5db2_idx"),
                ],
                "unique_together": {
                    ("hospital", "first_name", "last_name", "date_of_birth", "phone")
                },
            },
        ),
    ]