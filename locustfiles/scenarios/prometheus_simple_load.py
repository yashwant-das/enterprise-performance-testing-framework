import random
from locust import HttpUser, task, between, events
from prometheus_client import CollectorRegistry, Gauge, Counter, start_http_server
import threading

# Create a custom Prometheus registry
registry = CollectorRegistry()

# Prometheus metrics
requests_total = Counter('locust_requests_total', 'Total number of requests', ['method', 'name', 'result'], registry=registry)
response_time_percentile = Gauge('locust_response_time_percentile', 'Response time percentiles', ['method', 'name', 'quantile'], registry=registry)
users_gauge = Gauge('locust_users', 'Number of users', registry=registry)

# Storage for response times (for percentile calculation)
response_times = {}
response_times_lock = threading.Lock()

def start_prometheus_server():
    """Start Prometheus metrics server"""
    try:
        start_http_server(8089, registry=registry)  # This will conflict with Locust UI, so let's use a different port
    except OSError:
        pass  # Port might already be in use

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Track request metrics"""
    result = "success" if exception is None else "failure"
    requests_total.labels(method=request_type, name=name, result=result).inc()
    
    # Store response times for percentile calculation
    with response_times_lock:
        key = f"{request_type}_{name}"
        if key not in response_times:
            response_times[key] = []
        response_times[key].append(response_time)
        
        # Keep only last 1000 response times to prevent memory issues
        if len(response_times[key]) > 1000:
            response_times[key] = response_times[key][-1000:]

@events.user_count_changed.add_listener
def on_user_count_changed(user_count, **kwargs):
    """Track user count"""
    users_gauge.set(user_count)

def update_percentiles():
    """Update response time percentiles"""
    with response_times_lock:
        for key, times in response_times.items():
            if times:
                method, name = key.split('_', 1)
                times_sorted = sorted(times)
                
                # Calculate percentiles
                percentiles = [0.50, 0.95, 0.99]
                for p in percentiles:
                    idx = int(len(times_sorted) * p) - 1
                    if idx >= 0:
                        value = times_sorted[idx]
                        response_time_percentile.labels(method=method, name=name, quantile=str(p)).set(value)

class SimpleUser(HttpUser):
    """
    A simple user class that simulates basic API interactions with Prometheus metrics.
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when a user starts"""
        # Start Prometheus server on first user (if not already started)
        if not hasattr(self.environment, 'prometheus_started'):
            threading.Thread(target=start_prometheus_server, daemon=True).start()
            self.environment.prometheus_started = True
            
            # Start percentile update thread
            def percentile_updater():
                import time
                while True:
                    time.sleep(10)  # Update every 10 seconds
                    update_percentiles()
            
            threading.Thread(target=percentile_updater, daemon=True).start()

    @task
    def get_root(self):
        """
        Simulates a GET request to the root endpoint.
        """
        self.client.get("/")

    @task(3)  # This task will be executed 3 times more often
    def get_users(self):
        """
        Simulates a GET request to fetch all users.
        """
        self.client.get("/users")

    @task
    def get_user_by_id(self):
        """
        Simulates a GET request to fetch a specific user by a random ID.
        """
        user_id = random.randint(1, 10)  # Assuming user IDs are between 1 and 10
        self.client.get(f"/users/{user_id}", name="/users/[id]")

    @task
    def create_user(self):
        """
        Simulates a POST request to create a new user.
        """
        new_user = {
            "name": f"TestUser_{random.randint(100, 999)}",
            "email": f"test.{random.randint(100, 999)}@example.com"
        }
        self.client.post("/users", json=new_user)
