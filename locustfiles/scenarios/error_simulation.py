import random
import time
from locust import HttpUser, task, between, events

class ErrorSimulationUser(HttpUser):
    """
    A user class that includes error simulation scenarios.
    """
    wait_time = between(1, 3)

    @task(2)
    def get_valid_user(self):
        """Test valid user retrieval."""
        user_id = random.randint(1, 5)  # Valid user IDs
        self.client.get(f"/users/{user_id}", name="/users/[valid_id]")

    @task(1)
    def get_invalid_user(self):
        """Test invalid user retrieval to simulate 404 errors."""
        user_id = random.randint(100, 999)  # Invalid user IDs
        with self.client.get(f"/users/{user_id}", name="/users/[invalid_id]", catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # Expected behavior

    @task(2)
    def create_valid_user(self):
        """Test valid user creation."""
        new_user = {
            "name": f"TestUser_{random.randint(1000, 9999)}",
            "email": f"test.{random.randint(1000, 9999)}@example.com"
        }
        self.client.post("/users", json=new_user)

    @task(1)
    def create_invalid_user(self):
        """Test invalid user creation to simulate 400 errors."""
        invalid_user = {
            "email": f"test.{random.randint(1000, 9999)}@example.com"
            # Missing required 'name' field
        }
        with self.client.post("/users", json=invalid_user, name="/users/[invalid]", catch_response=True) as response:
            if response.status_code == 400:
                response.success()  # Expected behavior

    @task(3)
    def get_users_list(self):
        """Test retrieving the users list."""
        self.client.get("/users")

    @task(1)
    def slow_request_simulation(self):
        """Simulate occasionally slow requests by adding client-side delay."""
        if random.random() < 0.1:  # 10% chance of slow request
            time.sleep(random.uniform(0.5, 1.0))
        self.client.get("/")

    def on_start(self):
        """Called when a user starts."""
        pass

    def on_stop(self):
        """Called when a user stops."""
        pass
