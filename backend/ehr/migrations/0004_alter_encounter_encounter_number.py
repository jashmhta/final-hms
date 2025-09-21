from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ehr", "0003_allergy_assessment_clinicalnote_planofcare_and_more"),
    ]
    operations = [
        migrations.AlterField(
            model_name="encounter",
            name="encounter_number",
            field=models.CharField(db_index=True, default="TEMP", max_length=50),
        ),
    ]
