#!/usr/bin/env python3
"""
Validation script for the Performance Testing Framework
Checks all services and endpoints for proper functioning
"""

import requests
import subprocess
import json
import time
from datetime import datetime

def check_url(url, name, expected_status=200, timeout=5):
    """Check if a URL is accessible and returns expected status"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == expected_status:
            print(f"✅ {name}: OK (HTTP {response.status_code})")
            return True
        else:
            print(f"❌ {name}: Failed (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: Failed ({str(e)})")
        return False

def check_docker_containers():
    """Check status of Docker containers"""
    print("\n🐳 Docker Container Status:")
    try:
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker status check failed: {e}")
        return False

def check_prometheus_targets():
    """Check Prometheus targets status"""
    print("\n🎯 Prometheus Targets:")
    try:
        response = requests.get('http://localhost:9090/api/v1/targets', timeout=5)
        if response.status_code == 200:
            data = response.json()
            for target in data['data']['activeTargets']:
                health = "✅" if target['health'] == 'up' else "❌"
                print(f"{health} {target['labels']['job']}: {target['health']}")
            return True
        else:
            print(f"❌ Failed to fetch Prometheus targets (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Prometheus targets check failed: {str(e)}")
        return False

def check_custom_metrics():
    """Check if custom metrics are being collected"""
    print("\n📊 Custom Metrics Status:")
    metrics_to_check = [
        'app_requests_total',
        'app_users_count', 
        'app_active_connections',
        'app_response_time_avg'
    ]
    
    success_count = 0
    for metric in metrics_to_check:
        try:
            response = requests.get(f'http://localhost:9090/api/v1/query?query={metric}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['data']['result']:
                    value = data['data']['result'][0]['value'][1]
                    print(f"✅ {metric}: {value}")
                    success_count += 1
                else:
                    print(f"❌ {metric}: No data")
            else:
                print(f"❌ {metric}: Query failed")
        except Exception as e:
            print(f"❌ {metric}: Error ({str(e)})")
    
    return success_count == len(metrics_to_check)

def check_grafana_datasources():
    """Check Grafana datasource status"""
    print("\n📈 Grafana Datasources:")
    try:
        # Note: In production, you'd use proper authentication
        response = requests.get('http://admin:admin@localhost:3000/api/datasources', timeout=5)
        if response.status_code == 200:
            datasources = response.json()
            for ds in datasources:
                print(f"✅ {ds['name']}: {ds['type']} ({ds['url']})")
            return True
        else:
            print(f"❌ Failed to fetch datasources (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Grafana datasources check failed: {str(e)}")
        return False

def main():
    print("🚀 Performance Testing Framework Validation")
    print("=" * 50)
    print(f"Validation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check Docker containers
    docker_ok = check_docker_containers()
    
    # Service health checks
    print("\n🔍 Service Health Checks:")
    services = [
        ("http://localhost:5001/health", "Target App Health"),
        ("http://localhost:8089", "Locust Web UI"),
        ("http://localhost:9090/-/healthy", "Prometheus Health"),
        ("http://localhost:3000/api/health", "Grafana Health"),
        ("http://localhost:5001/metrics", "Target App Metrics"),
    ]
    
    health_results = []
    for url, name in services:
        health_results.append(check_url(url, name))
    
    # Check Prometheus targets
    targets_ok = check_prometheus_targets()
    
    # Check custom metrics
    metrics_ok = check_custom_metrics()
    
    # Check Grafana datasources
    grafana_ok = check_grafana_datasources()
    
    # Summary
    print("\n📋 Validation Summary:")
    print("=" * 30)
    
    all_services_healthy = all(health_results)
    overall_status = (docker_ok and all_services_healthy and 
                     targets_ok and metrics_ok and grafana_ok)
    
    status_emoji = "✅" if overall_status else "❌"
    status_text = "PASS" if overall_status else "FAIL"
    
    print(f"{status_emoji} Overall Status: {status_text}")
    print(f"🐳 Docker Containers: {'✅ OK' if docker_ok else '❌ FAIL'}")
    print(f"🔍 Service Health: {'✅ OK' if all_services_healthy else '❌ FAIL'}")
    print(f"🎯 Prometheus Targets: {'✅ OK' if targets_ok else '❌ FAIL'}")
    print(f"📊 Custom Metrics: {'✅ OK' if metrics_ok else '❌ FAIL'}")
    print(f"📈 Grafana Datasources: {'✅ OK' if grafana_ok else '❌ FAIL'}")
    
    if overall_status:
        print("\n🎉 Framework is ready for load testing!")
        print("\n📍 Access URLs:")
        print("   • Locust UI: http://localhost:8089")
        print("   • Prometheus: http://localhost:9090")
        print("   • Grafana: http://localhost:3000 (admin/admin)")
        print("   • Target App: http://localhost:5001")
    else:
        print("\n⚠️  Some components failed validation. Check the logs above.")
    
    return 0 if overall_status else 1

if __name__ == "__main__":
    exit(main())
