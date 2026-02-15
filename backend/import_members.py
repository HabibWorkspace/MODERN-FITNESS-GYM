"""Import members from Excel file."""
import openpyxl
from datetime import datetime
from app import create_app
from database import db
from models.user import User, UserRole
from models.member_profile import MemberProfile
from models.trainer_profile import TrainerProfile
from models.package import Package
from services.password_service import PasswordService

def import_data():
    app = create_app()
    
    with app.app_context():
        # First, create packages
        packages_data = {
            'Basic': {'price': 1000, 'duration': 30},
            'Cardio': {'price': 1500, 'duration': 30},
            'Combo I': {'price': 2500, 'duration': 30},
            'Combo III': {'price': 2000, 'duration': 30},
            'Aerobic': {'price': 1000, 'duration': 30}
        }
        
        print("Creating packages...")
        package_map = {}
        for pkg_name, pkg_data in packages_data.items():
            existing_pkg = Package.query.filter_by(name=pkg_name).first()
            if not existing_pkg:
                pkg = Package(
                    name=pkg_name,
                    price=pkg_data['price'],
                    duration_days=pkg_data['duration'],
                    description=f'{pkg_name} package'
                )
                db.session.add(pkg)
                db.session.flush()
                package_map[pkg_name] = pkg.id
                print(f"  Created package: {pkg_name}")
            else:
                package_map[pkg_name] = existing_pkg.id
                print(f"  Package already exists: {pkg_name}")
        
        db.session.commit()
        
        # Create trainers
        print("\nCreating trainers...")
        trainer_map = {}
        trainers_data = [
            {'name': 'Ali', 'username': 'ali_trainer'},
            {'name': 'Mustafa', 'username': 'mustafa_trainer'}
        ]
        
        for trainer_data in trainers_data:
            existing_user = User.query.filter_by(username=trainer_data['username']).first()
            if not existing_user:
                user = User(
                    username=trainer_data['username'],
                    password_hash=PasswordService.hash_password('trainer123'),
                    role=UserRole.TRAINER,
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()
                
                trainer_profile = TrainerProfile(
                    user_id=user.id,
                    specialization='General Training',
                    phone='0300000000' + trainer_data['name'][:3],
                    salary_rate=0.0  # Default salary rate
                )
                db.session.add(trainer_profile)
                trainer_map[trainer_data['name']] = user.id
                print(f"  Created trainer: {trainer_data['name']}")
            else:
                trainer_map[trainer_data['name']] = existing_user.id
                print(f"  Trainer already exists: {trainer_data['name']}")
        
        db.session.commit()
        
        # Load Excel file
        print("\nLoading Excel file...")
        wb = openpyxl.load_workbook('../frontend/public/Member Details (Jan-26).xlsx')
        ws = wb.active
        
        # Skip header row
        rows = list(ws.iter_rows(values_only=True))[1:]
        
        print(f"\nImporting {len(rows)} members...")
        imported_count = 0
        skipped_count = 0
        
        for row in rows:
            # Skip empty rows
            if not row[0] or not row[1]:
                continue
            
            member_id, name, cell, package_name, date_of_adm, next_due, gym_fee, trainer_name, ali_fee, mustafa_fee = row[:10]
            
            # Create username from name
            username = name.lower().replace(' ', '_')
            
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"  Skipped (already exists): {name}")
                skipped_count += 1
                continue
            
            # Create user
            user = User(
                username=username,
                password_hash=PasswordService.hash_password('member123'),
                role=UserRole.MEMBER,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            # Get package ID
            pkg_id = package_map.get(package_name) if package_name else None
            
            # Get trainer ID
            trainer_id = None
            if trainer_name and trainer_name != 'No':
                trainer_id = trainer_map.get(trainer_name)
            
            # Create member profile
            # Handle duplicate phone numbers by appending member ID
            phone_str = str(cell) if cell else f'030000{member_id:05d}'
            if cell:
                # Check if phone already exists
                existing_phone = MemberProfile.query.filter_by(phone=phone_str).first()
                if existing_phone:
                    phone_str = f'{cell}{member_id}'  # Append ID to make unique
            
            member_profile = MemberProfile(
                user_id=user.id,
                full_name=name,
                phone=phone_str,
                cnic=f'{member_id:05d}-0000000-0',  # Generate unique CNIC from member ID
                email=f'{username}@gym.local',  # Default email
                current_package_id=pkg_id,
                trainer_id=trainer_id,
                admission_date=date_of_adm if isinstance(date_of_adm, datetime) else datetime.now(),
                package_start_date=date_of_adm if isinstance(date_of_adm, datetime) else None
            )
            
            # Calculate package expiry if package assigned
            if pkg_id and member_profile.package_start_date:
                from datetime import timedelta
                pkg = Package.query.get(pkg_id)
                member_profile.package_expiry_date = member_profile.package_start_date + timedelta(days=pkg.duration_days)
            
            db.session.add(member_profile)
            imported_count += 1
            print(f"  Imported: {name} (Package: {package_name}, Trainer: {trainer_name})")
        
        db.session.commit()
        print(f"\n==> Import complete!")
        print(f"   Imported: {imported_count} members")
        print(f"   Skipped: {skipped_count} members")
        print(f"   Packages: {len(package_map)}")
        print(f"   Trainers: {len(trainer_map)}")

if __name__ == '__main__':
    import_data()
