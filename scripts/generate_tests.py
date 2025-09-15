#!/usr/bin/env python
import os
import inspect
from django.apps import apps

def generate_crud_tests():
    for app_config in apps.get_app_configs():
        app_name = app_config.name
        models = app_config.get_models()
        for model in models:
            test_file = f"backend/{app_name}/tests/test_{model.__name__.lower()}_crud.py"
            if not os.path.exists(test_file):
                with open(test_file, 'w') as f:
                    f.write(f"""
import pytest
from django.test import TestCase
from {app_name}.models import {model.__name__}

class {model.__name__}CRUDTest(TestCase):
    def test_create_{model.__name__.lower()}(self):
        # Implement create test
        pass

    def test_read_{model.__name__.lower()}(self):
        # Implement read test
        pass

    def test_update_{model.__name__.lower()}(self):
        # Implement update test
        pass

    def test_delete_{model.__name__.lower()}(self):
        # Implement delete test
        pass
""")

if __name__ == "__main__":
    generate_crud_tests()