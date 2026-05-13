"""
Create database tables without needing full app
Run this on PythonAnywhere to initialize the database
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from database import db

# Load environment
env_path = Path(__file__).parent / '.env.production'
if not env_path.exists():
    env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///fitnix.db')
print(f"Database URL: {DATABASE_URL}")

# Create engine
engine = create_engine(DATABASE_URL)

# Import all models to register them with SQLAlchemy
print("Importing models...")
from models.user import User
from models.member_profile import MemberProfile
from models.trainer_profile import TrainerProfile
from models.package import Package
from models.payment import Payment
from models.transaction import Transaction
from models.attendance_record import AttendanceRecord
from models.device_user_mapping import DeviceUserMapping
from models.settings import Settings
from models.daily_attendance_summary import DailyAttendanceSummary
from models.device_sync_state import DeviceSyncState

print("Creating all tables...")
db.metadata.create_all(engine)

print("\n✓ All database tables created successfully!")
print("\nTables created:")
for table in db.metadata.sorted_tables:
    print(f"  - {table.name}")
