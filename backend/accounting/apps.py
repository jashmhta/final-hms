from django.apps import AppConfig


class AccountingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounting"
    verbose_name = "Hospital Accounting System"

    def ready(self):
        import accounting.signals  # Import signals when app is ready  # noqa: F401, E501
