import random
import time
import logging
from flask import Flask, jsonify, request
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory "database" of users
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "created_at": "2024-01-01T00:00:00Z"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "created_at": "2024-01-01T00:00:00Z"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "created_at": "2024-01-01T00:00:00Z"},
    {"id": 4, "name": "David", "email": "david@example.com", "created_at": "2024-01-01T00:00:00Z"},
    {"id": 5, "name": "Eve", "email": "eve@example.com", "created_at": "2024-01-01T00:00:00Z"},
]
next_user_id = 6

# Simple metrics tracking
metrics = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_error": 0,
    "response_time_sum": 0.0,
    "active_connections": 0
}
metrics_lock = threading.Lock()

@app.before_request
def before_request():
    """Track request start time and increment connection count."""
    request.start_time = time.time()
    with metrics_lock:
        metrics["active_connections"] += 1

@app.after_request
def after_request(response):
    """Track request completion and update metrics."""
    response_time = time.time() - request.start_time
    
    with metrics_lock:
        metrics["requests_total"] += 1
        metrics["active_connections"] -= 1
        metrics["response_time_sum"] += response_time
        
        if 200 <= response.status_code < 400:
            metrics["requests_success"] += 1
        else:
            metrics["requests_error"] += 1
    
    return response

@app.route('/metrics')
def get_metrics():
    """Prometheus-style metrics endpoint."""
    with metrics_lock:
        current_metrics = metrics.copy()
    
    # Calculate average response time
    avg_response_time = 0
    if current_metrics["requests_total"] > 0:
        avg_response_time = current_metrics["response_time_sum"] / current_metrics["requests_total"]
    
    prometheus_metrics = f"""# HELP app_requests_total Total number of requests
# TYPE app_requests_total counter
app_requests_total {current_metrics["requests_total"]}

# HELP app_requests_success_total Total number of successful requests
# TYPE app_requests_success_total counter
app_requests_success_total {current_metrics["requests_success"]}

# HELP app_requests_error_total Total number of error requests
# TYPE app_requests_error_total counter
app_requests_error_total {current_metrics["requests_error"]}

# HELP app_active_connections Current number of active connections
# TYPE app_active_connections gauge
app_active_connections {current_metrics["active_connections"]}

# HELP app_response_time_avg Average response time in seconds
# TYPE app_response_time_avg gauge
app_response_time_avg {avg_response_time:.6f}

# HELP app_users_count Total number of users in database
# TYPE app_users_count gauge
app_users_count {len(users)}

# HELP app_health_status Application health status (1 = healthy, 0 = unhealthy)
# TYPE app_health_status gauge
app_health_status 1
"""
    
    return prometheus_metrics, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found", "status": 404}), 404

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors."""
    return jsonify({"error": "Bad request", "status": 400}), 400

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error", "status": 500}), 500

@app.route('/')
def index():
    """A simple welcome message with API info."""
    return jsonify({
        "message": "Welcome to the Performance Testing Target API!",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "user_by_id": "/users/{id}",
            "health": "/health"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "users_count": len(users)
    })

@app.route('/users', methods=['GET'])
def get_users():
    """Returns a JSON list of all users with pagination support."""
    try:
        # Simulate processing time
        time.sleep(random.uniform(0.05, 0.1))
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400
        
        # Calculate pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_users = users[start:end]
        
        response = {
            "users": paginated_users,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(users),
                "pages": (len(users) + per_page - 1) // per_page
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"Retrieved {len(paginated_users)} users (page {page})")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return jsonify({"error": "Failed to retrieve users"}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Returns a single user by ID."""
    try:
        # Simulate processing time
        time.sleep(random.uniform(0.05, 0.2))
        
        user = next((user for user in users if user["id"] == user_id), None)
        
        if user:
            logger.info(f"Retrieved user {user_id}")
            return jsonify({
                "user": user,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            logger.warning(f"User {user_id} not found")
            return jsonify({
                "error": f"User with id {user_id} not found",
                "status": 404,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
            
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        return jsonify({"error": "Failed to retrieve user"}), 500

@app.route('/users', methods=['POST'])
def create_user():
    """Creates a new user."""
    global next_user_id
    
    try:
        # Validate request
        if not request.json:
            return jsonify({
                "error": "Request must be JSON",
                "status": 400,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Validate required fields
        if 'name' not in request.json or not request.json['name'].strip():
            return jsonify({
                "error": "Missing or empty 'name' field",
                "status": 400,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Validate email format if provided
        email = request.json.get('email', '')
        if email and '@' not in email:
            return jsonify({
                "error": "Invalid email format",
                "status": 400,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Create new user
        new_user = {
            'id': next_user_id,
            'name': request.json['name'].strip(),
            'email': email,
            'created_at': datetime.utcnow().isoformat() + "Z"
        }
        
        users.append(new_user)
        next_user_id += 1
        
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.3))
        
        logger.info(f"Created user {new_user['id']}: {new_user['name']}")
        
        return jsonify({
            "user": new_user,
            "message": "User created successfully",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({"error": "Failed to create user"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
