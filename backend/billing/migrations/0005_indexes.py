from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0004_departmentbudget"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="bill",
            index=models.Index(fields=["status"], name="bill_status_idx"),
        ),
        migrations.AddIndex(
            model_name="billlineitem",
            index=models.Index(fields=["department"], name="bli_dept_idx"),
        ),
    ]
