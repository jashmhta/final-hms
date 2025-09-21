import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hospitals", "0002_plan_hospitalplan"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("appointments", "0003_alter_appointment_appointment_number"),
    ]
    operations = [
        migrations.CreateModel(
            name="SurgeryType",
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
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("estimated_duration", models.PositiveIntegerField(default=60)),
                (
                    "complexity_level",
                    models.CharField(
                        choices=[
                            ("LOW", "Low"),
                            ("MEDIUM", "Medium"),
                            ("HIGH", "High"),
                        ],
                        max_length=20,
                    ),
                ),
                ("requires_anesthesia", models.BooleanField(default=True)),
                ("anesthesia_type", models.CharField(blank=True, max_length=50)),
                ("required_equipment", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
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
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="OTSlot",
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
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("duration_minutes", models.PositiveIntegerField()),
                ("is_available", models.BooleanField(default=True)),
                ("max_cases", models.PositiveIntegerField(default=1)),
                ("scheduled_cases", models.PositiveIntegerField(default=0)),
                ("requires_anesthesia", models.BooleanField(default=True)),
                ("equipment_needed", models.JSONField(blank=True, default=list)),
                ("notes", models.TextField(blank=True)),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)ss",
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "ot_room",
                    models.ForeignKey(
                        limit_choices_to={"resource_type": "ROOM"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ot_slots",
                        to="appointments.resource",
                    ),
                ),
                (
                    "scheduled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "surgery_type_allowed",
                    models.ManyToManyField(blank=True, to="appointments.surgerytype"),
                ),
            ],
            options={
                "ordering": ["start_time"],
            },
        ),
        migrations.CreateModel(
            name="OTBooking",
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
                ("procedure_name", models.CharField(max_length=255)),
                ("procedure_code", models.CharField(blank=True, max_length=50)),
                ("estimated_duration", models.PositiveIntegerField()),
                ("actual_duration", models.PositiveIntegerField(blank=True, null=True)),
                ("anesthesia_type", models.CharField(blank=True, max_length=50)),
                ("anesthesia_notes", models.TextField(blank=True)),
                ("pre_op_checklist_completed", models.BooleanField(default=False)),
                ("time_out_completed", models.BooleanField(default=False)),
                ("pre_op_labs_reviewed", models.BooleanField(default=False)),
                ("informed_consent", models.BooleanField(default=False)),
                ("incision_time", models.DateTimeField(blank=True, null=True)),
                ("closure_time", models.DateTimeField(blank=True, null=True)),
                ("blood_loss_ml", models.PositiveIntegerField(blank=True, null=True)),
                ("fluids_given_ml", models.PositiveIntegerField(blank=True, null=True)),
                ("specimens_sent", models.TextField(blank=True)),
                ("complications", models.TextField(blank=True)),
                ("recovery_room_assigned", models.BooleanField(default=False)),
                ("post_op_orders", models.TextField(blank=True)),
                ("pain_management_plan", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("SCHEDULED", "Scheduled"),
                            ("CONFIRMED", "Confirmed"),
                            ("IN_PROGRESS", "In Progress"),
                            ("COMPLETED", "Completed"),
                            ("CANCELLED", "Cancelled"),
                            ("DELAYED", "Delayed"),
                        ],
                        default="SCHEDULED",
                        max_length=20,
                    ),
                ),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("LOW", "Low"),
                            ("NORMAL", "Normal"),
                            ("HIGH", "High"),
                            ("URGENT", "Urgent"),
                            ("EMERGENT", "Emergent"),
                        ],
                        default="NORMAL",
                        max_length=10,
                    ),
                ),
                ("is_confidential", models.BooleanField(default=False)),
                ("special_instructions", models.TextField(blank=True)),
                (
                    "anesthesiologist",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={"role": "ANESTHESIOLOGIST"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="anesthesiologist_ot_bookings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "appointment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ot_booking",
                        to="appointments.appointment",
                    ),
                ),
                (
                    "assisting_surgeon",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={"role": "SURGEON"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assisting_ot_bookings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "booked_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="booked_ot_bookings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "circulating_nurse",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={"role": "NURSE"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="circulating_ot_bookings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "confirmed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="confirmed_ot_bookings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)ss",
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "lead_surgeon",
                    models.ForeignKey(
                        limit_choices_to={"role": "SURGEON"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lead_ot_bookings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "ot_slot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bookings",
                        to="appointments.otslot",
                    ),
                ),
                (
                    "scrub_nurse",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={"role": "NURSE"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="scrub_ot_bookings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "surgery_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="appointments.surgerytype",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="surgerytype",
            index=models.Index(fields=["hospital", "is_active"], name="appointment_hospita_5f7f35_idx"),
        ),
        migrations.AddIndex(
            model_name="otslot",
            index=models.Index(fields=["ot_room", "start_time"], name="appointment_ot_room_b0021c_idx"),
        ),
        migrations.AddIndex(
            model_name="otslot",
            index=models.Index(
                fields=["is_available", "start_time"],
                name="appointment_is_avai_d81001_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="otbooking",
            index=models.Index(fields=["ot_slot", "status"], name="appointment_ot_slot_d65f7e_idx"),
        ),
        migrations.AddIndex(
            model_name="otbooking",
            index=models.Index(fields=["appointment", "status"], name="appointment_appoint_3f4198_idx"),
        ),
    ]
