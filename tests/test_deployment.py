#!/usr/bin/env python3
"""
TREXIMA v2.0 - Deployment Verification Tests

Run these tests before and after deployment to ensure the application
is working correctly.

Usage:
    # Test local development server
    python tests/test_deployment.py --local

    # Test production deployment
    python tests/test_deployment.py --prod

    # Test both
    python tests/test_deployment.py --all
"""

import os
import sys
import json
import time
import argparse
import subprocess
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Configuration
LOCAL_URL = "http://localhost:5000"
PROD_URL = "https://trexima-v4.cfapps.eu10-004.hana.ondemand.com"

# Test results tracking
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")

    def fail(self, name, reason):
        self.failed += 1
        self.errors.append(f"{name}: {reason}")
        print(f"  [FAIL] {name} - {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.errors:
            print(f"\nFailed tests:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")
        return self.failed == 0


def http_get(url, timeout=10):
    """Make HTTP GET request and return response."""
    try:
        req = Request(url, headers={'User-Agent': 'TREXIMA-Test/1.0'})
        with urlopen(req, timeout=timeout) as response:
            return {
                'status': response.status,
                'headers': dict(response.headers),
                'body': response.read().decode('utf-8'),
            }
    except HTTPError as e:
        return {'status': e.code, 'headers': {}, 'body': '', 'error': str(e)}
    except URLError as e:
        return {'status': 0, 'headers': {}, 'body': '', 'error': str(e)}
    except Exception as e:
        return {'status': 0, 'headers': {}, 'body': '', 'error': str(e)}


def http_head(url, timeout=10):
    """Make HTTP HEAD request and return headers."""
    try:
        req = Request(url, method='HEAD', headers={'User-Agent': 'TREXIMA-Test/1.0'})
        with urlopen(req, timeout=timeout) as response:
            # Normalize headers to lowercase keys
            headers = {k.lower(): v for k, v in response.headers.items()}
            return {
                'status': response.status,
                'headers': headers,
            }
    except HTTPError as e:
        return {'status': e.code, 'headers': {}, 'error': str(e)}
    except URLError as e:
        return {'status': 0, 'headers': {}, 'error': str(e)}
    except Exception as e:
        return {'status': 0, 'headers': {}, 'error': str(e)}


def test_health_endpoint(base_url, results):
    """Test the health check endpoint."""
    print("\n--- Health Check Tests ---")

    response = http_get(f"{base_url}/api/health")

    if response['status'] != 200:
        results.fail("Health endpoint status", f"Expected 200, got {response['status']}")
        return

    results.ok("Health endpoint returns 200")

    try:
        data = json.loads(response['body'])

        if data.get('status') == 'healthy':
            results.ok("Health status is 'healthy'")
        else:
            results.fail("Health status", f"Expected 'healthy', got '{data.get('status')}'")

        checks = data.get('checks', {})

        if checks.get('database') == 'ok':
            results.ok("Database check passed")
        else:
            results.fail("Database check", f"Got: {checks.get('database')}")

        if checks.get('storage') == 'ok':
            results.ok("Storage check passed")
        else:
            results.fail("Storage check", f"Got: {checks.get('storage')}")

        if checks.get('auth') == 'ok':
            results.ok("Auth check passed")
        else:
            results.fail("Auth check", f"Got: {checks.get('auth')}")

    except json.JSONDecodeError:
        results.fail("Health response JSON", "Invalid JSON response")


def test_api_info(base_url, results):
    """Test the API info endpoint."""
    print("\n--- API Info Tests ---")

    response = http_get(f"{base_url}/api/info")

    if response['status'] != 200:
        results.fail("API info status", f"Expected 200, got {response['status']}")
        return

    results.ok("API info returns 200")

    try:
        data = json.loads(response['body'])

        if 'version' in data:
            results.ok(f"API version present: {data.get('version')}")
        else:
            results.fail("API version", "Missing version field")

        if 'endpoints' in data:
            results.ok("API endpoints listed")
        else:
            results.fail("API endpoints", "Missing endpoints field")

    except json.JSONDecodeError:
        results.fail("API info JSON", "Invalid JSON response")


def test_frontend_loading(base_url, results):
    """Test that the frontend loads correctly."""
    print("\n--- Frontend Loading Tests ---")

    response = http_get(base_url)

    if response['status'] != 200:
        results.fail("Homepage status", f"Expected 200, got {response['status']}")
        return

    results.ok("Homepage returns 200")

    body = response['body']

    if '<!doctype html>' in body.lower() or '<!DOCTYPE html>' in body:
        results.ok("HTML doctype present")
    else:
        results.fail("HTML doctype", "Missing DOCTYPE")

    if '<div id="root">' in body:
        results.ok("React root div present")
    else:
        results.fail("React root div", "Missing root div")

    if 'src="/assets/' in body:
        results.ok("JavaScript assets referenced")
    else:
        results.fail("JavaScript assets", "Missing JS asset references")

    if 'href="/assets/' in body:
        results.ok("CSS assets referenced")
    else:
        results.fail("CSS assets", "Missing CSS asset references")


def test_static_files(base_url, results):
    """Test that static files are served with correct MIME types."""
    print("\n--- Static File Tests ---")

    # First, get the index.html to find actual asset filenames
    response = http_get(base_url)
    if response['status'] != 200:
        results.fail("Get index.html", f"Failed: {response.get('error')}")
        return

    body = response['body']

    # Extract JS filename
    js_files = []
    import re
    js_matches = re.findall(r'/assets/(index-[a-zA-Z0-9_-]+\.js)', body)
    if js_matches:
        js_files.extend(js_matches)

    css_matches = re.findall(r'/assets/(index-[a-zA-Z0-9_-]+\.css)', body)

    # Test JavaScript file
    if js_files:
        js_file = js_files[0]
        response = http_head(f"{base_url}/assets/{js_file}")

        if response['status'] != 200:
            results.fail(f"JS file {js_file}", f"Status: {response['status']}")
        else:
            results.ok(f"JS file {js_file} accessible")

            # Headers are already lowercase from http_head
            content_type = response['headers'].get('content-type', '').lower()
            if 'javascript' in content_type or 'text/javascript' in content_type:
                results.ok(f"JS MIME type correct: {content_type}")
            else:
                results.fail(f"JS MIME type", f"Expected javascript, got: {content_type}")
    else:
        results.fail("JS file reference", "No JS files found in index.html")

    # Test CSS file
    if css_matches:
        css_file = css_matches[0]
        response = http_head(f"{base_url}/assets/{css_file}")

        if response['status'] != 200:
            results.fail(f"CSS file {css_file}", f"Status: {response['status']}")
        else:
            results.ok(f"CSS file {css_file} accessible")

            content_type = response['headers'].get('content-type', '').lower()
            if 'text/css' in content_type:
                results.ok(f"CSS MIME type correct: {content_type}")
            else:
                results.fail(f"CSS MIME type", f"Expected text/css, got: {content_type}")
    else:
        results.fail("CSS file reference", "No CSS files found in index.html")


def test_api_auth_endpoints(base_url, results):
    """Test authentication API endpoints exist."""
    print("\n--- Auth API Tests ---")

    # Test auth status - should work without authentication
    response = http_get(f"{base_url}/api/auth/status")

    if response['status'] in [200, 401]:
        results.ok(f"Auth status endpoint exists (status: {response['status']})")
    else:
        results.fail("Auth status endpoint", f"Unexpected status: {response['status']}")


def test_api_projects_endpoints(base_url, results):
    """Test projects API endpoints exist."""
    print("\n--- Projects API Tests ---")

    # Test projects list - should require auth or return 401
    response = http_get(f"{base_url}/api/projects")

    if response['status'] in [200, 401, 403]:
        results.ok(f"Projects endpoint exists (status: {response['status']})")
    else:
        results.fail("Projects endpoint", f"Unexpected status: {response['status']}")

    # Test SF endpoints
    response = http_get(f"{base_url}/api/projects/sf-endpoints")

    if response['status'] in [200, 401, 403]:
        results.ok(f"SF endpoints endpoint exists (status: {response['status']})")
    else:
        results.fail("SF endpoints endpoint", f"Unexpected status: {response['status']}")


def test_spa_routing(base_url, results):
    """Test SPA client-side routing support."""
    print("\n--- SPA Routing Tests ---")

    # These routes should all return index.html (SPA handles routing)
    # Note: Some routes like /settings may be handled by legacy code
    test_routes = ['/projects', '/projects/123', '/dashboard']

    for route in test_routes:
        response = http_get(f"{base_url}{route}")

        if response['status'] == 200 and '<div id="root">' in response['body']:
            results.ok(f"SPA route {route} returns index.html")
        else:
            results.fail(f"SPA route {route}", f"Status: {response['status']}")


def run_tests(base_url, name):
    """Run all tests against a base URL."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {base_url}")
    print(f"{'='*60}")

    results = TestResults()

    # Run test suites
    test_health_endpoint(base_url, results)
    test_api_info(base_url, results)
    test_frontend_loading(base_url, results)
    test_static_files(base_url, results)
    test_api_auth_endpoints(base_url, results)
    test_api_projects_endpoints(base_url, results)
    test_spa_routing(base_url, results)

    return results.summary()


def check_local_frontend_build():
    """Verify the frontend build exists locally."""
    print("\n--- Local Frontend Build Check ---")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_app_dir = os.path.join(project_root, 'trexima', 'web', 'static', 'app')

    if not os.path.exists(static_app_dir):
        print(f"  [FAIL] Static app directory missing: {static_app_dir}")
        return False

    print(f"  [PASS] Static app directory exists")

    index_html = os.path.join(static_app_dir, 'index.html')
    if not os.path.exists(index_html):
        print(f"  [FAIL] index.html missing")
        return False

    print(f"  [PASS] index.html exists")

    assets_dir = os.path.join(static_app_dir, 'assets')
    if not os.path.exists(assets_dir):
        print(f"  [FAIL] assets directory missing")
        return False

    print(f"  [PASS] assets directory exists")

    # Check for JS files
    js_files = [f for f in os.listdir(assets_dir) if f.endswith('.js') and not f.endswith('.map')]
    if not js_files:
        print(f"  [FAIL] No JS files in assets")
        return False

    print(f"  [PASS] JS files present: {js_files}")

    # Check for CSS files
    css_files = [f for f in os.listdir(assets_dir) if f.endswith('.css')]
    if not css_files:
        print(f"  [FAIL] No CSS files in assets")
        return False

    print(f"  [PASS] CSS files present: {css_files}")

    return True


def main():
    parser = argparse.ArgumentParser(description='TREXIMA Deployment Verification Tests')
    parser.add_argument('--local', action='store_true', help='Test local development server')
    parser.add_argument('--prod', action='store_true', help='Test production deployment')
    parser.add_argument('--all', action='store_true', help='Test both local and production')
    parser.add_argument('--check-build', action='store_true', help='Check local frontend build')
    args = parser.parse_args()

    if not any([args.local, args.prod, args.all, args.check_build]):
        args.check_build = True
        args.prod = True

    all_passed = True

    if args.check_build or args.all:
        if not check_local_frontend_build():
            all_passed = False

    if args.local or args.all:
        if not run_tests(LOCAL_URL, "Local Development"):
            all_passed = False

    if args.prod or args.all:
        if not run_tests(PROD_URL, "Production"):
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
