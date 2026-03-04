"""Create missing transactions for members who don't have any."""
import sqlite3
import os
from datetime import datetime, timedelta

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'fitnix.db')

def create_missing_transactions():
    """Create admission transactions for members who don't have any."""
    print(f"🔧 Connecting to database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Find members without transactions
        cursor.execute("""
            SELECT 
                mp.id,
                mp.member_number,
                mp.full_name,
                mp.admission_date,
                mp.current_package_id,
                mp.package_start_date,
                mp.package_expiry_date
            FROM member_profiles mp
            LEFT JOIN transactions t ON mp.id = t.member_id
            WHERE t.id IS NULL
            GROUP BY mp.id
        """)
        
        members_without_transactions = cursor.fetchall()
        
        if not members_without_transactions:
            print("✅ All members have transactions!")
            return
        
        print(f"\n📋 Found {len(members_without_transactions)} members without transactions:")
        
        for member in members_without_transactions:
            member_id, member_number, full_name, admission_date, package_id, pkg_start, pkg_expiry = member
            print(f"   - {full_name} (ID: {member_number})")
        
        print("\n🔨 Creating transactions...")
        
        created_count = 0
        for member in members_without_transactions:
            member_id, member_number, full_name, admission_date, package_id, pkg_start, pkg_expiry = member
            
            # Get package price
            package_price = 0
            if package_id:
                cursor.execute("SELECT price FROM packages WHERE id = ?", (package_id,))
                pkg_result = cursor.fetchone()
                if pkg_result:
                    package_price = float(pkg_result[0])
            
            # Calculate due date
            if pkg_expiry:
                due_date = pkg_expiry
            elif pkg_start:
                # If no expiry but has start, add 30 days
                due_date = datetime.fromisoformat(pkg_start.replace('Z', '')) + timedelta(days=30)
                due_date = due_date.isoformat()
            else:
                # Default to 7 days from now
                due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
            
            # Default admission fee (you can adjust this)
            admission_fee = 5000
            total_amount = admission_fee + package_price
            
            # Create transaction
            import uuid
            transaction_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            
            cursor.execute("""
                INSERT INTO transactions (
                    id, member_id, amount, transaction_type, status,
                    due_date, paid_date, trainer_fee, package_price,
                    discount_amount, discount_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id,
                member_id,
                total_amount,
                'ADMISSION',
                'PENDING',
                due_date,
                None,  # paid_date
                0,     # trainer_fee
                package_price,
                0,     # discount_amount
                'fixed',
                created_at
            ))
            
            created_count += 1
            print(f"   ✅ Created transaction for {full_name} - Amount: Rs. {total_amount}, Due: {due_date}")
        
        conn.commit()
        print(f"\n✅ Successfully created {created_count} transactions!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_missing_transactions()
