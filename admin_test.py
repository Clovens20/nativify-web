#!/usr/bin/env python3
"""
NativiWeb Studio Admin API Testing
Tests admin-specific endpoints for the NativiWeb platform
"""

import requests
import sys
import json
from datetime import datetime
import time

class NativiWebAdminTester:
    def __init__(self, base_url="https://nativify.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.admin_user_id = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if params is None:
            params = {}

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=15)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    'test': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            self.failed_tests.append({
                'test': name,
                'error': str(e)
            })
            return False, {}

    def setup_admin_user(self):
        """Create a user and make them admin"""
        self.log("\n=== ADMIN SETUP ===")
        
        # Create test user
        test_user = {
            "email": f"admin_{int(time.time())}@example.com",
            "password": "AdminPass123!",
            "name": "Admin Test User"
        }
        
        success, response = self.run_test(
            "Create Admin User",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'id' in response:
            self.admin_user_id = response['id']
            self.log(f"   Admin User ID: {self.admin_user_id}")
        
        # Make user admin using setup endpoint
        admin_secret = "nativiweb_admin_setup_2024"
        success, response = self.run_test(
            "Setup Admin Access",
            "POST",
            "admin/setup",
            200,
            params={"email": test_user["email"], "secret": admin_secret}
        )
        
        if success:
            self.log("   Admin access granted")
        
        # Login as admin
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            self.log(f"   Admin Token: {self.token[:20]}...")

    def create_test_user(self):
        """Create a regular test user for admin operations"""
        self.log("\n=== CREATE TEST USER ===")
        
        test_user = {
            "email": f"testuser_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "name": "Regular Test User"
        }
        
        success, response = self.run_test(
            "Create Test User",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'id' in response:
            self.test_user_id = response['id']
            self.log(f"   Test User ID: {self.test_user_id}")

    def test_admin_analytics(self):
        """Test admin analytics endpoint"""
        self.log("\n=== ADMIN ANALYTICS TESTS ===")
        
        if not self.admin_user_id:
            self.log("❌ Skipping analytics tests - no admin user")
            return
        
        success, response = self.run_test(
            "Get Admin Analytics",
            "GET",
            "admin/analytics",
            200,
            params={"admin_id": self.admin_user_id}
        )
        
        if success:
            self.log(f"   Total Users: {response.get('users', {}).get('total', 0)}")
            self.log(f"   Total Projects: {response.get('projects', {}).get('total', 0)}")
            self.log(f"   Total Builds: {response.get('builds', {}).get('total', 0)}")

    def test_admin_users(self):
        """Test admin user management"""
        self.log("\n=== ADMIN USER MANAGEMENT TESTS ===")
        
        if not self.admin_user_id:
            self.log("❌ Skipping user management tests - no admin user")
            return
        
        # Get all users
        success, response = self.run_test(
            "Get All Users",
            "GET",
            "admin/users",
            200,
            params={"admin_id": self.admin_user_id, "page": 1, "limit": 10}
        )
        
        if success:
            users = response.get('users', [])
            self.log(f"   Found {len(users)} users")
        
        # Test user ban/unban if we have a test user
        if self.test_user_id:
            # Ban user
            success, response = self.run_test(
                "Ban User",
                "PUT",
                f"admin/users/{self.test_user_id}",
                200,
                data={"status": "banned"},
                params={"admin_id": self.admin_user_id}
            )
            
            # Unban user
            success, response = self.run_test(
                "Unban User",
                "PUT",
                f"admin/users/{self.test_user_id}",
                200,
                data={"status": "active"},
                params={"admin_id": self.admin_user_id}
            )

    def test_admin_builds(self):
        """Test admin build management"""
        self.log("\n=== ADMIN BUILD MANAGEMENT TESTS ===")
        
        if not self.admin_user_id:
            self.log("❌ Skipping build management tests - no admin user")
            return
        
        # Get all builds
        success, response = self.run_test(
            "Get All Builds (Admin)",
            "GET",
            "admin/builds",
            200,
            params={"admin_id": self.admin_user_id, "page": 1, "limit": 10}
        )
        
        if success:
            builds = response.get('builds', [])
            self.log(f"   Found {len(builds)} builds")

    def test_admin_logs(self):
        """Test admin system logs"""
        self.log("\n=== ADMIN LOGS TESTS ===")
        
        if not self.admin_user_id:
            self.log("❌ Skipping logs tests - no admin user")
            return
        
        # Get system logs
        success, response = self.run_test(
            "Get System Logs",
            "GET",
            "admin/logs",
            200,
            params={"admin_id": self.admin_user_id, "page": 1, "limit": 20}
        )
        
        if success:
            logs = response.get('logs', [])
            self.log(f"   Found {len(logs)} log entries")
            if logs:
                latest_log = logs[0]
                self.log(f"   Latest log: {latest_log.get('level', 'unknown')} - {latest_log.get('message', 'no message')[:50]}")

    def test_admin_config(self):
        """Test admin configuration management"""
        self.log("\n=== ADMIN CONFIG TESTS ===")
        
        if not self.admin_user_id:
            self.log("❌ Skipping config tests - no admin user")
            return
        
        # Get current config
        success, response = self.run_test(
            "Get Platform Config",
            "GET",
            "admin/config",
            200,
            params={"admin_id": self.admin_user_id}
        )
        
        if success:
            self.log(f"   Maintenance Mode: {response.get('maintenance_mode', False)}")
            self.log(f"   Max Projects per User: {response.get('max_projects_per_user', 0)}")
            self.log(f"   Max Builds per User: {response.get('max_builds_per_user', 0)}")
        
        # Update config
        config_update = {
            "max_projects_per_user": 15,
            "max_builds_per_user": 25,
            "build_timeout_minutes": 45
        }
        
        success, response = self.run_test(
            "Update Platform Config",
            "PUT",
            "admin/config",
            200,
            data=config_update,
            params={"admin_id": self.admin_user_id}
        )

    def test_certificate_upload(self):
        """Test certificate upload endpoint"""
        self.log("\n=== CERTIFICATE TESTS ===")
        
        if not self.admin_user_id:
            self.log("❌ Skipping certificate tests - no admin user")
            return
        
        # Test certificate upload endpoint exists (without actual file)
        # This will fail but we can check if the endpoint exists
        success, response = self.run_test(
            "Certificate Upload Endpoint Check",
            "POST",
            "certificates",
            422,  # Expect validation error without file
            data={
                "project_id": "test-project-id",
                "platform": "android",
                "cert_type": "keystore",
                "name": "test-cert"
            },
            params={"user_id": self.admin_user_id}
        )

    def run_all_admin_tests(self):
        """Run all admin tests in sequence"""
        self.log("🚀 Starting NativiWeb Studio Admin API Tests")
        self.log(f"Testing against: {self.base_url}")
        
        try:
            self.setup_admin_user()
            self.create_test_user()
            self.test_admin_analytics()
            self.test_admin_users()
            self.test_admin_builds()
            self.test_admin_logs()
            self.test_admin_config()
            self.test_certificate_upload()
            
        except Exception as e:
            self.log(f"❌ Test execution error: {str(e)}")
        
        # Print summary
        self.log(f"\n📊 ADMIN TEST SUMMARY")
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {len(self.failed_tests)}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            self.log(f"\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                error_msg = failure.get('error', f"Expected {failure.get('expected')}, got {failure.get('actual')}")
                self.log(f"   - {failure['test']}: {error_msg}")
        
        return len(self.failed_tests) == 0

def main():
    tester = NativiWebAdminTester()
    success = tester.run_all_admin_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())