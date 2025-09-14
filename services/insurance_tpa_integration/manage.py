#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

<<<<<<<< HEAD:services/insurance_tpa_integration/manage.py
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings_integration")
========

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms.settings")
>>>>>>>> transform-refactor:hms-enterprise-grade/backend/manage.py
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
<<<<<<<< HEAD:services/insurance_tpa_integration/manage.py
========


if __name__ == "__main__":
    main()
>>>>>>>> transform-refactor:hms-enterprise-grade/backend/manage.py
