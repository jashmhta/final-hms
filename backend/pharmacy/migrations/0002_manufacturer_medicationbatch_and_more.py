from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("hospitals", "0002_plan_hospitalplan"),
        ("pharmacy", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Manufacturer",
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
                ("name", models.CharField(max_length=255)),
                ("address", models.TextField(blank=True)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=20)),
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
            name="MedicationBatch",
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
                ("batch_number", models.CharField(max_length=100, unique=True)),
                ("expiry_date", models.DateField()),
                ("quantity_received", models.PositiveIntegerField()),
                ("quantity_remaining", models.PositiveIntegerField()),
                (
                    "cost_per_unit",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("received_date", models.DateField()),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)ss",
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "manufacturer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="pharmacy.manufacturer",
                    ),
                ),
            ],
            options={
                "ordering": ["-received_date"],
            },
        ),
        migrations.RenameField(
            model_name="medication",
            old_name="supplier",
            new_name="brand_name",
        ),
        migrations.RenameField(
            model_name="medication",
            old_name="stock_quantity",
            new_name="max_stock_level",
        ),
        migrations.RemoveField(
            model_name="medication",
            name="expiry_date",
        ),
        migrations.AddField(
            model_name="medication",
            name="generic_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="medication",
            name="interactions",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="medication",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="medication",
            name="is_discontinued",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="medication",
            name="ndc_code",
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
        migrations.AddField(
            model_name="medication",
            name="reorder_level",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="medication",
            name="route",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="medication",
            name="selling_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="medication",
            name="storage_instructions",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="medication",
            name="total_stock_quantity",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="medication",
            name="unit_cost",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="medication",
            name="warnings",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="Supplier",
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
                ("name", models.CharField(max_length=255)),
                ("contact_person", models.CharField(blank=True, max_length=255)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("address", models.TextField(blank=True)),
                ("lead_time_days", models.PositiveIntegerField(default=7)),
                ("is_preferred", models.BooleanField(default=False)),
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
            name="StockAdjustment",
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
                ("quantity_adjusted", models.IntegerField()),
                ("reason", models.CharField(max_length=255)),
                (
                    "adjustment_type",
                    models.CharField(
                        choices=[
                            ("EXPIRY", "Expiry"),
                            ("DAMAGE", "Damage"),
                            ("THEFT", "Theft/Loss"),
                            ("TRANSFER", "Transfer"),
                            ("CORRECTION", "Correction"),
                        ],
                        max_length=20,
                    ),
                ),
                ("adjusted_at", models.DateTimeField(auto_now_add=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "adjusted_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="stock_adjustments",
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
                    "medication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="pharmacy.medication",
                    ),
                ),
                (
                    "medication_batch",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="pharmacy.medicationbatch",
                    ),
                ),
                (
                    "witnessed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="witnessed_adjustments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-adjusted_at"],
            },
        ),
        migrations.CreateModel(
            name="PharmacyOrder",
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
                ("order_date", models.DateTimeField(auto_now_add=True)),
                ("expected_delivery_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("ORDERED", "Ordered"),
                            ("SHIPPED", "Shipped"),
                            ("RECEIVED", "Received"),
                            ("PARTIAL", "Partial Delivery"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                (
                    "total_cost",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                ("tracking_number", models.CharField(blank=True, max_length=100)),
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
                    "ordered_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pharmacy_orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="pharmacy.supplier",
                    ),
                ),
            ],
            options={
                "ordering": ["-order_date"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
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
                ("quantity_ordered", models.PositiveIntegerField()),
                ("quantity_received", models.PositiveIntegerField(default=0)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("batch_number", models.CharField(blank=True, max_length=100)),
                ("expected_delivery_date", models.DateField(blank=True, null=True)),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)ss",
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "medication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="pharmacy.medication",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="pharmacy.pharmacyorder",
                    ),
                ),
            ],
            options={
                "ordering": ["medication"],
            },
        ),
        migrations.AddField(
            model_name="medicationbatch",
            name="medication",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="batches",
                to="pharmacy.medication",
            ),
        ),
        migrations.AddField(
            model_name="medicationbatch",
            name="received_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="received_batches",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="DrugCategory",
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
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_controlled_substance", models.BooleanField(default=False)),
                (
                    "schedule",
                    models.CharField(
                        blank=True,
                        help_text="DEA Schedule for controlled substances",
                        max_length=20,
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
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Dispensation",
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
                ("quantity_dispensed", models.PositiveIntegerField()),
                ("dispensed_at", models.DateTimeField(auto_now_add=True)),
                ("instructions_given", models.TextField(blank=True)),
                ("patient_education_provided", models.BooleanField(default=False)),
                ("verification_performed", models.BooleanField(default=False)),
                (
                    "cost_to_patient",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "dispensed_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="dispensations",
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
                    "medication_batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispensations",
                        to="pharmacy.medicationbatch",
                    ),
                ),
                (
                    "prescription",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dispensations",
                        to="pharmacy.prescription",
                    ),
                ),
            ],
            options={
                "ordering": ["-dispensed_at"],
            },
        ),
        migrations.AddField(
            model_name="medication",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="pharmacy.drugcategory",
            ),
        ),
        migrations.AddField(
            model_name="medication",
            name="manufacturer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="pharmacy.manufacturer",
            ),
        ),
        migrations.AddField(
            model_name="medication",
            name="preferred_supplier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="pharmacy.supplier",
            ),
        ),
        migrations.AddIndex(
            model_name="medicationbatch",
            index=models.Index(
                fields=["medication", "batch_number"],
                name="pharmacy_me_medicat_5f348c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="medicationbatch",
            index=models.Index(
                fields=["expiry_date"], name="pharmacy_me_expiry__266ee1_idx"
            ),
        ),
    ]