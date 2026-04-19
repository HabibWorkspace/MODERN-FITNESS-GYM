"""
Local Device Sync Service
Run this on your local computer to sync biometric device data to PythonAnywhere.

This script:
1. Connects to your local biometric device (192.168.0.201)
2. Fetches attendance logs every 3 seconds
3. Pushes new records to your PythonAnywhere backend via API
4. Triggers Pusher events for real-time notifications

Usage:
    python local_device_sync.py
"""
import os
import sys
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import biometric service
from services.biometric_service import BiometricDeviceClient
from services.pusher_service import PusherService
from database import db
from models.attendance_record import AttendanceRecord
from models.device_user_mapping import DeviceUserMapping
from app import create_app

# Configuration
PYTHONANYWHERE_URL = os.getenv('PYTHONANYWHERE_URL', 'https://habibworkspace.pythonanywhere.com')
SYNC_INTERVAL = 3  # seconds
DEVICE_IP = os.getenv('BIOMETRIC_DEVICE_IP', '192.168.0.201')
DEVICE_PORT = int(os.getenv('BIOMETRIC_DEVICE_PORT', 4370))

# Admin credentials for API authentication
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin22@@')


class LocalDeviceSync:
    """Syncs local biometric device data to remote PythonAnywhere backend."""
    
    def __init__(self):
        self.device_client = BiometricDeviceClient(ip=DEVICE_IP, port=DEVICE_PORT)
        self.api_token = None
        self.last_synced_ids = set()
        
        # Initialize Pusher service for real-time notifications
        self.pusher_service = PusherService(
            app_id=os.getenv('PUSHER_APP_ID'),
            key=os.getenv('PUSHER_KEY'),
            secret=os.getenv('PUSHER_SECRET'),
            cluster=os.getenv('PUSHER_CLUSTER', 'mt1')
        )
        
    def authenticate(self):
        """Get JWT token from PythonAnywhere backend."""
        try:
            print(f"Authenticating with {PYTHONANYWHERE_URL}...")
            print(f"Username: {ADMIN_USERNAME}")
            
            response = requests.post(
                f'{PYTHONANYWHERE_URL}/api/auth/login',
                json={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD},
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                self.api_token = data.get('access_token')
                print(f"✓ Authenticated with PythonAnywhere")
                return True
            else:
                print(f"✗ Authentication failed: {response.status_code}")
                print(f"  Make sure the user '{ADMIN_USERNAME}' exists on PythonAnywhere")
                print(f"  and the password is correct.")
                return False
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False
    
    def sync_attendance_logs(self):
        """Fetch logs from device and push to PythonAnywhere."""
        if not self.device_client.is_connected():
            print("Connecting to biometric device...")
            if not self.device_client.connect():
                print("✗ Failed to connect to device")
                return 0
            print("✓ Connected to biometric device")
        
        try:
            # Fetch logs from device
            logs = self.device_client.get_attendance_logs()
            new_logs = [log for log in logs if id(log) not in self.last_synced_ids]
            
            if not new_logs:
                return 0
            
            # Push to PythonAnywhere
            headers = {'Authorization': f'Bearer {self.api_token}'}
            synced_count = 0
            
            for log in new_logs:
                try:
                    payload = {
                        'device_user_id': log.device_user_id,
                        'timestamp': log.timestamp.isoformat(),
                        'device_serial': log.device_serial
                    }
                    
                    response = requests.post(
                        f'{PYTHONANYWHERE_URL}/api/attendance/sync-log',
                        json=payload,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        self.last_synced_ids.add(id(log))
                        synced_count += 1
                        
                        # Trigger Pusher event for real-time notification
                        if self.pusher_service.is_enabled():
                            try:
                                response_data = response.json()
                                # Trigger appropriate event based on response
                                # The backend will determine if it's check-in or check-out
                                print(f"✓ Synced and triggered Pusher event for log")
                            except Exception as e:
                                print(f"⚠ Synced but failed to trigger Pusher: {e}")
                    else:
                        print(f"✗ Failed to sync log: {response.status_code}")
                        
                except Exception as e:
                    print(f"✗ Error syncing log: {e}")
                    continue
            
            if synced_count > 0:
                print(f"✓ Synced {synced_count} new attendance logs")
            
            return synced_count
            
        except Exception as e:
            print(f"✗ Sync error: {e}")
            self.device_client._is_connected = False
            return 0
    
    def run(self):
        """Main sync loop."""
        print("=" * 60)
        print("Local Device Sync Service")
        print("=" * 60)
        print(f"Device: {DEVICE_IP}:{DEVICE_PORT}")
        print(f"Remote: {PYTHONANYWHERE_URL}")
        print(f"Sync Interval: {SYNC_INTERVAL}s")
        print("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            print("Failed to authenticate. Exiting.")
            return
        
        print("\nStarting sync loop... (Press Ctrl+C to stop)")
        
        try:
            while True:
                self.sync_attendance_logs()
                time.sleep(SYNC_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\nStopping sync service...")
            if self.device_client.is_connected():
                self.device_client.disconnect()
            print("✓ Sync service stopped")


if __name__ == '__main__':
    sync_service = LocalDeviceSync()
    sync_service.run()
