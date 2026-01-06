#!/usr/bin/env python3
"""
NativiWeb Studio Backend API Testing
Tests all backend endpoints for the NativiWeb platform
"""

import requests
import sys
import json
from datetime import datetime
import time

class NativiWebAPITester:
    def __init__(self, base_url="https://nativify-web.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.test_project_id = None
        self.test_build_id = None
        self.test_api_key_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add user_id to params if available
        if params is None:
            params = {}
        if self.user_id and 'user_id' not in params:
            params['user_id'] = self.user_id

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=10)

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

    def test_health_check(self):
        """Test basic health endpoints"""
        self.log("\n=== HEALTH CHECK TESTS ===")
        
        # Test root endpoint
        self.run_test("Root Endpoint", "GET", "", 200)
        
        # Test health endpoint
        self.run_test("Health Check", "GET", "health", 200)

    def test_auth_flow(self):
        """Test authentication endpoints"""
        self.log("\n=== AUTHENTICATION TESTS ===")
        
        # Test user registration
        test_user = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "name": "Test User"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'id' in response:
            self.user_id = response['id']
            self.log(f"   User ID: {self.user_id}")
        
        # Test user login
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.log(f"   Token: {self.token[:20]}...")
            
        # Test get current user (with token)
        if self.token:
            self.run_test(
                "Get Current User",
                "GET",
                "auth/me",
                200,
                params={"token": self.token}
            )

    def test_features_endpoint(self):
        """Test features endpoint"""
        self.log("\n=== FEATURES TESTS ===")
        
        success, response = self.run_test(
            "Get Available Features",
            "GET",
            "features",
            200
        )
        
        if success and isinstance(response, list):
            self.log(f"   Found {len(response)} available features")
            for feature in response[:3]:  # Show first 3
                self.log(f"   - {feature.get('name', 'Unknown')}")

    def test_projects_crud(self):
        """Test project CRUD operations"""
        self.log("\n=== PROJECTS TESTS ===")
        
        if not self.user_id:
            self.log("❌ Skipping projects tests - no user_id")
            return
        
        # Create project
        project_data = {
            "name": "Test Project",
            "web_url": "https://example.com",
            "description": "Test project description",
            "platform": ["android", "ios"]
        }
        
        success, response = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data=project_data
        )
        
        if success and 'id' in response:
            self.test_project_id = response['id']
            self.log(f"   Project ID: {self.test_project_id}")
        
        # Get all projects
        self.run_test(
            "Get All Projects",
            "GET",
            "projects",
            200
        )
        
        # Get specific project
        if self.test_project_id:
            self.run_test(
                "Get Project Details",
                "GET",
                f"projects/{self.test_project_id}",
                200
            )
            
            # Update project
            update_data = {
                "name": "Updated Test Project",
                "description": "Updated description"
            }
            
            self.run_test(
                "Update Project",
                "PUT",
                f"projects/{self.test_project_id}",
                200,
                data=update_data
            )

    def test_builds_flow(self):
        """Test build operations"""
        self.log("\n=== BUILDS TESTS ===")
        
        if not self.user_id or not self.test_project_id:
            self.log("❌ Skipping builds tests - missing user_id or project_id")
            return
        
        # Create build
        build_data = {
            "project_id": self.test_project_id,
            "platform": "android",
            "build_type": "debug"
        }
        
        success, response = self.run_test(
            "Create Build",
            "POST",
            "builds",
            200,
            data=build_data
        )
        
        if success and 'id' in response:
            self.test_build_id = response['id']
            self.log(f"   Build ID: {self.test_build_id}")
        
        # Get all builds
        self.run_test(
            "Get All Builds",
            "GET",
            "builds",
            200
        )
        
        # Get specific build
        if self.test_build_id:
            self.run_test(
                "Get Build Details",
                "GET",
                f"builds/{self.test_build_id}",
                200
            )
            
            # Wait a moment for build to process
            time.sleep(2)
            
            # Check build status again
            success, response = self.run_test(
                "Check Build Status",
                "GET",
                f"builds/{self.test_build_id}",
                200
            )
            
            if success:
                status = response.get('status', 'unknown')
                progress = response.get('progress', 0)
                self.log(f"   Build Status: {status} ({progress}%)")

    def test_api_keys(self):
        """Test API keys management"""
        self.log("\n=== API KEYS TESTS ===")
        
        if not self.user_id:
            self.log("❌ Skipping API keys tests - no user_id")
            return
        
        # Create API key
        key_data = {
            "name": "Test API Key",
            "permissions": ["read", "write"]
        }
        
        success, response = self.run_test(
            "Create API Key",
            "POST",
            "api-keys",
            200,
            data=key_data
        )
        
        if success and 'id' in response:
            self.test_api_key_id = response['id']
            self.log(f"   API Key ID: {self.test_api_key_id}")
            if 'key' in response:
                self.log(f"   API Key: {response['key'][:20]}...")
        
        # Get all API keys
        self.run_test(
            "Get All API Keys",
            "GET",
            "api-keys",
            200
        )

    def test_stats(self):
        """Test user stats"""
        self.log("\n=== STATS TESTS ===")
        
        if not self.user_id:
            self.log("❌ Skipping stats tests - no user_id")
            return
        
        success, response = self.run_test(
            "Get User Stats",
            "GET",
            "stats",
            200
        )
        
        if success:
            self.log(f"   Projects: {response.get('projects', 0)}")
            self.log(f"   Total Builds: {response.get('total_builds', 0)}")
            self.log(f"   Successful Builds: {response.get('successful_builds', 0)}")
            self.log(f"   API Keys: {response.get('api_keys', 0)}")

    def test_generator_endpoints(self):
        """Test code generation endpoints"""
        self.log("\n=== GENERATOR TESTS ===")
        
        if not self.user_id or not self.test_project_id:
            self.log("❌ Skipping generator tests - missing user_id or project_id")
            return
        
        # Test SDK generation
        self.run_test(
            "Generate SDK",
            "GET",
            f"generator/sdk/{self.test_project_id}",
            200
        )
        
        # Test Android template generation
        self.run_test(
            "Generate Android Template",
            "GET",
            f"generator/template/{self.test_project_id}/android",
            200
        )
        
        # Test iOS template generation
        self.run_test(
            "Generate iOS Template",
            "GET",
            f"generator/template/{self.test_project_id}/ios",
            200
        )

    def cleanup(self):
        """Clean up test data"""
        self.log("\n=== CLEANUP ===")
        
        # Delete API key
        if self.test_api_key_id and self.user_id:
            self.run_test(
                "Delete API Key",
                "DELETE",
                f"api-keys/{self.test_api_key_id}",
                200
            )
        
        # Delete project (this should also clean up builds)
        if self.test_project_id and self.user_id:
            self.run_test(
                "Delete Project",
                "DELETE",
                f"projects/{self.test_project_id}",
                200
            )
        
        # Logout
        if self.token:
            self.run_test(
                "Logout",
                "POST",
                "auth/logout",
                200,
                params={"token": self.token}
            )

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting NativiWeb Studio API Tests")
        self.log(f"Testing against: {self.base_url}")
        
        try:
            self.test_health_check()
            self.test_auth_flow()
            self.test_features_endpoint()
            self.test_projects_crud()
            self.test_builds_flow()
            self.test_api_keys()
            self.test_stats()
            self.test_generator_endpoints()
            
        finally:
            self.cleanup()
        
        # Print summary
        self.log(f"\n📊 TEST SUMMARY")
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
    tester = NativiWebAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())