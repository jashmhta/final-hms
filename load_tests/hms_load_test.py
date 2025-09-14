from locust import HttpUser, between, task


class HMSUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        self.client.get("/health/")

    @task(3)
    def login(self):
        self.client.post(
            "/auth/login/", json={"username": "testuser", "password": "testpass"}
        )

    @task(2)
    def get_patients(self):
        self.client.get("/patients/")

    @task(1)
    def create_appointment(self):
        self.client.post(
            "/appointments/", json={"patient": 1, "doctor": 1, "date": "2025-01-01"}
        )
