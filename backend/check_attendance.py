"""
Quick script to check if attendance records are being created
Run this on PythonAnywhere to verify data is being saved
"""
from app import create_app
from database import db
from models.attendance_record import AttendanceRecord
from models.device_user_mapping import DeviceUserMapping
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print("=" * 60)
    print("ATTENDANCE RECORDS CHECK")
    print("=" * 60)
    print()
    
    # Check total records
    total = AttendanceRecord.query.count()
    print(f"Total Attendance Records: {total}")
    print()
    
    # Check today's records
    today = datetime.utcnow().date()
    today_records = AttendanceRecord.query.filter(
        db.func.date(AttendanceRecord.check_in_time) == today
    ).all()
    
    print(f"Today's Records: {len(today_records)}")
    print()
    
    if today_records:
        print("Recent Records (last 10):")
        print("-" * 60)
        for r in today_records[-10:]:
            print(f"ID: {r.id}")
            print(f"  Person: {r.person_name or 'Unknown'} ({r.person_type})")
            print(f"  Check-in: {r.check_in_time}")
            print(f"  Device User ID: {r.device_user_id}")
            print(f"  Device Serial: {r.device_serial}")
            print(f"  Created: {r.created_at}")
            print()
    else:
        print("⚠️  No records found for today!")
        print()
    
    # Check last 5 minutes
    recent = AttendanceRecord.query.filter(
        AttendanceRecord.created_at >= datetime.utcnow() - timedelta(minutes=5)
    ).all()
    
    print(f"Records in Last 5 Minutes: {len(recent)}")
    if recent:
        for r in recent:
            print(f"  - {r.person_name or 'Unknown'} at {r.check_in_time}")
    print()
    
    # Check device mappings
    mappings = DeviceUserMapping.query.all()
    print(f"Device User Mappings: {len(mappings)}")
    if mappings:
        print("Mappings:")
        for m in mappings:
            print(f"  Device User {m.device_user_id} → {m.person_type} {m.person_id}")
    else:
        print("⚠️  No device mappings found!")
        print("     You need to create mappings for device users!")
    print()
    
    print("=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)
    
    if len(recent) > 0:
        print("✅ Records are being created successfully!")
        print("   Issue might be with:")
        print("   - Dashboard not refreshing")
        print("   - Pusher notifications not working")
        print("   - Frontend not polling for updates")
    elif len(mappings) == 0:
        print("❌ No device user mappings found!")
        print("   Create mappings at: /attendance/mappings")
    elif total == 0:
        print("❌ No attendance records at all!")
        print("   Check if sync is actually running")
    else:
        print("⚠️  Records exist but none recent")
        print("   Check if sync is running and device is connected")
    
    print("=" * 60)
