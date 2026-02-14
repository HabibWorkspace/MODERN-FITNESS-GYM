"""Settings model for gym-wide configuration."""
from database import db
from datetime import datetime


class Settings(db.Model):
    """Settings model for gym-wide configuration."""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    admission_fee = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Settings admission_fee={self.admission_fee}>'
    
    def to_dict(self):
        """Convert settings to dictionary."""
        return {
            'id': self.id,
            'admission_fee': float(self.admission_fee),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

