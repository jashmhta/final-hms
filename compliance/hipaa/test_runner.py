from django.conf import settings
from django.test.runner import DiscoverRunner


class HIPAACoverageRunner(DiscoverRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Run tests with coverage reporting for HIPAA compliance."""
        import coverage

        cov = coverage.Coverage()
        cov.start()

        result = super().run_tests(test_labels, extra_tests, **kwargs)

        cov.stop()
        cov.save()

        print("\nHIPAA Compliance Test Coverage Report:")
        cov.report()

        if cov.coverage_dict["summary"]["percent_covered"] < 95:
            print("\nWARNING: Test coverage below 95% threshold!")
        else:
            print("\nHIPAA Test Coverage: PASS (95%+ achieved)")

        return result
