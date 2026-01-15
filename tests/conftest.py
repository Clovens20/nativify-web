"""
Pytest configuration and fixtures for NativiWeb Studio tests
"""
import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["SUPABASE_URL"] = os.environ.get("TEST_SUPABASE_URL", "https://test.supabase.co")
os.environ["SUPABASE_ANON_KEY"] = os.environ.get("TEST_SUPABASE_ANON_KEY", "test_anon_key")
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.environ.get("TEST_SUPABASE_SERVICE_KEY", "test_service_key")


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    mock_client = Mock()
    mock_client.table.return_value = mock_client
    mock_client.select.return_value = mock_client
    mock_client.insert.return_value = mock_client
    mock_client.update.return_value = mock_client
    mock_client.delete.return_value = mock_client
    mock_client.eq.return_value = mock_client
    mock_client.execute.return_value = Mock(data=[])
    return mock_client


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app"""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_jwt_token():
    """Generate a mock JWT token for testing"""
    import jwt
    from datetime import datetime, timedelta, timezone
    
    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    
    # Use a test secret
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return token


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "name": "Test User",
        "role": "user",
        "status": "active"
    }


@pytest.fixture
def test_project_data():
    """Test project data"""
    return {
        "id": "test-project-id",
        "user_id": "test-user-id",
        "name": "Test Project",
        "web_url": "https://example.com",
        "description": "Test description",
        "platform": ["android", "ios"],
        "features": [],
        "status": "active"
    }

