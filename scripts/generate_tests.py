"""
generate_tests module
"""

import inspect
import os

from django.apps import apps


def generate_crud_tests():
    for app_config in apps.get_app_configs():
        app_name = app_config.name
        models = app_config.get_models()
        for model in models:
            test_file = (
                f"backend/{app_name}/tests/test_{model.__name__.lower()}_crud.py"
            )
            if not os.path.exists(test_file):
                with open(test_file, "w") as f:
                    f.write(f)


if __name__ == "__main__":
    generate_crud_tests()
