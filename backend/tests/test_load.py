"""
test_load module
"""

import pytest
from locust import HttpUser, task


class HMSUser(HttpUser):
    @task
    def test_api_endpoint(self):
        self.client.get("/api/patients/")
