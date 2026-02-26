"""Export all members from local database to production-ready SQL."""
import sqlite3
import json
from datetime import datetime

# Connect to local database
conn = sqlite3.connect('instance/fitnix.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all users with role MEMBER
cursor.execute("SELECT * FROM users WHERE role = 'MEMBER'")
users = cursor.fetchall()

# Get all member profiles
cursor.execute("SELECT * FROM member_profiles")
profiles = cursor.fetchall()

# Get all transactions
cursor.execute("SELECT * FROM transactions")
transactions = cursor.fetchall()

print(f"Found {len(users)} member users")
print(f"Found {len(profiles)} member profiles")
print(f"Found {len(transactions)} transactions")

# Create SQL export file
with open('members_export.sql', 'w', encoding='utf-8') as f:
    f.write("-- Member Data Export\n")
    f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"-- Total Members: {len(users)}\n\n")
    
    # Export users
    f.write("-- Insert Users\n")
    for user in users:
        username = user['username'].replace("'", "''")
        f.write(f"INSERT INTO users (id, username, password_hash, role, created_at, updated_at) VALUES (")
        f.write(f"'{user['id']}', ")
        f.write(f"'{username}', ")
        f.write(f"'{user['password_hash']}', ")
        f.write(f"'{user['role']}', ")
        f.write(f"'{user['created_at']}', ")
        f.write(f"'{user['updated_at']}');\n")
    
    f.write("\n-- Insert Member Profiles\n")
    for profile in profiles:
        full_name = profile['full_name'].replace("'", "''")
        f.write(f"INSERT INTO member_profiles (id, user_id, member_number, full_name, phone, cnic, email, gender, date_of_birth, admission_date, admission_fee_paid, current_package_id, trainer_id, package_start_date, package_expiry_date, is_frozen, profile_picture, created_at, updated_at) VALUES (")
        f.write(f"'{profile['id']}', ")
        f.write(f"'{profile['user_id']}', ")
        f.write(f"{profile['member_number'] if profile['member_number'] else 'NULL'}, ")
        f.write(f"'{full_name}', ")
        f.write(f"'{profile['phone'] if profile['phone'] else ''}', ")
        f.write(f"'{profile['cnic'] if profile['cnic'] else ''}', ")
        f.write(f"'{profile['email'] if profile['email'] else ''}', ")
        f.write(f"'{profile['gender'] if profile['gender'] else ''}', ")
        f.write(f"'{profile['date_of_birth'] if profile['date_of_birth'] else ''}', ")
        f.write(f"'{profile['admission_date'] if profile['admission_date'] else ''}', ")
        f.write(f"{1 if profile['admission_fee_paid'] else 0}, ")
        f.write(f"'{profile['current_package_id'] if profile['current_package_id'] else ''}', ")
        f.write(f"'{profile['trainer_id'] if profile['trainer_id'] else ''}', ")
        f.write(f"'{profile['package_start_date'] if profile['package_start_date'] else ''}', ")
        f.write(f"'{profile['package_expiry_date'] if profile['package_expiry_date'] else ''}', ")
        f.write(f"{1 if profile['is_frozen'] else 0}, ")
        f.write(f"'{profile['profile_picture'] if profile['profile_picture'] else ''}', ")
        f.write(f"'{profile['created_at']}', ")
        f.write(f"'{profile['updated_at']}');\n")
    
    f.write("\n-- Insert Transactions\n")
    for txn in transactions:
        f.write(f"INSERT INTO transactions (id, member_id, amount, transaction_type, status, due_date, paid_date, package_price, trainer_fee, discount_amount, discount_type, created_at) VALUES (")
        f.write(f"'{txn['id']}', ")
        f.write(f"'{txn['member_id']}', ")
        f.write(f"{txn['amount']}, ")
        f.write(f"'{txn['transaction_type']}', ")
        f.write(f"'{txn['status']}', ")
        f.write(f"'{txn['due_date'] if txn['due_date'] else ''}', ")
        f.write(f"'{txn['paid_date'] if txn['paid_date'] else ''}', ")
        f.write(f"{txn['package_price'] if txn['package_price'] else 0}, ")
        f.write(f"{txn['trainer_fee'] if txn['trainer_fee'] else 0}, ")
        f.write(f"{txn['discount_amount'] if txn['discount_amount'] else 0}, ")
        f.write(f"'{txn['discount_type'] if txn['discount_type'] else ''}', ")
        f.write(f"'{txn['created_at']}');\n")

conn.close()

print("\n✅ Export complete! File saved as: members_export.sql")
print("\nTo import to production:")
print("1. Download the members_export.sql file")
print("2. Go to PythonAnywhere > Databases > Open console for your database")
print("3. Copy and paste the SQL commands from the file")
print("4. Or use: sqlite3 your_database.db < members_export.sql")
