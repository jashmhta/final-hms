DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
TEST_RUNNER = "django.test.runner.DiscoverRunner"
SECRET_KEY = "test-secret-key-for-testing-only"
DEBUG = False
