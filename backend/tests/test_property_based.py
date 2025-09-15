import pytest
from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase

class TestPropertyBased(TestCase):
    @given(st.text(min_size=1, max_size=100))
    def test_user_creation_with_valid_names(self, name):
        # Example property test
        from users.models import User
        user = User.objects.create(username=name, email=f"{name}@example.com")
        assert user.username == name

    # Add more property-based tests for critical functions