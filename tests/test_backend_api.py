"""
Backend API Tests for NativiWeb Studio
Tests: Health check, Features endpoint, Root status
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nativify.preview.emergentagent.com').rstrip('/')


class TestHealthEndpoints:
    """Health and status endpoint tests"""
    
    def test_health_check(self):
        """Test GET /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print(f"Health check passed: {data}")
    
    def test_root_status(self):
        """Test GET /api/ returns operational status"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "operational"
        assert "NativiWeb Studio API" in data["message"]
        print(f"Root status passed: {data}")


class TestFeaturesEndpoint:
    """Features endpoint tests"""
    
    def test_get_features(self):
        """Test GET /api/features returns list of native features"""
        response = requests.get(f"{BASE_URL}/api/features")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify feature structure
        first_feature = data[0]
        assert "id" in first_feature
        assert "name" in first_feature
        assert "enabled" in first_feature
        assert "config" in first_feature
        
        # Verify expected features exist
        feature_ids = [f["id"] for f in data]
        expected_features = ["push_notifications", "camera", "geolocation", "biometrics"]
        for expected in expected_features:
            assert expected in feature_ids, f"Expected feature '{expected}' not found"
        
        print(f"Features endpoint passed: {len(data)} features returned")
        print(f"Feature IDs: {feature_ids}")


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("Login with invalid credentials correctly returns 401")
    
    def test_register_missing_fields(self):
        """Test register with missing fields returns error"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "test@test.com"
            # Missing password and name
        })
        assert response.status_code == 422  # Validation error
        print("Register with missing fields correctly returns 422")


class TestProjectEndpoints:
    """Project endpoint tests (without auth)"""
    
    def test_get_projects_requires_user_id(self):
        """Test GET /api/projects requires user_id parameter"""
        response = requests.get(f"{BASE_URL}/api/projects")
        # Should return 422 (validation error) since user_id is required
        assert response.status_code == 422
        print("Projects endpoint correctly requires user_id")


class TestBuildEndpoints:
    """Build endpoint tests (without auth)"""
    
    def test_get_builds_requires_user_id(self):
        """Test GET /api/builds requires user_id parameter"""
        response = requests.get(f"{BASE_URL}/api/builds")
        # Should return 422 (validation error) since user_id is required
        assert response.status_code == 422
        print("Builds endpoint correctly requires user_id")


class TestAPIKeyEndpoints:
    """API Key endpoint tests (without auth)"""
    
    def test_get_api_keys_requires_user_id(self):
        """Test GET /api/api-keys requires user_id parameter"""
        response = requests.get(f"{BASE_URL}/api/api-keys")
        # Should return 422 (validation error) since user_id is required
        assert response.status_code == 422
        print("API Keys endpoint correctly requires user_id")


class TestAdminEndpoints:
    """Admin endpoint tests (without auth)"""
    
    def test_admin_users_requires_admin(self):
        """Test GET /api/admin/users requires admin access"""
        response = requests.get(f"{BASE_URL}/api/admin/users")
        # Should return 422 (validation error) since admin_id is required
        assert response.status_code == 422
        print("Admin users endpoint correctly requires admin_id")
    
    def test_admin_analytics_requires_admin(self):
        """Test GET /api/admin/analytics requires admin access"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        # Should return 422 (validation error) since admin_id is required
        assert response.status_code == 422
        print("Admin analytics endpoint correctly requires admin_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
