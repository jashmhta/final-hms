from django.apps import AppConfig


class HIPAAComplianceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "compliance.hipaa"
    verbose_name = "HIPAA Compliance"

    def ready(self):
        """Initialize HIPAA compliance features on app startup."""
        import compliance.hipaa.signals  # Import signals
        from compliance.hipaa.utils import ConsentManager

        # Check for expired consents on startup
        expired_count = ConsentManager.check_consent_expiry()
        print(f"HIPAA: {expired_count} expired consents deactivated on startup")
