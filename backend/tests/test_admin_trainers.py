"""Tests for admin trainer management endpoints."""
import pytest
from app import db
from models.user import User, UserRole
from models.trainer_profile import TrainerProfile
from models.trainer_attendance import TrainerAttendance
from services.password_service import PasswordService
from datetime import datetime, timedelta, date


class TestTrainerCRUDEndpoints:
    """Tests for trainer CRUD endpoints."""
    
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
    
    def test_create_trainer_success(self, client, admin_token):
        """Test successful trainer creation."""
        response = client.post('/api/admin/trainers',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'trainer1',
                'password': 'password123',
                'specialization': 'Strength Training',
                'salary_rate': 50.00
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['specialization'] == 'Strength Training'
        assert float(data['salary_rate']) == 50.00
        assert 'hire_date' in data
    
    def test_create_trainer_with_hire_date(self, client, admin_token):
        """Test trainer creation with custom hire date."""
        hire_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        response = client.post('/api/admin/trainers',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'trainer1',
                'password': 'password123',
                'specialization': 'Cardio',
                'salary_rate': 45.00,
                'hire_date': hire_date
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['specialization'] == 'Cardio'
    
    def test_create_trainer_missing_required_fields(self, client, admin_token):
        """Test trainer creation with missing required fields."""
        response = client.post('/api/admin/trainers',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'trainer1',
                'password': 'password123'
                # Missing specialization and salary_rate
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_trainer_duplicate_username(self, client, admin_token, app):
        """Test trainer creation with duplicate username."""
        # Create first trainer
        with app.app_context():
            user = User(
                username="existingtrainer",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.TRAINER,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        # Try to create another with same username
        response = client.post('/api/admin/trainers',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'existingtrainer',
                'password': 'password123',
                'specialization': 'Yoga',
                'salary_rate': 40.00
            }
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'Username already exists' in data['error']
    
    def test_create_trainer_invalid_salary_rate(self, client, admin_token):
        """Test trainer creation with invalid salary rate."""
        response = client.post('/api/admin/trainers',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'trainer1',
                'password': 'password123',
                'specialization': 'Pilates',
                'salary_rate': -50.00
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Salary rate must be positive' in data['error']
    
    def test_create_trainer_non_numeric_salary_rate(self, client, admin_token):
        """Test trainer creation with non-numeric salary rate."""
        response = client.post('/api/admin/trainers',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'trainer1',
                'password': 'password123',
                'specialization': 'Boxing',
                'salary_rate': 'invalid'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Salary rate must be a valid number' in data['error']
    
    def test_list_trainers_empty(self, client, admin_token):
        """Test listing trainers when none exist."""
        response = client.get('/api/admin/trainers',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['trainers'] == []
        assert data['total'] == 0
        assert data['page'] == 1
        assert data['per_page'] == 20
    
    def test_list_trainers_with_pagination(self, client, admin_token, app):
        """Test listing trainers with pagination."""
        # Create multiple trainers
        with app.app_context():
            for i in range(5):
                user = User(
                    username=f"trainer{i}",
                    password_hash=PasswordService.hash_password("password123"),
                    role=UserRole.TRAINER,
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()
                
                trainer = TrainerProfile(
                    user_id=user.id,
                    specialization=f'Specialization {i}',
                    salary_rate=50.00 + i
                )
                db.session.add(trainer)
            db.session.commit()
        
        # Get first page
        response = client.get('/api/admin/trainers?page=1&per_page=2',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['trainers']) == 2
        assert data['total'] == 5
        assert data['page'] == 1
        assert data['per_page'] == 2
    
    def test_get_trainer_success(self, client, admin_token, app):
        """Test getting trainer details."""
        # Create trainer
        with app.app_context():
            user = User(
                username="trainer1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.TRAINER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            trainer = TrainerProfile(
                user_id=user.id,
                specialization='CrossFit',
                salary_rate=60.00
            )
            db.session.add(trainer)
            db.session.commit()
            trainer_id = trainer.id
        
        response = client.get(f'/api/admin/trainers/{trainer_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['specialization'] == 'CrossFit'
        assert float(data['salary_rate']) == 60.00
    
    def test_get_trainer_not_found(self, client, admin_token):
        """Test getting nonexistent trainer."""
        response = client.get('/api/admin/trainers/nonexistent-id',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'Trainer not found' in data['error']
    
    def test_update_trainer_success(self, client, admin_token, app):
        """Test updating trainer information."""
        # Create trainer
        with app.app_context():
            user = User(
                username="trainer1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.TRAINER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            trainer = TrainerProfile(
                user_id=user.id,
                specialization='Yoga',
                salary_rate=40.00
            )
            db.session.add(trainer)
            db.session.commit()
            trainer_id = trainer.id
        
        response = client.put(f'/api/admin/trainers/{trainer_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'specialization': 'Advanced Yoga',
                'salary_rate': 55.00
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['specialization'] == 'Advanced Yoga'
        assert float(data['salary_rate']) == 55.00
    
    def test_update_trainer_invalid_salary_rate(self, client, admin_token, app):
        """Test updating trainer with invalid salary rate."""
        # Create trainer
        with app.app_context():
            user = User(
                username="trainer1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.TRAINER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            trainer = TrainerProfile(
                user_id=user.id,
                specialization='Yoga',
                salary_rate=40.00
            )
            db.session.add(trainer)
            db.session.commit()
            trainer_id = trainer.id
        
        response = client.put(f'/api/admin/trainers/{trainer_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'salary_rate': -10.00
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Salary rate must be positive' in data['error']
    
    def test_delete_trainer_success(self, client, admin_token, app):
        """Test deleting a trainer."""
        # Create trainer
        with app.app_context():
            user = User(
                username="trainer1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.TRAINER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            trainer = TrainerProfile(
                user_id=user.id,
                specialization='Zumba',
                salary_rate=35.00
            )
            db.session.add(trainer)
            db.session.commit()
            trainer_id = trainer.id
        
        response = client.delete(f'/api/admin/trainers/{trainer_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'Trainer deleted successfully' in data['message']
        
        # Verify trainer is deleted
        with app.app_context():
            deleted_trainer = TrainerProfile.query.get(trainer_id)
            assert deleted_trainer is None
    
    def test_delete_trainer_not_found(self, client, admin_token):
        """Test deleting nonexistent trainer."""
        response = client.delete('/api/admin/trainers/nonexistent-id',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'Trainer not found' in data['error']


class TestTrainerAttendanceEndpoints:
    """Tests for trainer attendance endpoints."""
    
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
    def test_trainer(self, app):
        """Create a test trainer."""
        with app.app_context():
            user = User(
                username="trainer1",
                password_hash=PasswordService.hash_password("password123"),
                role=UserRole.TRAINER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            trainer = TrainerProfile(
                user_id=user.id,
                specialization='Fitness',
                salary_rate=50.00
            )
            db.session.add(trainer)
            db.session.commit()
            return trainer.id
    
    def test_get_trainer_attendance_empty(self, client, admin_token, test_trainer):
        """Test getting trainer attendance when none exist."""
        response = client.get(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['attendance'] == []
        assert data['total'] == 0
    
    def test_get_trainer_attendance_not_found(self, client, admin_token):
        """Test getting attendance for nonexistent trainer."""
        response = client.get('/api/admin/trainers/nonexistent-id/attendance',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'Trainer not found' in data['error']
    
    def test_mark_trainer_check_in_success(self, client, admin_token, test_trainer):
        """Test marking trainer check-in."""
        response = client.post(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'action': 'check-in'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['check_in_time'] is not None
        assert data['check_out_time'] is None
        assert data['hours_worked'] is None
    
    def test_mark_trainer_check_in_with_timestamp(self, client, admin_token, test_trainer):
        """Test marking trainer check-in with custom timestamp."""
        timestamp = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        response = client.post(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'action': 'check-in',
                'timestamp': timestamp
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['check_in_time'] is not None
    
    def test_mark_trainer_check_out_success(self, client, admin_token, test_trainer, app):
        """Test marking trainer check-out."""
        # First check-in
        with app.app_context():
            trainer = TrainerProfile.query.get(test_trainer)
            attendance = TrainerAttendance(
                trainer_id=test_trainer,
                check_in_time=datetime.utcnow(),
                attendance_date=date.today()
            )
            db.session.add(attendance)
            db.session.commit()
        
        # Then check-out
        response = client.post(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'action': 'check-out'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['check_in_time'] is not None
        assert data['check_out_time'] is not None
        assert data['hours_worked'] is not None
    
    def test_mark_trainer_check_out_no_active_check_in(self, client, admin_token, test_trainer):
        """Test check-out without active check-in."""
        response = client.post(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'action': 'check-out'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'No active check-in found' in data['error']
    
    def test_mark_trainer_attendance_invalid_action(self, client, admin_token, test_trainer):
        """Test marking attendance with invalid action."""
        response = client.post(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'action': 'invalid-action'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid action' in data['error']
    
    def test_mark_trainer_attendance_missing_action(self, client, admin_token, test_trainer):
        """Test marking attendance without action field."""
        response = client.post(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Missing action field' in data['error']
    
    def test_get_trainer_attendance_with_records(self, client, admin_token, test_trainer, app):
        """Test getting trainer attendance with records."""
        # Create attendance records
        with app.app_context():
            for i in range(3):
                attendance = TrainerAttendance(
                    trainer_id=test_trainer,
                    check_in_time=datetime.utcnow() - timedelta(days=i),
                    check_out_time=datetime.utcnow() - timedelta(days=i, hours=-2),
                    attendance_date=(date.today() - timedelta(days=i))
                )
                db.session.add(attendance)
            db.session.commit()
        
        response = client.get(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['attendance']) == 3
        assert data['total'] == 3
    
    def test_get_trainer_attendance_with_date_filter(self, client, admin_token, test_trainer, app):
        """Test getting trainer attendance with date filter."""
        # Create attendance records
        with app.app_context():
            for i in range(5):
                attendance = TrainerAttendance(
                    trainer_id=test_trainer,
                    check_in_time=datetime.utcnow() - timedelta(days=i),
                    check_out_time=datetime.utcnow() - timedelta(days=i, hours=-2),
                    attendance_date=(date.today() - timedelta(days=i))
                )
                db.session.add(attendance)
            db.session.commit()
        
        # Filter by date range
        start_date = (date.today() - timedelta(days=2)).isoformat()
        end_date = date.today().isoformat()
        
        response = client.get(
            f'/api/admin/trainers/{test_trainer}/attendance?start_date={start_date}&end_date={end_date}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['attendance']) == 3  # Today, yesterday, 2 days ago
    
    def test_trainer_hours_worked_calculation(self, client, admin_token, test_trainer, app):
        """Test that hours worked is calculated correctly."""
        # Create attendance record with 2 hours worked
        with app.app_context():
            check_in = datetime.utcnow()
            check_out = check_in + timedelta(hours=2)
            
            attendance = TrainerAttendance(
                trainer_id=test_trainer,
                check_in_time=check_in,
                check_out_time=check_out,
                attendance_date=date.today()
            )
            db.session.add(attendance)
            db.session.commit()
        
        response = client.get(f'/api/admin/trainers/{test_trainer}/attendance',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['attendance']) == 1
        assert data['attendance'][0]['hours_worked'] == 2.0
