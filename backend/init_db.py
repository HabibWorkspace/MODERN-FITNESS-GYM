"""Database initialization script."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from config import get_config
from models.user import User, UserRole
from services.password_service import PasswordService

def init_database():
    """Initialize the database schema."""
    config = get_config()
    app = create_app(config)
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Create admin user if it doesn't exist
        print("Creating admin user...")
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=PasswordService.hash_password('admin123'),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("  Admin user created (username: admin, password: admin123)")
        else:
            print("  Admin user already exists")
        
        # Print database info
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
        # Hide password in URL
        if '@' in db_url:
            parts = db_url.split('@')
            db_url_safe = parts[0].split(':')[0] + ':****@' + parts[1]
        else:
            db_url_safe = db_url
        print(f"Database initialized: {db_url_safe}")

if __name__ == '__main__':
    init_database()
