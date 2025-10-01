#!/usr/bin/env python3
"""
Health check script for deployment validation.
Performs comprehensive health checks on the HMS system.
"""
import argparse
import json
import sys
import time
from typing import Dict, List
import requests


def check_api_health(base_url: str) -> Dict:
    """Check API endpoint health"""
    try:
        response = requests.get(f"{base_url}/health/", timeout=10)
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_database_health() -> Dict:
    """Check database connectivity"""
    try:
        import django
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms.settings')
        django.setup()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return {"status": "healthy"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_redis_health() -> Dict:
    """Check Redis connectivity"""
    try:
        import redis
        import os
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def run_health_checks(environment: str, detailed: bool = False) -> Dict:
    """Run all health checks"""
    results = {
        "environment": environment,
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Determine base URL based on environment
    base_urls = {
        "staging": "http://staging.example.com",
        "production": "http://production.example.com",
        "local": "http://localhost:8000"
    }
    base_url = base_urls.get(environment, "http://localhost:8000")
    
    # Run checks
    results["checks"]["api"] = check_api_health(base_url)
    
    if detailed:
        results["checks"]["database"] = check_database_health()
        results["checks"]["redis"] = check_redis_health()
    
    # Determine overall status
    all_healthy = all(
        check.get("status") == "healthy" 
        for check in results["checks"].values()
    )
    results["overall_status"] = "healthy" if all_healthy else "unhealthy"
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Run health checks")
    parser.add_argument(
        "--environment",
        default="local",
        help="Environment to check (staging, production, local)"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Run detailed health checks"
    )
    parser.add_argument(
        "--output",
        default="json",
        choices=["json", "text"],
        help="Output format"
    )
    
    args = parser.parse_args()
    
    results = run_health_checks(args.environment, args.detailed)
    
    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        print(f"Environment: {results['environment']}")
        print(f"Overall Status: {results['overall_status']}")
        for check_name, check_result in results['checks'].items():
            status = check_result.get('status', 'unknown')
            print(f"  {check_name}: {status}")
            if 'error' in check_result:
                print(f"    Error: {check_result['error']}")
    
    # Exit with error code if unhealthy
    sys.exit(0 if results["overall_status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
