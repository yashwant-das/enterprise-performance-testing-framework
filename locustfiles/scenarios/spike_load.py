import random
from locust import HttpUser, task, between, LoadTestShape

class SpikeLoadUser(HttpUser):
    """
    A user class for spike load testing.
    """
    wait_time = between(0.5, 2)

    @task(4)
    def get_users(self):
        """Heavy load on users endpoint."""
        self.client.get("/users")

    @task(2)
    def get_user_by_id(self):
        """Load on specific user retrieval."""
        user_id = random.randint(1, 10)
        self.client.get(f"/users/{user_id}", name="/users/[id]")

    @task(1)
    def create_user(self):
        """User creation under load."""
        new_user = {
            "name": f"SpikeUser_{random.randint(10000, 99999)}",
            "email": f"spike.{random.randint(10000, 99999)}@example.com"
        }
        self.client.post("/users", json=new_user)

class SpikeLoadShape(LoadTestShape):
    """
    A load shape that creates spike patterns:
    - Ramp up to 50 users over 2 minutes
    - Spike to 200 users for 1 minute
    - Drop to 10 users for 2 minutes
    - Repeat cycle
    """
    
    stages = [
        {"duration": 120, "users": 50, "spawn_rate": 2},   # Ramp up
        {"duration": 180, "users": 200, "spawn_rate": 10}, # Spike
        {"duration": 300, "users": 10, "spawn_rate": 5},   # Cool down
        {"duration": 420, "users": 50, "spawn_rate": 2},   # Ramp up again
        {"duration": 480, "users": 200, "spawn_rate": 10}, # Second spike
        {"duration": 600, "users": 10, "spawn_rate": 5},   # Final cool down
    ]

    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None  # Test ends after all stages
