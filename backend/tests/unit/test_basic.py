"""
test_basic module
"""

from django.test import TestCase


class BasicTestCase(TestCase):
    def test_basic_functionality(self):
        self.assertEqual(1 + 1, 2)
