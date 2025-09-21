class DatabaseRouter:
    def db_for_read(self, model, **hints):
        if hasattr(model, "_meta") and model._meta.app_label in [
            "analytics",
            "feedback",
            "accounting",
        ]:
            return "replica"
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
