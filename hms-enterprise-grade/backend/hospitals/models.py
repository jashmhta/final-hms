from django.db import models


class Hospital(models.Model):
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=64, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Plan(models.Model):
    name = models.CharField(max_length=128, unique=True)
    max_users = models.PositiveIntegerField(default=10)
    enable_opd = models.BooleanField(default=True)
    enable_ipd = models.BooleanField(default=True)
    enable_diagnostics = models.BooleanField(default=True)
    enable_pharmacy = models.BooleanField(default=True)
    enable_accounting = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class HospitalPlan(models.Model):
    hospital = models.OneToOneField(
        Hospital, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    # Overrides per hospital
    enable_opd = models.BooleanField(null=True, blank=True)
    enable_ipd = models.BooleanField(null=True, blank=True)
    enable_diagnostics = models.BooleanField(null=True, blank=True)
    enable_pharmacy = models.BooleanField(null=True, blank=True)
    enable_accounting = models.BooleanField(null=True, blank=True)

    def is_enabled(self, module_flag: str) -> bool:
        override = getattr(self, module_flag, None)
        if override is not None:
            return override
        return getattr(self.plan, module_flag)
