import os
import sys
from unittest import TestLoader, TextTestRunner

import django

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings.test_settings")
    django.setup()
    loader = TestLoader()
    suite = loader.discover("tests/blood_bank", pattern="test_*.py")
    runner = TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("All tests passed!")
    else:
        sys.exit(1)
