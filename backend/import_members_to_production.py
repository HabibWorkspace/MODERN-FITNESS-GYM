"""Import members from local database to production database."""
import sqlite3
import sys

# Connect to production database
try:
    conn = sqlite3.connect('instance/fitnix.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    print("✅ Connected to production database")
except Exception as e:
    print(f"❌ Error connecting to database: {e}")
    sys.exit(1)

# Check if is_active column exists
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]
has_is_active = 'is_active' in columns
print(f"Database has is_active column: {has_is_active}")

# Read the export file
try:
    with open('members_export.sql', 'r', encoding='utf-8') as f:
        content = f.read()
    print("✅ Read export file")
except Exception as e:
    print(f"❌ Error reading export file: {e}")
    sys.exit(1)

# Parse and modify INSERT statements
lines = content.split('\n')
users_inserted = 0
profiles_inserted = 0
transactions_inserted = 0
errors = 0

for line in lines:
    if not line.strip() or line.startswith('--'):
        continue
    
    try:
        if line.startswith('INSERT INTO users'):
            # Check if user already exists
            user_id = line.split("'")[1]
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if cursor.fetchone():
                continue  # Skip if user already exists
            
            # Add is_active column if needed
            if has_is_active:
                line = line.replace(
                    'INSERT INTO users (id, username, password_hash, role, created_at, updated_at)',
                    'INSERT INTO users (id, username, password_hash, role, created_at, updated_at, is_active)'
                )
                line = line.replace(');', ', 1);')
            
            cursor.execute(line)
            users_inserted += 1
            
        elif line.startswith('INSERT INTO member_profiles'):
            # Check if profile already exists
            profile_id = line.split("'")[1]
            cursor.execute("SELECT id FROM member_profiles WHERE id = ?", (profile_id,))
            if cursor.fetchone():
                continue  # Skip if profile already exists
            
            # Extract member_number more carefully
            try:
                # Find the VALUES part
                values_part = line.split('VALUES (')[1]
                # Split by comma and get the third value (member_number)
                values = values_part.split(', ')
                member_number_str = values[2].strip()
                
                if member_number_str != 'NULL':
                    member_number = int(member_number_str)
                    cursor.execute("SELECT id FROM member_profiles WHERE member_number = ?", (member_number,))
                    if cursor.fetchone():
                        # Find next available member number
                        cursor.execute("SELECT MAX(member_number) FROM member_profiles")
                        max_num = cursor.fetchone()[0] or 0
                        new_number = max_num + 1
                        # Replace the member number in the line
                        values[2] = str(new_number)
                        values_part = ', '.join(values)
                        line = line.split('VALUES (')[0] + 'VALUES (' + values_part
                        print(f"  ⚠️  Member number {member_number} already exists, using {new_number}")
            except (ValueError, IndexError) as e:
                pass  # If parsing fails, just try to insert as-is
            
            cursor.execute(line)
            profiles_inserted += 1
            
        elif line.startswith('INSERT INTO transactions'):
            # Check if transaction already exists
            txn_id = line.split("'")[1]
            cursor.execute("SELECT id FROM transactions WHERE id = ?", (txn_id,))
            if cursor.fetchone():
                continue  # Skip if transaction already exists
            
            cursor.execute(line)
            transactions_inserted += 1
            
    except Exception as e:
        errors += 1
        if errors <= 5:  # Only show first 5 errors
            print(f"  ⚠️  Error: {str(e)[:100]}")

# Commit changes
conn.commit()
conn.close()

print("\n" + "="*60)
print("IMPORT SUMMARY")
print("="*60)
print(f"✅ Users inserted: {users_inserted}")
print(f"✅ Member profiles inserted: {profiles_inserted}")
print(f"✅ Transactions inserted: {transactions_inserted}")
if errors > 0:
    print(f"⚠️  Errors encountered: {errors}")
print("="*60)
print("\n✅ Import complete!")
