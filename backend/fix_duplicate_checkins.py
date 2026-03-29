"""Fix duplicate unclosed check-ins by auto-checking out old records."""
import sys
from datetime import datetime, timedelta, timezone
from app import create_app
from database import db
from models.attendance_record import AttendanceRecord

def fix_duplicate_checkins():
    """Auto check-out any unclosed records older than 12 hours."""
    app, _ = create_app()
    
    with app.app_context():
        # Find all unclosed records
        unclosed_records = AttendanceRecord.query.filter(
            AttendanceRecord.check_out_time.is_(None)
        ).all()
        
        print(f"Found {len(unclosed_records)} unclosed records")
        
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        cutoff_time = now - timedelta(hours=12)
        
        fixed_count = 0
        for record in unclosed_records:
            check_in = record.check_in_time
            if check_in.tzinfo is None:
                check_in = check_in.replace(tzinfo=timezone.utc)
            
            # If check-in is older than 12 hours, auto check-out
            if check_in < cutoff_time:
                # Set check-out to 8 hours after check-in (reasonable gym session)
                auto_checkout_time = check_in + timedelta(hours=8)
                record.check_out_time = auto_checkout_time
                record.stay_duration = int((auto_checkout_time - check_in).total_seconds() / 60)
                
                print(f"Auto checked-out: {record.person_name} (checked in at {check_in}, auto checked-out at {auto_checkout_time})")
                fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\nFixed {fixed_count} old unclosed records")
        else:
            print("\nNo old records to fix")
        
        # Show remaining unclosed records
        remaining = AttendanceRecord.query.filter(
            AttendanceRecord.check_out_time.is_(None)
        ).count()
        print(f"Remaining unclosed records: {remaining}")

if __name__ == '__main__':
    fix_duplicate_checkins()
