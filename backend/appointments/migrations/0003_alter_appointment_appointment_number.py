from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("appointments", "0002_appointmenthistory_appointmentreminder_and_more"),
    ]
    operations = [
        migrations.AlterField(
            model_name="appointment",
            name="appointment_number",
            field=models.CharField(db_index=True, default="TEMP", max_length=50),
        ),
    ]
