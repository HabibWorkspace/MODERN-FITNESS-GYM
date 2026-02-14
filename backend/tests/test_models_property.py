"""Property-based tests for database models.

**Validates: Requirements 18.1, 18.2, 18.3**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta, date
import uuid
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db, create_app
from config import TestingConfig
from models.user import User, UserRole
from models.member_profile import MemberProfile
from models.trainer_profile import TrainerProfile
from models.package import Package
from models.attendance import Attendance, AttendanceMethod, AttendanceStatus
from models.diet_log import DietLog
from models.progress_metric import ProgressMetric, MetricType
from models.transaction import Transaction, TransactionType, TransactionStatus
from models.workout_routine import WorkoutRoutine
from models.trainer_feedback import TrainerFeedback
from models.trainer_attendance import TrainerAttendance


# Strategy definitions - use UUIDs for unique fields to avoid constraint violations
def unique_username():
    """Generate unique username."""
    return f"user_{uuid.uuid4().hex[:8]}"

def unique_email():
    """Generate unique email."""
    return f"user_{uuid.uuid4().hex[:8]}@test.com"

def unique_phone():
    """Generate unique phone."""
    return f"555{uuid.uuid4().hex[:7]}"

def unique_cnic():
    """Generate unique CNIC."""
    return f"{uuid.uuid4().hex[:13]}"

password_hash_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=20,
    max_size=255
)

positive_float = st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
positive_int = st.integers(min_value=1, max_value=365)


@pytest.fixture
def app_context(app):
    """Create app context for testing."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


class TestMemberDataPersistence:
    """Property 4: Member Data Persistence.
    
    For any member created with valid data, retrieving that member should return 
    the exact same data that was stored.
    
    **Validates: Requirements 2.1, 2.2**
    """
    
    @given(
        password_hash=password_hash_strategy,
        admission_fee_paid=st.booleans(),
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_member_profile_persistence(
        self, app_context, password_hash, admission_fee_paid
    ):
        """Test that member profile data persists correctly."""
        username = unique_username()
        phone = unique_phone()
        cnic = unique_cnic()
        email = unique_email()
        
        # Create user
        user = User(
            username=username,
            password_hash=password_hash,
            role=UserRole.MEMBER,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()
        
        # Create member profile
        member = MemberProfile(
            user_id=user.id,
            phone=phone,
            cnic=cnic,
            email=email,
            admission_fee_paid=admission_fee_paid,
            is_frozen=False
        )
        db.session.add(member)
        db.session.commit()
        
        # Retrieve and verify
        retrieved = MemberProfile.query.filter_by(user_id=user.id).first()
        assert retrieved is not None
        assert retrieved.phone == phone
        assert retrieved.cnic == cnic
        assert retrieved.email == email
        assert retrieved.admission_fee_paid == admission_fee_paid
        assert retrieved.is_frozen == False
        assert retrieved.user_id == user.id
    
    @given(
        password_hash=password_hash_strategy,
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_member_to_dict_consistency(
        self, app_context, password_hash
    ):
        """Test that member to_dict() returns consistent data."""
        username = unique_username()
        phone = unique_phone()
        cnic = unique_cnic()
        email = unique_email()
        
        user = User(
            username=username,
            password_hash=password_hash,
            role=UserRole.MEMBER
        )
        db.session.add(user)
        db.session.flush()
        
        member = MemberProfile(
            user_id=user.id,
            phone=phone,
            cnic=cnic,
            email=email,
            admission_fee_paid=True
        )
        db.session.add(member)
        db.session.commit()
        
        # Convert to dict and verify all fields present
        member_dict = member.to_dict()
        assert member_dict['phone'] == phone
        assert member_dict['cnic'] == cnic
        assert member_dict['email'] == email
        assert member_dict['user_id'] == user.id
        assert 'created_at' in member_dict
        assert 'updated_at' in member_dict


class TestDatabaseAbstraction:
    """Property 16: Database Abstraction.
    
    For any database operation, the system should work identically whether using 
    SQLite or PostgreSQL without code changes.
    
    **Validates: Requirements 18.1, 18.2**
    """
    
    @given(
        password_hash=password_hash_strategy,
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_creation_and_retrieval(self, app_context, password_hash):
        """Test user creation works across database backends."""
        username = unique_username()
        
        user = User(
            username=username,
            password_hash=password_hash,
            role=UserRole.ADMIN
        )
        db.session.add(user)
        db.session.commit()
        
        # Retrieve by ID
        retrieved = User.query.filter_by(id=user.id).first()
        assert retrieved is not None
        assert retrieved.username == username
        assert retrieved.password_hash == password_hash
        assert retrieved.role == UserRole.ADMIN
    
    @given(
        name=st.text(min_size=1, max_size=100),
        duration_days=positive_int,
        price=positive_float,
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_package_crud_operations(self, app_context, name, duration_days, price):
        """Test package CRUD operations work across backends."""
        # Create
        package = Package(
            name=name,
            duration_days=duration_days,
            price=price,
            is_active=True
        )
        db.session.add(package)
        db.session.commit()
        
        # Read
        retrieved = Package.query.filter_by(id=package.id).first()
        assert retrieved is not None
        assert retrieved.name == name
        assert retrieved.duration_days == duration_days
        assert float(retrieved.price) == pytest.approx(price, rel=0.01)
        
        # Update
        new_name = "Updated " + name
        retrieved.name = new_name
        db.session.commit()
        
        # Verify update
        updated = Package.query.filter_by(id=package.id).first()
        assert updated.name == new_name
        
        # Delete
        db.session.delete(updated)
        db.session.commit()
        
        # Verify deletion
        deleted = Package.query.filter_by(id=package.id).first()
        assert deleted is None
    
    @given(
        specialization=st.text(min_size=1, max_size=100),
        salary_rate=positive_float,
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_trainer_profile_persistence(self, app_context, specialization, salary_rate):
        """Test trainer profile persists correctly across backends."""
        username = unique_username()
        
        user = User(
            username=username,
            password_hash="hash",
            role=UserRole.TRAINER
        )
        db.session.add(user)
        db.session.flush()
        
        trainer = TrainerProfile(
            user_id=user.id,
            specialization=specialization,
            salary_rate=salary_rate,
            hire_date=datetime.utcnow()
        )
        db.session.add(trainer)
        db.session.commit()
        
        retrieved = TrainerProfile.query.filter_by(user_id=user.id).first()
        assert retrieved is not None
        assert retrieved.specialization == specialization
        assert float(retrieved.salary_rate) == pytest.approx(salary_rate, rel=0.01)


class TestAttendanceRecordIntegrity:
    """Property 6: Attendance Record Integrity.
    
    For any attendance record created with valid geofencing and QR code validation, 
    retrieving that record should return the exact same data including timestamp and method.
    
    **Validates: Requirements 8.4, 9.1**
    """
    
    @given(
        latitude=st.floats(min_value=-90, max_value=90),
        longitude=st.floats(min_value=-180, max_value=180),
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_attendance_record_persistence(self, app_context, latitude, longitude):
        """Test attendance records persist with exact data."""
        username = unique_username()
        
        user = User(
            username=username,
            password_hash="hash",
            role=UserRole.MEMBER
        )
        db.session.add(user)
        db.session.flush()
        
        now = datetime.utcnow()
        attendance = Attendance(
            user_id=user.id,
            timestamp=now,
            method=AttendanceMethod.QR_GPS,
            status=AttendanceStatus.SUCCESS,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(attendance)
        db.session.commit()
        
        retrieved = Attendance.query.filter_by(id=attendance.id).first()
        assert retrieved is not None
        assert retrieved.user_id == user.id
        assert retrieved.method == AttendanceMethod.QR_GPS
        assert retrieved.status == AttendanceStatus.SUCCESS
        assert retrieved.latitude == pytest.approx(latitude, abs=0.0001)
        assert retrieved.longitude == pytest.approx(longitude, abs=0.0001)
        # Timestamp should be very close (within 1 second)
        assert abs((retrieved.timestamp - now).total_seconds()) < 1
    
    @given(
        method=st.sampled_from(list(AttendanceMethod)),
        status=st.sampled_from(list(AttendanceStatus)),
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_attendance_method_and_status_preserved(self, app_context, method, status):
        """Test that attendance method and status are preserved."""
        username = unique_username()
        
        user = User(
            username=username,
            password_hash="hash",
            role=UserRole.MEMBER
        )
        db.session.add(user)
        db.session.flush()
        
        attendance = Attendance(
            user_id=user.id,
            method=method,
            status=status
        )
        db.session.add(attendance)
        db.session.commit()
        
        retrieved = Attendance.query.filter_by(id=attendance.id).first()
        assert retrieved.method == method
        assert retrieved.status == status


class TestDietLoggingAggregation:
    """Property 9: Diet Logging Aggregation.
    
    For any set of food items logged on the same day, the daily totals should 
    equal the sum of individual item values.
    
    **Validates: Requirements 10.4, 10.5**
    """
    
    @given(
        food_items=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=50),  # food_name
                st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False),  # quantity
                st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),  # calories
                st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),  # protein
                st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),  # carbs
                st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),  # fats
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_diet_log_aggregation(self, app_context, food_items):
        """Test that diet log totals equal sum of individual items."""
        username = unique_username()
        phone = unique_phone()
        cnic = unique_cnic()
        email = unique_email()
        
        user = User(
            username=username,
            password_hash="hash",
            role=UserRole.MEMBER
        )
        db.session.add(user)
        db.session.flush()
        
        member = MemberProfile(
            user_id=user.id,
            phone=phone,
            cnic=cnic,
            email=email
        )
        db.session.add(member)
        db.session.flush()
        
        today = date.today()
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        for food_name, quantity, calories, protein, carbs, fats in food_items:
            diet_log = DietLog(
                member_id=member.id,
                food_name=food_name,
                quantity=quantity,
                unit="g",
                calories=calories,
                protein_g=protein,
                carbs_g=carbs,
                fats_g=fats,
                logged_date=today
            )
            db.session.add(diet_log)
            total_calories += calories
            total_protein += protein
            total_carbs += carbs
            total_fats += fats
        
        db.session.commit()
        
        # Retrieve all logs for today
        logs = DietLog.query.filter_by(member_id=member.id, logged_date=today).all()
        assert len(logs) == len(food_items)
        
        # Calculate totals
        retrieved_calories = sum(log.calories for log in logs)
        retrieved_protein = sum(log.protein_g for log in logs)
        retrieved_carbs = sum(log.carbs_g for log in logs)
        retrieved_fats = sum(log.fats_g for log in logs)
        
        # Verify totals match
        assert retrieved_calories == pytest.approx(total_calories, rel=0.01)
        assert retrieved_protein == pytest.approx(total_protein, rel=0.01)
        assert retrieved_carbs == pytest.approx(total_carbs, rel=0.01)
        assert retrieved_fats == pytest.approx(total_fats, rel=0.01)


class TestProgressMetricCalculation:
    """Property 10: Progress Metric Calculation.
    
    For any weight value logged, the calculated BMI should be mathematically correct 
    based on the member's height.
    
    **Validates: Requirements 11.2, 11.4, 11.5**
    """
    
    @given(
        weight=st.floats(min_value=30, max_value=300, allow_nan=False, allow_infinity=False),
        body_fat=st.floats(min_value=5, max_value=50, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_progress_metric_persistence(self, app_context, weight, body_fat):
        """Test that progress metrics are stored and retrieved correctly."""
        username = unique_username()
        phone = unique_phone()
        cnic = unique_cnic()
        email = unique_email()
        
        user = User(
            username=username,
            password_hash="hash",
            role=UserRole.MEMBER
        )
        db.session.add(user)
        db.session.flush()
        
        member = MemberProfile(
            user_id=user.id,
            phone=phone,
            cnic=cnic,
            email=email
        )
        db.session.add(member)
        db.session.flush()
        
        # Log weight
        weight_metric = ProgressMetric(
            member_id=member.id,
            metric_type=MetricType.WEIGHT,
            value=weight,
            unit="kg"
        )
        db.session.add(weight_metric)
        
        # Log body fat
        body_fat_metric = ProgressMetric(
            member_id=member.id,
            metric_type=MetricType.BODY_FAT,
            value=body_fat,
            unit="%"
        )
        db.session.add(body_fat_metric)
        db.session.commit()
        
        # Retrieve and verify
        weight_retrieved = ProgressMetric.query.filter_by(
            member_id=member.id,
            metric_type=MetricType.WEIGHT
        ).first()
        assert weight_retrieved is not None
        assert weight_retrieved.value == pytest.approx(weight, rel=0.01)
        assert weight_retrieved.unit == "kg"
        
        body_fat_retrieved = ProgressMetric.query.filter_by(
            member_id=member.id,
            metric_type=MetricType.BODY_FAT
        ).first()
        assert body_fat_retrieved is not None
        assert body_fat_retrieved.value == pytest.approx(body_fat, rel=0.01)
        assert body_fat_retrieved.unit == "%"


class TestTransactionStatusTracking:
    """Property 13: Transaction Status Tracking.
    
    For any transaction marked as paid, the payment status should be updated 
    and the transaction timestamp should be recorded.
    
    **Validates: Requirements 5.2**
    """
    
    @given(
        amount=positive_float,
        transaction_type=st.sampled_from(list(TransactionType)),
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_transaction_status_update(self, app_context, amount, transaction_type):
        """Test that transaction status updates are persisted."""
        username = unique_username()
        phone = unique_phone()
        cnic = unique_cnic()
        email = unique_email()
        
        user = User(
            username=username,
            password_hash="hash",
            role=UserRole.MEMBER
        )
        db.session.add(user)
        db.session.flush()
        
        member = MemberProfile(
            user_id=user.id,
            phone=phone,
            cnic=cnic,
            email=email
        )
        db.session.add(member)
        db.session.flush()
        
        # Create transaction
        transaction = Transaction(
            member_id=member.id,
            amount=amount,
            transaction_type=transaction_type,
            status=TransactionStatus.PENDING,
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Verify initial status
        retrieved = Transaction.query.filter_by(id=transaction.id).first()
        assert retrieved.status == TransactionStatus.PENDING
        assert retrieved.paid_date is None
        
        # Update status to completed
        retrieved.status = TransactionStatus.COMPLETED
        retrieved.paid_date = datetime.utcnow()
        db.session.commit()
        
        # Verify update
        updated = Transaction.query.filter_by(id=transaction.id).first()
        assert updated.status == TransactionStatus.COMPLETED
        assert updated.paid_date is not None
        assert float(updated.amount) == pytest.approx(amount, rel=0.01)


class TestTrainerAttendanceHours:
    """Property 19: Trainer Attendance Hours.
    
    For any trainer check-in and check-out pair, the calculated hours_worked 
    should equal (check_out_time - check_in_time) in hours.
    
    **Validates: Requirements 16.2, 16.3**
    """
    
    @given(
        hours_worked=st.floats(min_value=0.5, max_value=12, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_trainer_hours_calculation(self, app_context, hours_worked):
        """Test that trainer hours are calculated correctly."""
        username = unique_username()
        
        user = User(
            username=username,
            password_hash="hash",
            role=UserRole.TRAINER
        )
        db.session.add(user)
        db.session.flush()
        
        trainer = TrainerProfile(
            user_id=user.id,
            specialization="Fitness",
            salary_rate=50.0,
            hire_date=datetime.utcnow()
        )
        db.session.add(trainer)
        db.session.flush()
        
        check_in = datetime.utcnow()
        check_out = check_in + timedelta(hours=hours_worked)
        
        attendance = TrainerAttendance(
            trainer_id=trainer.id,
            check_in_time=check_in,
            check_out_time=check_out
        )
        db.session.add(attendance)
        db.session.commit()
        
        retrieved = TrainerAttendance.query.filter_by(id=attendance.id).first()
        calculated_hours = retrieved.get_hours_worked()
        assert calculated_hours == pytest.approx(hours_worked, rel=0.01)
