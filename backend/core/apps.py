"""
apps module
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from . import signals

        # Setup cache invalidation after all apps are loaded
        try:
            from .enhanced_cache import setup_cache_invalidation

            setup_cache_invalidation()
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Could not setup cache invalidation: {str(e)}")
