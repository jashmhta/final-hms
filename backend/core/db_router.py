"""
Database router for read/write splitting and performance optimization.
"""

class DatabaseRouter:
    """
    Routes database operations to appropriate databases for read/write splitting.
    """

    def db_for_read(self, model, **hints):
        """
        Route read operations to replica database if available.
        """
        if hasattr(model, '_meta') and model._meta.app_label in [
            'analytics', 'feedback', 'accounting'
        ]:
            return 'replica'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Route write operations to primary database.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects from different databases.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Allow migrations on all databases.
        """
        return True