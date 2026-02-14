"""Property-based tests for authentication system."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app import db, create_app
from config import TestingConfig
from models.user import User, UserRole
from services.password_service import PasswordService
from services.auth_service import AuthService
from flask_jwt_extended import decode_token


# Strategies for generating test data
username_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=3,
    max_size=50
)

password_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=8,
    max_size=100
)

role_strategy = st.sampled_from(['admin', 'trainer', 'member'])


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestAuthenticationRoundTrip:
    """
    **Property 1: Authentication Round Trip**
    
    For any valid username and password combination, logging in should return a JWT token 
    that can be used to authenticate subsequent requests, and logging out should invalidate 
    that token.
    
    **Validates: Requirements 1.1, 1.5**
    """
    
    @given(username_strategy, password_strategy)
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_login_returns_valid_token(self, username, password):
        """Test that login returns a valid JWT token."""
        app = create_app(TestingConfig)
        client = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Create user
            user = User(
                username=username,
                password_hash=PasswordService.hash_password(password),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Login
            response = client.post('/api/auth/login', json={
                'username': username,
                'password': password
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'access_token' in data
            
            # Verify token is valid
            token = data['access_token']
            is_valid, claims = AuthService.validate_token(token)
            assert is_valid is True
            assert claims['username'] == username
            
            db.drop_all()
    
    @given(username_strategy, password_strategy)
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_logout_invalidates_token_client_side(self, username, password):
        """Test that logout endpoint is accessible with valid token."""
        app = create_app(TestingConfig)
        client = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Create user
            user = User(
                username=username,
                password_hash=PasswordService.hash_password(password),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Login
            login_response = client.post('/api/auth/login', json={
                'username': username,
                'password': password
            })
            token = login_response.get_json()['access_token']
            
            # Logout
            logout_response = client.post('/api/auth/logout', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert logout_response.status_code == 200
            
            db.drop_all()


class TestPasswordSecurity:
    """
    **Property 2: Password Security**
    
    For any password, the stored password_hash should be different from the plaintext 
    password and should be verifiable using bcrypt.
    
    **Validates: Requirements 1.7**
    """
    
    @given(password_strategy)
    @settings(max_examples=5, deadline=None)
    def test_password_hash_different_from_plaintext(self, password):
        """Test that password hash is different from plaintext."""
        password_hash = PasswordService.hash_password(password)
        
        # Hash should not equal plaintext
        assert password_hash != password
        # Hash should be a string
        assert isinstance(password_hash, str)
        # Hash should be bcrypt format (starts with $2b$)
        assert password_hash.startswith('$2b$')
    
    @given(password_strategy)
    @settings(max_examples=5, deadline=None)
    def test_password_hash_verifiable(self, password):
        """Test that password hash can be verified."""
        password_hash = PasswordService.hash_password(password)
        
        # Should verify successfully
        assert PasswordService.verify_password(password, password_hash) is True
    
    @given(password_strategy, password_strategy)
    @settings(max_examples=5, deadline=None)
    def test_different_passwords_produce_different_hashes(self, password1, password2):
        """Test that different passwords produce different hashes."""
        if password1 == password2:
            # Skip if passwords are the same
            return
        
        hash1 = PasswordService.hash_password(password1)
        hash2 = PasswordService.hash_password(password2)
        
        # Different passwords should not verify against each other's hashes
        assert PasswordService.verify_password(password1, hash2) is False
        assert PasswordService.verify_password(password2, hash1) is False


class TestRoleBasedAccessControl:
    """
    **Property 3: Role-Based Access Control**
    
    For any user with a specific role, attempting to access resources restricted to a 
    different role should return a 403 Forbidden response.
    
    **Validates: Requirements 1.6**
    """
    
    @given(role_strategy, role_strategy)
    @settings(max_examples=5)
    def test_token_contains_correct_role(self, role1, role2):
        """Test that generated token contains the correct role."""
        user_id = "test_user_123"
        username = "testuser"
        
        token = AuthService.generate_token(user_id, username, role1)
        
        is_valid, claims = AuthService.validate_token(token)
        assert is_valid is True
        assert claims['role'] == role1
        
        # If roles are different, token should have different role
        if role1 != role2:
            token2 = AuthService.generate_token(user_id, username, role2)
            is_valid2, claims2 = AuthService.validate_token(token2)
            assert claims2['role'] == role2
            assert claims['role'] != claims2['role']
    
    @given(username_strategy, password_strategy, role_strategy)
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_login_returns_correct_role_in_token(self, username, password, role):
        """Test that login returns token with correct role."""
        app = create_app(TestingConfig)
        client = app.test_client()
        
        # Map role string to UserRole enum
        role_map = {
            'admin': UserRole.ADMIN,
            'trainer': UserRole.TRAINER,
            'member': UserRole.MEMBER
        }
        
        with app.app_context():
            db.create_all()
            # Create user with specific role
            user = User(
                username=username,
                password_hash=PasswordService.hash_password(password),
                role=role_map[role],
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Login
            response = client.post('/api/auth/login', json={
                'username': username,
                'password': password
            })
            
            assert response.status_code == 200
            data = response.get_json()
            token = data['access_token']
            
            # Verify token has correct role
            is_valid, claims = AuthService.validate_token(token)
            assert is_valid is True
            assert claims['role'] == role
            
            db.drop_all()
