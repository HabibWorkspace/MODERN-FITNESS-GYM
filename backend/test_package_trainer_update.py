"""
Test script to verify package and trainer changes update pending transactions correctly.
Run this after starting the Flask app to test the fix.
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

# Login as admin
def login():
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin22@@"
    })
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_package_change(token):
    """Test that changing a member's package updates pending transactions."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== TEST 1: Package Change ===")
    
    # Get first member
    response = requests.get(f"{BASE_URL}/admin/members?per_page=1", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get members: {response.text}")
        return
    
    members = response.json()['members']
    if not members:
        print("No members found")
        return
    
    member = members[0]
    member_id = member['id']
    print(f"Testing with member: {member['full_name']} (ID: {member_id})")
    print(f"Current package: {member.get('current_package_id')}")
    
    # Get pending transactions for this member
    response = requests.get(f"{BASE_URL}/admin/finance/member-payments-fixed", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get transactions: {response.text}")
        return
    
    pending_txns = [t for t in response.json()['payments'] 
                    if t['member_id'] == member_id and t['status'] == 'PENDING']
    
    print(f"Found {len(pending_txns)} pending transactions")
    if pending_txns:
        print(f"Current pending transaction amount: {pending_txns[0]['amount']}")
        print(f"Package price: {pending_txns[0]['package_price']}, Trainer fee: {pending_txns[0]['trainer_fee']}")
    
    # Get available packages
    response = requests.get(f"{BASE_URL}/packages", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get packages: {response.text}")
        return
    
    packages = response.json()['packages']
    if len(packages) < 2:
        print("Need at least 2 packages to test package change")
        return
    
    # Change to a different package
    new_package = packages[1] if member.get('current_package_id') != packages[1]['id'] else packages[0]
    print(f"\nChanging package to: {new_package['name']} (Price: {new_package['price']})")
    
    response = requests.put(f"{BASE_URL}/admin/members/{member_id}", 
                           headers=headers,
                           json={"package_id": new_package['id']})
    
    if response.status_code != 200:
        print(f"Failed to update member: {response.text}")
        return
    
    print("✓ Package updated successfully")
    
    # Check if pending transactions were updated
    response = requests.get(f"{BASE_URL}/admin/finance/member-payments-fixed", headers=headers)
    updated_txns = [t for t in response.json()['payments'] 
                    if t['member_id'] == member_id and t['status'] == 'PENDING']
    
    if updated_txns:
        print(f"\nAfter package change:")
        print(f"New pending transaction amount: {updated_txns[0]['amount']}")
        print(f"Package price: {updated_txns[0]['package_price']}, Trainer fee: {updated_txns[0]['trainer_fee']}")
        
        if updated_txns[0]['package_price'] == new_package['price']:
            print("✓ TEST PASSED: Package price updated correctly!")
        else:
            print(f"✗ TEST FAILED: Expected package price {new_package['price']}, got {updated_txns[0]['package_price']}")
    else:
        print("No pending transactions to verify")

def test_trainer_add(token):
    """Test that adding a trainer to a member updates pending transactions."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n\n=== TEST 2: Trainer Addition ===")
    
    # Get a member without a trainer
    response = requests.get(f"{BASE_URL}/admin/members?per_page=100", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get members: {response.text}")
        return
    
    members = response.json()['members']
    member_without_trainer = next((m for m in members if not m.get('trainer_id')), None)
    
    if not member_without_trainer:
        print("No member without trainer found. Using first member and removing trainer first.")
        member = members[0]
        member_id = member['id']
        
        # Remove trainer first
        response = requests.put(f"{BASE_URL}/admin/members/{member_id}", 
                               headers=headers,
                               json={"trainer_id": None})
        if response.status_code != 200:
            print(f"Failed to remove trainer: {response.text}")
            return
        print("Removed existing trainer")
    else:
        member = member_without_trainer
        member_id = member['id']
    
    print(f"Testing with member: {member['full_name']} (ID: {member_id})")
    print(f"Current trainer: {member.get('trainer_id')}")
    
    # Get pending transactions
    response = requests.get(f"{BASE_URL}/admin/finance/member-payments-fixed", headers=headers)
    pending_txns = [t for t in response.json()['payments'] 
                    if t['member_id'] == member_id and t['status'] == 'PENDING']
    
    if pending_txns:
        print(f"Current pending transaction amount: {pending_txns[0]['amount']}")
        print(f"Trainer fee: {pending_txns[0]['trainer_fee']}")
    
    # Get available trainers
    response = requests.get(f"{BASE_URL}/admin/trainers", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get trainers: {response.text}")
        return
    
    trainers = response.json()['trainers']
    if not trainers:
        print("No trainers available to test")
        return
    
    trainer = trainers[0]
    print(f"\nAdding trainer: {trainer['full_name']} (Fee: {trainer.get('salary_rate', 0)})")
    
    response = requests.put(f"{BASE_URL}/admin/members/{member_id}", 
                           headers=headers,
                           json={"trainer_id": trainer['id']})
    
    if response.status_code != 200:
        print(f"Failed to update member: {response.text}")
        return
    
    print("✓ Trainer added successfully")
    
    # Check if pending transactions were updated
    response = requests.get(f"{BASE_URL}/admin/finance/member-payments-fixed", headers=headers)
    updated_txns = [t for t in response.json()['payments'] 
                    if t['member_id'] == member_id and t['status'] == 'PENDING']
    
    if updated_txns:
        print(f"\nAfter trainer addition:")
        print(f"New pending transaction amount: {updated_txns[0]['amount']}")
        print(f"Trainer fee: {updated_txns[0]['trainer_fee']}")
        
        expected_fee = float(trainer.get('salary_rate', 0))
        if updated_txns[0]['trainer_fee'] == expected_fee:
            print(f"✓ TEST PASSED: Trainer fee updated correctly to {expected_fee}!")
        else:
            print(f"✗ TEST FAILED: Expected trainer fee {expected_fee}, got {updated_txns[0]['trainer_fee']}")
    else:
        print("No pending transactions to verify")

if __name__ == "__main__":
    print("Starting Package & Trainer Update Tests...")
    print("=" * 50)
    
    token = login()
    if not token:
        print("Failed to login. Exiting.")
        exit(1)
    
    print("✓ Logged in successfully")
    
    try:
        test_package_change(token)
        test_trainer_add(token)
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
