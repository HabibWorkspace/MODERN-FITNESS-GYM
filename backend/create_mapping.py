"""
Quick script to create device user mapping
Run this on PythonAnywhere to map device users to members/trainers
"""
from app import create_app
from database import db
from models.device_user_mapping import DeviceUserMapping
from models.member_profile import MemberProfile
from models.trainer_profile import TrainerProfile

app = create_app()

with app.app_context():
    print("=" * 60)
    print("DEVICE USER MAPPING TOOL")
    print("=" * 60)
    print()
    
    # Check existing mappings
    existing_mappings = DeviceUserMapping.query.all()
    print(f"Existing Mappings: {len(existing_mappings)}")
    if existing_mappings:
        print("\nCurrent Mappings:")
        for m in existing_mappings:
            print(f"  Device User {m.device_user_id} → {m.person_type} {m.person_id}")
    print()
    
    # List available members
    members = MemberProfile.query.all()
    print(f"Available Members: {len(members)}")
    if members:
        print("\nMembers:")
        for i, m in enumerate(members[:10], 1):  # Show first 10
            print(f"  {i}. {m.full_name or m.name} (ID: {m.id}, Member #: {m.member_number})")
        if len(members) > 10:
            print(f"  ... and {len(members) - 10} more")
    print()
    
    # List available trainers
    trainers = TrainerProfile.query.all()
    print(f"Available Trainers: {len(trainers)}")
    if trainers:
        print("\nTrainers:")
        for i, t in enumerate(trainers, 1):
            print(f"  {i}. {t.full_name or t.name} (ID: {t.id})")
    print()
    
    print("=" * 60)
    print("TO CREATE A MAPPING:")
    print("=" * 60)
    print()
    print("You need to know:")
    print("1. Device User ID (from the iFace950 device)")
    print("2. Person Type (member or trainer)")
    print("3. Person ID (from the list above)")
    print()
    print("Example:")
    print("  Device User ID: 7")
    print("  Person Type: member")
    print("  Person ID: ca79d323-2aac-4262-8191-0f504cdfe7ab")
    print()
    print("Create mapping via API:")
    print("  POST /api/attendance/mappings")
    print("  {")
    print('    "device_user_id": "7",')
    print('    "person_type": "member",')
    print('    "person_id": "ca79d323-2aac-4262-8191-0f504cdfe7ab"')
    print("  }")
    print()
    print("Or use the web interface:")
    print("  https://habibworkspace.pythonanywhere.com/attendance/mappings")
    print()
    print("=" * 60)
    
    # Auto-create mapping if we have the data
    print("\nAUTO-CREATE MAPPING:")
    print("=" * 60)
    
    # Check if we have the specific user from the error
    device_user_7 = DeviceUserMapping.query.filter_by(device_user_id='7').first()
    
    if device_user_7:
        print(f"✓ Device User 7 is already mapped to {device_user_7.person_type} {device_user_7.person_id}")
    else:
        print("✗ Device User 7 is NOT mapped")
        
        # Find the member "Blank 10" from the error
        blank_10 = MemberProfile.query.filter(
            (MemberProfile.full_name == 'Blank 10') | 
            (MemberProfile.name == 'Blank 10')
        ).first()
        
        if blank_10:
            print(f"\nFound member 'Blank 10': {blank_10.id}")
            print("\nCreating mapping...")
            
            try:
                mapping = DeviceUserMapping(
                    device_user_id='7',
                    person_type='member',
                    person_id=blank_10.id
                )
                db.session.add(mapping)
                db.session.commit()
                print("✓ Mapping created successfully!")
                print(f"  Device User 7 → Member {blank_10.full_name or blank_10.name}")
            except Exception as e:
                print(f"✗ Error creating mapping: {e}")
                db.session.rollback()
        else:
            print("\n⚠️  Could not find member 'Blank 10'")
            print("   You need to create the mapping manually")
    
    print()
    print("=" * 60)
