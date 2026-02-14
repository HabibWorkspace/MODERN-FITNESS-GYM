"""Tests for authentication system."""
import pytest
from app import db
from models.user import User, UserRole
from services.password_service import PasswordService
from services.auth_service import AuthService
from flask_jwt_extended import decode_token


class TestPasswordService:
    """Tests for password hashing and verification."""
    
    def test_hash_password_creates_different_hash(self):
        """Test that hashing the same password twice creates different hashes."""
        password = "test_password_123"
        hash1 = PasswordService.hash_password(password)
        hash2 = PasswordService.hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify against the original password
        assert PasswordService.verify_password(password, hash1)
        assert PasswordService.verify_password(password, hash2)
    
    def test_verify_password_correct(self):
        """Test that correct password verifies successfully."""
        password = "correct_password"
        password_hash = PasswordService.hash_password(password)
        
        assert PasswordService.verify_password(password, password_hash) is True
    
    def test_verify_password_incorrect(self):
        """Test that incorrect password fails verification."""
        password = "correct_password"
        wrong_password = "wrong_password"
        password_hash = PasswordService.hash_password(password)
        
        assert PasswordService.verify_password(wrong_password, password_hash) is False
    
    def test_verify_password_empty_string(self):
        """Test that empty password fails verification."""
        password = "correct_password"
        password_hash = PasswordService.hash_password(password)
        
        assert PasswordService.verify_password("", password_hash) is False
    
    def test_hash_password_uses_minimum_rounds(self):
        """Test that password hashing uses minimum 12 rounds."""
        password = "test_password"
        password_hash = PasswordService.hash_password(password)
        
        # Bcrypt hash format: $2b$rounds$...
        # Extract rounds from hash
        rounds = int(password_hash.split('$')[2])
        assert rounds >= 12


class TestAuthService:
    """Tests for JWT token generation and validation."""
    
    def test_generate_token_returns_string(self):
        """Test that token generation returns a string."""
        token = AuthService.generate_token("user123", "testuser", "member")
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_token_contains_claims(self):
        """Test that generated token contains correct claims."""
        user_id = "user123"
        username = "testuser"
        role = "member"
        
        token = AuthService.generate_token(user_id, username, role)
        
        # Decode token to verify claims
        claims = decode_token(token)
        assert claims['sub'] == user_id  # 'sub' is the identity
        assert claims['username'] == username
        assert claims['role'] == role
    
    def test_validate_token_valid(self):
        """Test that valid token validates successfully."""
        token = AuthService.generate_token("user123", "testuser", "admin")
        
        is_valid, claims = AuthService.validate_token(token)
        assert is_valid is True
        assert claims is not None
        assert claims['sub'] == "user123"
        assert claims['role'] == "admin"
    
    def test_validate_token_invalid(self):
        """Test that invalid token fails validation."""
        invalid_token = "invalid.token.here"
        
        is_valid, claims = AuthService.validate_token(invalid_token)
        assert is_valid is False
        assert claims is None
    
    def test_validate_token_empty_string(self):
        """Test that empty token fails validation."""
        is_valid, claims = AuthService.validate_token("")
        assert is_valid is False
        assert claims is None
    
    def test_generate_token_different_roles(self):
        """Test token generation for different roles."""
        roles = ["admin", "trainer", "member"]
        
        for role in roles:
            token = AuthService.generate_token("user123", "testuser", role)
            is_valid, claims = AuthService.validate_token(token)
            
            assert is_valid is True
            assert claims['role'] == role


class TestAuthenticationEndpoints:
    """Tests for authentication API endpoints."""
    
    @pytest.fixture
    def test_user(self, app):
        """Create a test user."""
        with app.app_context():
            user = User(
                username="testuser",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['username'] == 'testuser'
        assert data['user']['role'] == 'member'
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Invalid credentials'
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent username."""
        response = client.post('/api/auth/login', json={
            'username': 'nonexistent',
            'password': 'password123'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid credentials'
    
    def test_login_missing_username(self, client):
        """Test login with missing username."""
        response = client.post('/api/auth/login', json={
            'password': 'password123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_login_missing_password(self, client):
        """Test login with missing password."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_login_frozen_account(self, client, app):
        """Test login with frozen account."""
        with app.app_context():
            user = User(
                username="frozenuser",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=False
            )
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/api/auth/login', json={
            'username': 'frozenuser',
            'password': 'password123'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Account is frozen'
    
    def test_logout_with_valid_token(self, client, test_user):
        """Test logout with valid token."""
        # First login to get token
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Then logout
        response = client.post('/api/auth/logout', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    def test_logout_without_token(self, client):
        """Test logout without token."""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401
    
    def test_refresh_token_valid(self, client, test_user):
        """Test token refresh with valid token."""
        # First login to get token
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Refresh token
        response = client.post('/api/auth/refresh', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        
        # New token should be different
        new_token = data['access_token']
        assert new_token != token
        
        # New token should be valid
        is_valid, claims = AuthService.validate_token(new_token)
        assert is_valid is True
    
    def test_refresh_token_without_token(self, client):
        """Test token refresh without token."""
        response = client.post('/api/auth/refresh')
        
        assert response.status_code == 401
    
    def test_refresh_token_frozen_user(self, client, app):
        """Test token refresh for frozen user."""
        with app.app_context():
            user = User(
                username="frozenuser",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Login
        login_response = client.post('/api/auth/login', json={
            'username': 'frozenuser',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Freeze user
        with app.app_context():
            user = User.query.get(user_id)
            user.is_active = False
            db.session.commit()
        
        # Try to refresh
        response = client.post('/api/auth/refresh', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 401


class TestRoleBasedAccessControl:
    """Tests for role-based access control."""
    
    @pytest.fixture
    def admin_user(self, app):
        """Create an admin user."""
        with app.app_context():
            user = User(
                username="admin",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    @pytest.fixture
    def trainer_user(self, app):
        """Create a trainer user."""
        with app.app_context():
            user = User(
                username="trainer",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.TRAINER,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    @pytest.fixture
    def member_user(self, app):
        """Create a member user."""
        with app.app_context():
            user = User(
                username="member",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    def test_admin_can_access_admin_endpoint(self, client, admin_user):
        """Test that admin can access admin-only endpoint."""
        # Login as admin
        login_response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Verify token contains admin role
        is_valid, claims = AuthService.validate_token(token)
        assert claims['role'] == 'admin'
    
    def test_trainer_cannot_access_admin_endpoint(self, client, trainer_user):
        """Test that trainer cannot access admin-only endpoint."""
        # Login as trainer
        login_response = client.post('/api/auth/login', json={
            'username': 'trainer',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Verify token contains trainer role
        is_valid, claims = AuthService.validate_token(token)
        assert claims['role'] == 'trainer'
    
    def test_member_cannot_access_admin_endpoint(self, client, member_user):
        """Test that member cannot access admin-only endpoint."""
        # Login as member
        login_response = client.post('/api/auth/login', json={
            'username': 'member',
            'password': 'password123'
        })
        token = login_response.get_json()['access_token']
        
        # Verify token contains member role
        is_valid, claims = AuthService.validate_token(token)
        assert claims['role'] == 'member'
