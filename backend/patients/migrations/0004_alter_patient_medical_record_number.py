from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "patients",
            "0003_emergencycontact_insuranceinformation_patientalert_and_more",
        ),
    ]
    operations = [
        migrations.AlterField(
            model_name="patient",
            name="medical_record_number",
            field=models.CharField(db_index=True, default="TEMP", max_length=50),
        ),
    ]
