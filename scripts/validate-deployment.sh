#!/bin/bash

# Performance Testing Framework Validation Script
# This script validates that all services are running correctly

set -e

echo "🚀 Starting Performance Testing Framework Validation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is responding
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to wait for services to be ready
wait_for_services() {
    echo "⏳ Waiting for services to be ready..."
    
    # Wait up to 120 seconds for services
    local max_attempts=24
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if check_service "Target App" "http://localhost:5001" && \
           check_service "Locust Master" "http://localhost:8089" && \
           check_service "Prometheus" "http://localhost:9090" && \
           check_service "Grafana" "http://localhost:3000"; then
            echo -e "${GREEN}✅ All services are ready!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Waiting... (attempt $((attempt + 1))/$max_attempts)${NC}"
        sleep 5
        ((attempt++))
    done
    
    echo -e "${RED}❌ Services failed to start within the expected time${NC}"
    return 1
}

# Function to run basic functionality tests
run_functional_tests() {
    echo "🧪 Running functional tests..."
    
    # Test Target App endpoints
    echo "Testing Target App endpoints..."
    check_service "GET /" "http://localhost:5001/"
    check_service "GET /users" "http://localhost:5001/users"
    
    # Test creating a user
    echo -n "Testing POST /users... "
    response=$(curl -s -X POST http://localhost:5001/users \
        -H "Content-Type: application/json" \
        -d '{"name": "Test User", "email": "test@example.com"}' \
        -w "%{http_code}")
    
    if echo "$response" | grep -q "201"; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
    
    # Test Prometheus metrics
    echo -n "Testing Prometheus metrics... "
    if curl -s "http://localhost:9090/api/v1/query?query=up" | grep -q "success"; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ All functional tests passed!${NC}"
}

# Function to display service URLs
display_urls() {
    echo ""
    echo "🌐 Service URLs:"
    echo "📊 Locust Web UI: http://localhost:8089"
    echo "📈 Grafana Dashboard: http://localhost:3000 (admin/admin)"
    echo "🔍 Prometheus: http://localhost:9090"
    echo "🎯 Target API: http://localhost:5001"
    echo ""
}

# Function to show next steps
show_next_steps() {
    echo "📋 Next Steps:"
    echo "1. Open Locust Web UI at http://localhost:8089"
    echo "2. Configure test parameters (users: 10, spawn rate: 2)"
    echo "3. Start the load test"
    echo "4. Monitor metrics in Grafana at http://localhost:3000"
    echo ""
    echo "🛑 To stop the framework:"
    echo "   docker-compose down -v"
    echo ""
}

# Main execution
main() {
    # Check if Docker Compose is running
    if ! docker-compose ps | grep -q "Up"; then
        echo -e "${YELLOW}⚠️  Services are not running. Starting them first...${NC}"
        docker-compose up -d --build
    fi
    
    # Wait for services and validate
    if wait_for_services && run_functional_tests; then
        echo -e "${GREEN}🎉 Performance Testing Framework is ready!${NC}"
        display_urls
        show_next_steps
        exit 0
    else
        echo -e "${RED}❌ Validation failed. Check the logs:${NC}"
        echo "   docker-compose logs"
        exit 1
    fi
}

# Run the script
main "$@"
