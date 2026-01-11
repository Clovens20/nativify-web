"""
Unit tests for input validation
"""
import pytest
from pydantic import ValidationError
from main import UserCreate, UserLogin, ProjectCreate, BuildCreate


@pytest.mark.unit
class TestUserValidation:
    """Test user input validation"""
    
    def test_valid_user_create(self):
        """Test creating a user with valid data"""
        user = UserCreate(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"
    
    def test_invalid_email(self):
        """Test that invalid email is rejected"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="password123",
                name="Test User"
            )
    
    def test_short_password(self):
        """Test that short password is accepted (validation in backend)"""
        # Pydantic doesn't validate password length, but we can test it
        user = UserCreate(
            email="test@example.com",
            password="short",
            name="Test User"
        )
        # Password validation happens in the endpoint, not in the model
        assert user.password == "short"


@pytest.mark.unit
class TestProjectValidation:
    """Test project input validation"""
    
    def test_valid_project_create(self):
        """Test creating a project with valid data"""
        project = ProjectCreate(
            name="Test Project",
            web_url="https://example.com",
            description="Test description",
            platform=["android", "ios"]
        )
        assert project.name == "Test Project"
        assert project.web_url == "https://example.com"
        assert "android" in project.platform
    
    def test_invalid_url(self):
        """Test that invalid URL is handled"""
        # Pydantic URL validation
        with pytest.raises(ValidationError):
            ProjectCreate(
                name="Test Project",
                web_url="not-a-url",
                platform=["android"]
            )

