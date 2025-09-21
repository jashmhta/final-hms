import encrypted_model_fields.fields

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0001_initial"),
    ]
    operations = [
        migrations.AlterField(
            model_name="patient",
            name="email",
            field=encrypted_model_fields.fields.EncryptedEmailField(blank=True),
        ),
        migrations.AlterField(
            model_name="patient",
            name="phone",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
    ]
