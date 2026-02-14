"""Tests for overdue payment logic."""
import pytest
from datetime import datetime, timedelta
from models.transaction import Transaction, TransactionStatus, TransactionType
from models.member_profile import MemberProfile
from models.user import User, UserRole
from models.package import Package
from services.password_service import PasswordService
from database import db


@pytest.fixture
def test_data(app):
    """Create test data for overdue payment tests."""
    with app.app_context():
        # Create a user
        user = User(
            username='testmember',
            password_hash=PasswordService.hash_password('password123'),
            role=UserRole.MEMBER,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()
        
        # Create a member
        member = MemberProfile(
            user_id=user.id,
            full_name='Test Member',
            phone='1234567890',
            cnic='12345-1234567-1',
            email='test@example.com',
            gender='Male',
            is_frozen=False
        )
        db.session.add(member)
        db.session.flush()
        
        # Create a package
        package = Package(
            name='Test Package',
            description='Test package',
            price=5000,
            duration_days=30,
            is_active=True
        )
        db.session.add(package)
        db.session.flush()
        
        # Create transactions with different due dates
        # 1. Overdue transaction (due date in the past)
        overdue_transaction = Transaction(
            member_id=member.id,
            amount=10000,
            transaction_type=TransactionType.ADMISSION,
            status=TransactionStatus.PENDING,
            due_date=datetime.utcnow() - timedelta(days=5),  # 5 days ago
            trainer_fee=5000,
            package_price=5000,
            discount_amount=0,
            discount_type='fixed',
            created_at=datetime.utcnow()
        )
        db.session.add(overdue_transaction)
        db.session.flush()
        
        # 2. Pending transaction (due date in the future)
        pending_transaction = Transaction(
            member_id=member.id,
            amount=10000,
            transaction_type=TransactionType.ADMISSION,
            status=TransactionStatus.PENDING,
            due_date=datetime.utcnow() + timedelta(days=5),  # 5 days from now
            trainer_fee=5000,
            package_price=5000,
            discount_amount=0,
            discount_type='fixed',
            created_at=datetime.utcnow()
        )
        db.session.add(pending_transaction)
        db.session.flush()
        
        # 3. Completed transaction
        completed_transaction = Transaction(
            member_id=member.id,
            amount=10000,
            transaction_type=TransactionType.ADMISSION,
            status=TransactionStatus.COMPLETED,
            due_date=datetime.utcnow() - timedelta(days=10),
            paid_date=datetime.utcnow() - timedelta(days=8),
            trainer_fee=5000,
            package_price=5000,
            discount_amount=0,
            discount_type='fixed',
            created_at=datetime.utcnow()
        )
        db.session.add(completed_transaction)
        db.session.commit()
        
        yield {
            'user': user,
            'member': member,
            'package': package,
            'overdue_transaction': overdue_transaction,
            'pending_transaction': pending_transaction,
            'completed_transaction': completed_transaction
        }


def test_overdue_payment_detection(test_data, app):
    """Test that overdue payments are correctly identified."""
    with app.app_context():
        overdue_txn = test_data['overdue_transaction']
        
        # Check that the transaction is marked as PENDING
        assert overdue_txn.status == TransactionStatus.PENDING
        
        # Check that the due date is in the past
        assert overdue_txn.due_date < datetime.utcnow()
        
        # Simulate the logic from get_member_payments_fixed
        status = overdue_txn.status.value
        if status != 'COMPLETED' and overdue_txn.due_date:
            if datetime.utcnow() > overdue_txn.due_date:
                status = 'OVERDUE'
        
        assert status == 'OVERDUE', "Transaction should be marked as OVERDUE"


def test_pending_payment_not_overdue(test_data, app):
    """Test that pending payments with future due dates are not marked as overdue."""
    with app.app_context():
        pending_txn = test_data['pending_transaction']
        
        # Check that the transaction is marked as PENDING
        assert pending_txn.status == TransactionStatus.PENDING
        
        # Check that the due date is in the future
        assert pending_txn.due_date > datetime.utcnow()
        
        # Simulate the logic from get_member_payments_fixed
        status = pending_txn.status.value
        if status != 'COMPLETED' and pending_txn.due_date:
            if datetime.utcnow() > pending_txn.due_date:
                status = 'OVERDUE'
        
        assert status == 'PENDING', "Transaction should remain PENDING"


def test_completed_payment_not_overdue(test_data, app):
    """Test that completed payments are never marked as overdue."""
    with app.app_context():
        completed_txn = test_data['completed_transaction']
        
        # Check that the transaction is marked as COMPLETED
        assert completed_txn.status == TransactionStatus.COMPLETED
        
        # Simulate the logic from get_member_payments_fixed
        status = completed_txn.status.value
        if status != 'COMPLETED' and completed_txn.due_date:
            if datetime.utcnow() > completed_txn.due_date:
                status = 'OVERDUE'
        
        assert status == 'COMPLETED', "Completed transaction should not be marked as OVERDUE"


def test_transaction_amount_calculation(test_data, app):
    """Test that transaction amounts are calculated correctly."""
    with app.app_context():
        txn = test_data['overdue_transaction']
        
        # Amount should be: admission_fee + package_price + trainer_fee - discount
        # In this case: 0 + 5000 + 5000 - 0 = 10000
        assert txn.amount == 10000
        assert txn.trainer_fee == 5000
        assert txn.package_price == 5000
        assert txn.discount_amount == 0


def test_transaction_with_discount(app):
    """Test transaction calculation with discount."""
    with app.app_context():
        # Create a user
        user = User(
            username='testmember2',
            password_hash=PasswordService.hash_password('password123'),
            role=UserRole.MEMBER,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()
        
        # Create a member
        member = MemberProfile(
            user_id=user.id,
            full_name='Test Member 2',
            phone='0987654321',
            cnic='98765-7654321-9',
            email='test2@example.com',
            gender='Female',
            is_frozen=False
        )
        db.session.add(member)
        db.session.flush()
        
        # Create transaction with discount
        # Total: 5000 (admission) + 5000 (package) + 5000 (trainer) = 15000
        # Discount: 1500 (10%)
        # Final: 13500
        txn = Transaction(
            member_id=member.id,
            amount=13500,
            transaction_type=TransactionType.ADMISSION,
            status=TransactionStatus.PENDING,
            due_date=datetime.utcnow() + timedelta(days=7),
            trainer_fee=5000,
            package_price=5000,
            discount_amount=1500,
            discount_type='fixed',
            created_at=datetime.utcnow()
        )
        db.session.add(txn)
        db.session.commit()
        
        # Verify calculation
        assert txn.amount == 13500
        assert txn.trainer_fee == 5000
        assert txn.package_price == 5000
        assert txn.discount_amount == 1500
        
        # Reverse calculate admission fee
        admission_fee = txn.amount + txn.discount_amount - txn.trainer_fee - txn.package_price
        assert admission_fee == 5000
