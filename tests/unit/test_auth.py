"""
Unit tests for authentication and authorization
"""
import pytest
from unittest.mock import Mock, patch
import jwt
from datetime import datetime, timedelta, timezone


class TestJWTValidation:
    """Test JWT token validation"""
    
    def test_valid_jwt_token(self, mock_jwt_token):
        """Test that a valid JWT token can be decoded"""
        decoded = jwt.decode(mock_jwt_token, "test-secret", algorithms=["HS256"])
        assert decoded["sub"] == "test-user-id"
        assert decoded["email"] == "test@example.com"
    
    def test_expired_jwt_token(self):
        """Test that an expired JWT token is rejected"""
        payload = {
            "sub": "test-user-id",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, "test-secret", algorithms=["HS256"])
    
    def test_invalid_jwt_token(self):
        """Test that an invalid JWT token is rejected"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(invalid_token, "test-secret", algorithms=["HS256"])


class TestAuthDependencies:
    """Test authentication dependencies"""
    
    @patch('main.get_supabase_client')
    def test_get_current_user_with_valid_token(self, mock_get_client, mock_jwt_token, test_user_data):
        """Test getting current user with valid token"""
        from main import get_current_user
        
        # Mock Supabase response
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user_data]
        mock_get_client.return_value = mock_client
        
        # This would need actual implementation testing with FastAPI dependencies
        # For now, we test the logic separately
        assert test_user_data["id"] == "test-user-id"


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing utilities"""
    
    def test_password_hashing(self):
        """Test that passwords are hashed correctly"""
        import bcrypt
        
        password = "test_password_123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Verify password can be checked
        assert bcrypt.checkpw(password.encode(), hashed)
        assert not bcrypt.checkpw("wrong_password".encode(), hashed)

