"""Tests for admin member management endpoints."""
import pytest
from app import db
from models.user import User, UserRole
from models.member_profile import MemberProfile
from models.package import Package
from services.password_service import PasswordService
from services.auth_service import AuthService
from datetime import datetime, timedelta


class TestMemberCRUDEndpoints:
    """Tests for member CRUD endpoints."""
    
    @pytest.fixture
    def admin_token(self, client, app):
        """Create admin user and return token."""
        with app.app_context():
            user = User(
                username="admin",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'password123'
        })
        return response.get_json()['access_token']
    
    @pytest.fixture
    def test_package(self, app):
        """Create a test package."""
        with app.app_context():
            package = Package(
                name="Basic Package",
                duration_days=30,
                price=50.00,
                description="Basic gym membership",
                is_active=True
            )
            db.session.add(package)
            db.session.commit()
            return package.id
    
    def test_create_member_success(self, client, admin_token):
        """Test successful member creation."""
        response = client.post('/api/admin/members', 
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'newmember',
                'password': 'password123',
                'phone': '1234567890',
                'cnic': '12345-1234567-1',
                'email': 'member@example.com',
                'admission_fee_paid': False
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['phone'] == '1234567890'
        assert data['cnic'] == '12345-1234567-1'
        assert data['email'] == 'member@example.com'
        assert data['admission_fee_paid'] is False
        assert data['is_frozen'] is False
    
    def test_create_member_with_package(self, client, admin_token, test_package):
        """Test member creation with package assignment."""
        response = client.post('/api/admin/members',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'newmember',
                'password': 'password123',
                'phone': '1234567890',
                'cnic': '12345-1234567-1',
                'email': 'member@example.com',
                'current_package_id': test_package,
                'admission_fee_paid': True
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['current_package_id'] == test_package
        assert data['admission_fee_paid'] is True
        assert data['package_start_date'] is not None
        assert data['package_expiry_date'] is not None
    
    def test_create_member_missing_required_fields(self, client, admin_token):
        """Test member creation with missing required fields."""
        response = client.post('/api/admin/members',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'newmember',
                'password': 'password123'
                # Missing phone, cnic, email
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_member_duplicate_username(self, client, admin_token, app):
        """Test member creation with duplicate username."""
        # Create first member
        with app.app_context():
            user = User(
                username="existinguser",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        # Try to create another with same username
        response = client.post('/api/admin/members',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'existinguser',
                'password': 'password123',
                'phone': '1234567890',
                'cnic': '12345-1234567-1',
                'email': 'member@example.com'
            }
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'Username already exists' in data['error']
    
    def test_create_member_duplicate_phone(self, client, admin_token, app):
        """Test member creation with duplicate phone."""
        # Create first member
        with app.app_context():
            user = User(
                username="member1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            member = MemberProfile(
                user_id=user.id,
                phone='1234567890',
                cnic='12345-1234567-1',
                email='member1@example.com'
            )
            db.session.add(member)
            db.session.commit()
        
        # Try to create another with same phone
        response = client.post('/api/admin/members',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'member2',
                'password': 'password123',
                'phone': '1234567890',
                'cnic': '12345-1234567-2',
                'email': 'member2@example.com'
            }
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'Phone already exists' in data['error']
    
    def test_create_member_duplicate_cnic(self, client, admin_token, app):
        """Test member creation with duplicate CNIC."""
        # Create first member
        with app.app_context():
            user = User(
                username="member1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            member = MemberProfile(
                user_id=user.id,
                phone='1111111111',
                cnic='12345-1234567-1',
                email='member1@example.com'
            )
            db.session.add(member)
            db.session.commit()
        
        # Try to create another with same CNIC
        response = client.post('/api/admin/members',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'member2',
                'password': 'password123',
                'phone': '2222222222',
                'cnic': '12345-1234567-1',
                'email': 'member2@example.com'
            }
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'CNIC already exists' in data['error']
    
    def test_create_member_duplicate_email(self, client, admin_token, app):
        """Test member creation with duplicate email."""
        # Create first member
        with app.app_context():
            user = User(
                username="member1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            member = MemberProfile(
                user_id=user.id,
                phone='1111111111',
                cnic='12345-1234567-1',
                email='member@example.com'
            )
            db.session.add(member)
            db.session.commit()
        
        # Try to create another with same email
        response = client.post('/api/admin/members',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'member2',
                'password': 'password123',
                'phone': '2222222222',
                'cnic': '12345-1234567-2',
                'email': 'member@example.com'
            }
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'Email already exists' in data['error']
    
    def test_list_members_empty(self, client, admin_token):
        """Test listing members when none exist."""
        response = client.get('/api/admin/members',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['members'] == []
        assert data['total'] == 0
        assert data['page'] == 1
        assert data['per_page'] == 20
    
    def test_list_members_with_pagination(self, client, admin_token, app):
        """Test listing members with pagination."""
        # Create multiple members
        with app.app_context():
            for i in range(5):
                user = User(
                    username=f"member{i}",
                    password_hash=PasswordService.hash_password("password123"),
                    role=UserRole.MEMBER,
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()
                
                member = MemberProfile(
                    user_id=user.id,
                    phone=f'111111111{i}',
                    cnic=f'12345-1234567-{i}',
                    email=f'member{i}@example.com'
                )
                db.session.add(member)
            db.session.commit()
        
        # Get first page
        response = client.get('/api/admin/members?page=1&per_page=2',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['members']) == 2
        assert data['total'] == 5
        assert data['page'] == 1
        assert data['per_page'] == 2
    
    def test_get_member_success(self, client, admin_token, app):
        """Test getting member details."""
        # Create member
        with app.app_context():
            user = User(
                username="member1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            member = MemberProfile(
                user_id=user.id,
                phone='1234567890',
                cnic='12345-1234567-1',
                email='member@example.com'
            )
            db.session.add(member)
            db.session.commit()
            member_id = member.id
        
        response = client.get(f'/api/admin/members/{member_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['phone'] == '1234567890'
        assert data['cnic'] == '12345-1234567-1'
        assert data['email'] == 'member@example.com'
    
    def test_get_member_not_found(self, client, admin_token):
        """Test getting nonexistent member."""
        response = client.get('/api/admin/members/nonexistent-id',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'Member not found' in data['error']
    
    def test_update_member_success(self, client, admin_token, app):
        """Test updating member information."""
        # Create member
        with app.app_context():
            user = User(
                username="member1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            member = MemberProfile(
                user_id=user.id,
                phone='1234567890',
                cnic='12345-1234567-1',
                email='member@example.com'
            )
            db.session.add(member)
            db.session.commit()
            member_id = member.id
        
        response = client.put(f'/api/admin/members/{member_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'phone': '9876543210',
                'email': 'newemail@example.com'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['phone'] == '9876543210'
        assert data['email'] == 'newemail@example.com'
        assert data['cnic'] == '12345-1234567-1'  # Unchanged
    
    def test_update_member_with_package(self, client, admin_token, app, test_package):
        """Test updating member with package assignment."""
        # Create member
        with app.app_context():
            user = User(
                username="member1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            member = MemberProfile(
                user_id=user.id,
                phone='1234567890',
                cnic='12345-1234567-1',
                email='member@example.com'
            )
            db.session.add(member)
            db.session.commit()
            member_id = member.id
        
        response = client.put(f'/api/admin/members/{member_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'current_package_id': test_package,
                'admission_fee_paid': True
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['current_package_id'] == test_package
        assert data['admission_fee_paid'] is True
        assert data['package_start_date'] is not None
        assert data['package_expiry_date'] is not None
    
    def test_delete_member_success(self, client, admin_token, app):
        """Test deleting a member."""
        # Create member
        with app.app_context():
            user = User(
                username="member1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            member = MemberProfile(
                user_id=user.id,
                phone='1234567890',
                cnic='12345-1234567-1',
                email='member@example.com'
            )
            db.session.add(member)
            db.session.commit()
            member_id = member.id
        
        response = client.delete(f'/api/admin/members/{member_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'Member deleted successfully' in data['message']
        
        # Verify member is deleted
        with app.app_context():
            deleted_member = MemberProfile.query.get(member_id)
            assert deleted_member is None
    
    def test_delete_member_not_found(self, client, admin_token):
        """Test deleting nonexistent member."""
        response = client.delete('/api/admin/members/nonexistent-id',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'Member not found' in data['error']


class TestMemberSearchEndpoints:
    """Tests for member search endpoints."""
    
    @pytest.fixture
    def admin_token(self, client, app):
        """Create admin user and return token."""
        with app.app_context():
            user = User(
                username="admin",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'password123'
        })
        return response.get_json()['access_token']
    
    @pytest.fixture
    def test_members(self, app):
        """Create test members for search."""
        with app.app_context():
            members_data = [
                {'username': 'member1', 'phone': '1111111111', 'cnic': '11111-1111111-1', 'email': 'member1@example.com'},
                {'username': 'member2', 'phone': '2222222222', 'cnic': '22222-2222222-2', 'email': 'member2@example.com'},
                {'username': 'member3', 'phone': '3333333333', 'cnic': '33333-3333333-3', 'email': 'member3@example.com'},
            ]
            
            for data in members_data:
                user = User(
                    username=data['username'],
                    password_hash=PasswordService.hash_password("password123"),
                    role=UserRole.MEMBER,
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()
                
                member = MemberProfile(
                    user_id=user.id,
                    phone=data['phone'],
                    cnic=data['cnic'],
                    email=data['email']
                )
                db.session.add(member)
            db.session.commit()
    
    def test_search_by_phone(self, client, admin_token, test_members):
        """Test searching members by phone."""
        response = client.get('/api/admin/members/search?phone=1111111111',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['members']) == 1
        assert data['members'][0]['phone'] == '1111111111'
    
    def test_search_by_cnic(self, client, admin_token, test_members):
        """Test searching members by CNIC."""
        response = client.get('/api/admin/members/search?cnic=22222-2222222-2',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['members']) == 1
        assert data['members'][0]['cnic'] == '22222-2222222-2'
    
    def test_search_by_email(self, client, admin_token, test_members):
        """Test searching members by email."""
        response = client.get('/api/admin/members/search?email=member3@example.com',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['members']) == 1
        assert data['members'][0]['email'] == 'member3@example.com'
    
    def test_search_no_parameters(self, client, admin_token):
        """Test search without parameters."""
        response = client.get('/api/admin/members/search',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'At least one search parameter required' in data['error']
    
    def test_search_partial_match(self, client, admin_token, test_members):
        """Test search with partial match."""
        response = client.get('/api/admin/members/search?phone=111',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['members']) == 1
        assert '1111111111' in data['members'][0]['phone']


class TestMemberAccountManagementEndpoints:
    """Tests for member account management endpoints."""
    
    @pytest.fixture
    def admin_token(self, client, app):
        """Create admin user and return token."""
        with app.app_context():
            user = User(
                username="admin",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'password123'
        })
        return response.get_json()['access_token']
    
    @pytest.fixture
    def test_member(self, app):
        """Create a test member."""
        with app.app_context():
            user = User(
                username="member1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            member = MemberProfile(
                user_id=user.id,
                phone='1234567890',
                cnic='12345-1234567-1',
                email='member@example.com',
                admission_fee_paid=False,
                is_frozen=False
            )
            db.session.add(member)
            db.session.commit()
            return member.id
    
    def test_freeze_member_success(self, client, admin_token, test_member):
        """Test freezing a member account."""
        response = client.post(f'/api/admin/members/{test_member}/freeze',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_frozen'] is True
        assert 'Member account frozen' in data['message']
    
    def test_freeze_member_not_found(self, client, admin_token):
        """Test freezing nonexistent member."""
        response = client.post('/api/admin/members/nonexistent-id/freeze',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'Member not found' in data['error']
    
    def test_mark_admission_fee_paid_success(self, client, admin_token, test_member):
        """Test marking admission fee as paid."""
        response = client.post(f'/api/admin/members/{test_member}/admission-fee',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['admission_fee_paid'] is True
        assert 'Admission fee marked as paid' in data['message']
        assert 'timestamp' in data
    
    def test_mark_admission_fee_paid_not_found(self, client, admin_token):
        """Test marking admission fee for nonexistent member."""
        response = client.post('/api/admin/members/nonexistent-id/admission-fee',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'Member not found' in data['error']
    
    def test_frozen_member_cannot_login(self, client, admin_token, test_member, app):
        """Test that frozen member cannot login."""
        # Freeze member
        client.post(f'/api/admin/members/{test_member}/freeze',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        # Try to login
        response = client.post('/api/auth/login', json={
            'username': 'member1',
            'password': 'password123'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Account is frozen' in data['error']
