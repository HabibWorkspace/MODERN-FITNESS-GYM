"""Package model."""
from database import db
from datetime import datetime
import uuid


class Package(db.Model):
    """Package model for membership plans."""
    __tablename__ = 'packages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    member_profiles = db.relationship('MemberProfile', backref='package')
    
    def __repr__(self):
        return f'<Package {self.name}>'
    
    def to_dict(self):
        """Convert package to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'duration_days': self.duration_days,
            'price': float(self.price),
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
