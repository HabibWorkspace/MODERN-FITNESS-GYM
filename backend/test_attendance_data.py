"""
Test script to check attendance data in database
Run this on PythonAnywhere to debug the issue
"""
from app import app
from database import db
from models.attendance_record import AttendanceRecord
from datetime import datetime, timezone as tz
from sqlalchemy import func

with app.app_context():
    print("=" * 70)
    print("ATTENDANCE DATA DEBUG")
    print("=" * 70)
    
    # Get current UTC time
    now_utc = datetime.now(tz.utc)
    today = now_utc.date()
    
    print(f"\nCurrent UTC time: {now_utc}")
    print(f"Today's date (UTC): {today}")
    
    # Count total records
    total_records = db.session.query(func.count(AttendanceRecord.id)).scalar()
    print(f"\nTotal attendance records in database: {total_records}")
    
    # Get last 10 records
    print("\n" + "=" * 70)
    print("LAST 10 ATTENDANCE RECORDS:")
    print("=" * 70)
    
    recent_records = db.session.query(AttendanceRecord).order_by(
        AttendanceRecord.check_in_time.desc()
    ).limit(10).all()
    
    for i, record in enumerate(recent_records, 1):
        check_in_date = record.check_in_time.date() if record.check_in_time else None
        print(f"\n{i}. {record.person_name or 'Unknown'}")
        print(f"   Person ID: {record.person_id}")
        print(f"   Type: {record.person_type}")
        print(f"   Check-in: {record.check_in_time}")
        print(f"   Check-in DATE: {check_in_date}")
        print(f"   Device User ID: {record.device_user_id}")
        print(f"   Device Serial: {record.device_serial}")
    
    # Count today's records
    print("\n" + "=" * 70)
    print(f"TODAY'S RECORDS (date = {today}):")
    print("=" * 70)
    
    today_records = db.session.query(AttendanceRecord).filter(
        func.date(AttendanceRecord.check_in_time) == today
    ).all()
    
    print(f"\nFound {len(today_records)} records for today")
    
    for i, record in enumerate(today_records, 1):
        print(f"\n{i}. {record.person_name or 'Unknown'}")
        print(f"   Check-in: {record.check_in_time}")
        print(f"   Type: {record.person_type}")
    
    # Try different date comparisons
    print("\n" + "=" * 70)
    print("TESTING DIFFERENT DATE QUERIES:")
    print("=" * 70)
    
    # Test 1: Using utcnow().date()
    test_date_1 = datetime.utcnow().date()
    count_1 = db.session.query(func.count(AttendanceRecord.id)).filter(
        func.date(AttendanceRecord.check_in_time) == test_date_1
    ).scalar()
    print(f"\n1. Using datetime.utcnow().date() = {test_date_1}")
    print(f"   Count: {count_1}")
    
    # Test 2: Using now(tz.utc).date()
    test_date_2 = datetime.now(tz.utc).date()
    count_2 = db.session.query(func.count(AttendanceRecord.id)).filter(
        func.date(AttendanceRecord.check_in_time) == test_date_2
    ).scalar()
    print(f"\n2. Using datetime.now(tz.utc).date() = {test_date_2}")
    print(f"   Count: {count_2}")
    
    # Test 3: Check if timestamps have timezone info
    if recent_records:
        sample = recent_records[0]
        print(f"\n3. Sample timestamp analysis:")
        print(f"   Raw timestamp: {sample.check_in_time}")
        print(f"   Has timezone: {sample.check_in_time.tzinfo is not None if sample.check_in_time else 'N/A'}")
        print(f"   Timezone: {sample.check_in_time.tzinfo if sample.check_in_time else 'N/A'}")
        print(f"   Date extracted: {sample.check_in_time.date() if sample.check_in_time else 'N/A'}")
    
    print("\n" + "=" * 70)
    print("DEBUG COMPLETE")
    print("=" * 70)
