from django.apps import AppConfig


class AccountingAdvancedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounting_advanced"
    verbose_name = "Advanced Accounting"

    def ready(self):
        pass
