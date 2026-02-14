"""Transaction model."""
from database import db
from datetime import datetime
import uuid
from enum import Enum


class TransactionType(Enum):
    """Transaction type enumeration."""
    ADMISSION = 'ADMISSION'
    PACKAGE = 'PACKAGE'
    PAYMENT = 'PAYMENT'


class TransactionStatus(Enum):
    """Transaction status enumeration."""
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    OVERDUE = 'OVERDUE'


class Transaction(db.Model):
    """Transaction model."""
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = db.Column(db.String(36), db.ForeignKey('member_profiles.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    status = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    due_date = db.Column(db.DateTime)
    paid_date = db.Column(db.DateTime)
    trainer_fee = db.Column(db.Numeric(10, 2), default=0)
    package_price = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_type = db.Column(db.String(20), default='fixed')  # 'fixed' or 'percentage'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.amount}>'
    
    def to_dict(self):
        """Convert transaction to dictionary."""
        return {
            'id': self.id,
            'member_id': self.member_id,
            'amount': float(self.amount),
            'transaction_type': self.transaction_type.value,
            'status': self.status.value,
            'due_date': self.due_date.isoformat() + 'Z' if self.due_date else None,
            'paid_date': self.paid_date.isoformat() + 'Z' if self.paid_date else None,
            'trainer_fee': float(self.trainer_fee) if self.trainer_fee else 0,
            'package_price': float(self.package_price) if self.package_price else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'discount_type': self.discount_type or 'fixed',
            'created_at': self.created_at.isoformat() + 'Z',
        }
