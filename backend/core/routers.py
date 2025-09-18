class DatabaseRouter:
    route_app_labels = {
        "accounting": "accounting",
        "analytics": "analytics",
        "appointments": "appointments",
        "billing": "billing",
        "ehr": "ehr",
        "facilities": "facilities",
        "hr": "hr",
        "lab": "lab",
        "patients": "patients",
        "pharmacy": "pharmacy",
        "users": "users",
    }
    def db_for_read(self, model, **hints):
        app_label = model._meta.app_label
        return self.route_app_labels.get(app_label, "default")
    def db_for_write(self, model, **hints):
        app_label = model._meta.app_label
        return self.route_app_labels.get(app_label, "default")
    def allow_relation(self, obj1, obj2, **hints):
        db1 = self.db_for_write(obj1.__class__)
        db2 = self.db_for_write(obj2.__class__)
        return db1 == db2
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == self.route_app_labels[app_label]
        return db == "default"