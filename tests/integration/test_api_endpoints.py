"""
Integration tests for API endpoints
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint returns 200"""
        response = test_client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
    
    def test_health_endpoint(self, test_client):
        """Test health endpoint returns healthy status"""
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.integration
class TestFeaturesEndpoint:
    """Test features endpoint"""
    
    def test_get_features(self, test_client):
        """Test getting available features"""
        response = test_client.get("/api/features")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check that features have required fields
        if len(data) > 0:
            feature = data[0]
            assert "id" in feature
            assert "name" in feature
            assert "description" in feature


@pytest.mark.integration
@pytest.mark.requires_auth
class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""
    
    @patch('main.get_current_user')
    @patch('main.get_supabase_client')
    def test_get_projects_requires_auth(self, mock_get_client, mock_get_user, test_client, test_user_data):
        """Test that projects endpoint requires authentication"""
        # Without auth
        response = test_client.get("/api/projects")
        assert response.status_code == 401
        
        # With auth (mocked)
        mock_get_user.return_value = test_user_data
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_get_client.return_value = mock_client
        
        # This would work with proper dependency injection
        # response = test_client.get("/api/projects", headers={"Authorization": f"Bearer {token}"})
        # assert response.status_code == 200

