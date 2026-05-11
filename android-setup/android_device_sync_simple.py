"""
Android Device Sync Service - SIMPLE VERSION
This version connects and disconnects for EACH sync to avoid Broken Pipe errors.

Run this on an Android device using Termux.
"""
import os
import sys
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import ZKTeco library
try:
    from zk import ZK
    logger.info("✓ ZKTeco library (pyzk) loaded successfully")
except ImportError as e:
    logger.error("✗ Failed to import pyzk library. Install it with: pip install pyzk")
    sys.exit(1)

# Configuration
PYTHONANYWHERE_URL = os.getenv('PYTHONANYWHERE_URL', 'https://habibworkspace.pythonanywhere.com')
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 5))  # 5 seconds default
DEVICE_IP = os.getenv('BIOMETRIC_DEVICE_IP', '192.168.0.201')
DEVICE_PORT = int(os.getenv('BIOMETRIC_DEVICE_PORT', 4270))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')


class SimpleAndroidSync:
    """Simple sync that connects/disconnects each time - avoids Broken Pipe."""
    
    def __init__(self):
        self.api_token = None
        self.synced_records = set()  # Track synced records by timestamp+user_id
        self.sync_count = 0
        self.error_count = 0
        self.last_heartbeat = 0  # Track last heartbeat time
        
    def send_heartbeat(self):
        """Send heartbeat to server to indicate sync script is alive."""
        try:
            # Only send heartbeat every 30 seconds
            current_time = time.time()
            if current_time - self.last_heartbeat < 30:
                return
            
            headers = {'Content-Type': 'application/json'}
            payload = {'device_ip': DEVICE_IP}
            
            response = requests.post(
                f'{PYTHONANYWHERE_URL}/api/attendance/heartbeat',
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                self.last_heartbeat = current_time
                logger.debug("✓ Heartbeat sent")
            else:
                logger.warning(f"⚠ Heartbeat failed: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")
        
    def authenticate(self):
        """Get JWT token from PythonAnywhere backend."""
        try:
            logger.info(f"Authenticating with {PYTHONANYWHERE_URL}...")
            
            response = requests.post(
                f'{PYTHONANYWHERE_URL}/api/auth/login',
                json={'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.api_token = data.get('access_token')
                logger.info(f"✓ Authenticated with PythonAnywhere")
                return True
            else:
                logger.error(f"✗ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"✗ Authentication error: {e}")
            return False
    
    def fetch_and_sync(self):
        """Connect, fetch, sync, disconnect - all in one go."""
        conn = None
        zk = None
        
        try:
            # Create new connection (UDP mode for Android)
            logger.info(f"Connecting to {DEVICE_IP}:{DEVICE_PORT}...")
            zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=10, force_udp=True, ommit_ping=True)
            conn = zk.connect()
            
            if not conn:
                logger.error("✗ Failed to connect to device")
                return 0
            
            logger.info("✓ Connected to device")
            
            # Get device serial
            try:
                device_serial = conn.get_serialnumber()
            except:
                device_serial = "UNKNOWN"
            
            # Fetch attendance logs
            attendances = conn.get_attendance()
            logger.info(f"Fetched {len(attendances)} total records from device")
            
            # Disconnect immediately after fetching
            conn.disconnect()
            logger.info("✓ Disconnected from device")
            
            # Process and sync new records
            synced_count = 0
            headers = {'Authorization': f'Bearer {self.api_token}'}
            
            for att in attendances:
                try:
                    # Create unique key for this record
                    record_key = f"{att.user_id}_{att.timestamp.isoformat()}"
                    
                    # Skip if already synced
                    if record_key in self.synced_records:
                        continue
                    
                    # Prepare payload
                    payload = {
                        'device_user_id': str(att.user_id),
                        'timestamp': att.timestamp.isoformat(),
                        'device_serial': device_serial
                    }
                    
                    # Send to PythonAnywhere
                    response = requests.post(
                        f'{PYTHONANYWHERE_URL}/api/attendance/sync-log',
                        json=payload,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        self.synced_records.add(record_key)
                        synced_count += 1
                        self.sync_count += 1
                        logger.info(f"✓ Synced: User {att.user_id} at {att.timestamp}")
                    elif response.status_code == 404:
                        # No mapping found - mark as synced to avoid retrying
                        self.synced_records.add(record_key)
                        logger.warning(f"⚠ No mapping for device user {att.user_id}")
                    else:
                        logger.error(f"✗ Sync failed: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"✗ Error syncing record: {e}")
                    continue
            
            if synced_count > 0:
                logger.info(f"✓ Synced {synced_count} new records (Total: {self.sync_count})")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            self.error_count += 1
            return 0
            
        finally:
            # Always disconnect
            try:
                if conn:
                    conn.disconnect()
            except:
                pass
    
    def run(self):
        """Main sync loop."""
        logger.info("=" * 60)
        logger.info("Android Device Sync Service - SIMPLE VERSION")
        logger.info("=" * 60)
        logger.info(f"Device: {DEVICE_IP}:{DEVICE_PORT}")
        logger.info(f"Remote: {PYTHONANYWHERE_URL}")
        logger.info(f"Sync Interval: {SYNC_INTERVAL}s")
        logger.info(f"Mode: UDP (Android optimized)")
        logger.info("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            logger.error("Failed to authenticate. Exiting.")
            return
        
        logger.info("\nStarting sync loop... (Press Ctrl+C to stop)")
        logger.info("This version connects/disconnects each time to avoid Broken Pipe")
        logger.info("")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"--- Cycle {cycle_count} ---")
                
                # Send heartbeat to indicate we're alive
                self.send_heartbeat()
                
                self.fetch_and_sync()
                
                # Status every 10 cycles
                if cycle_count % 10 == 0:
                    logger.info("=" * 60)
                    logger.info(f"Status: Synced {self.sync_count} | Errors {self.error_count}")
                    logger.info("=" * 60)
                
                time.sleep(SYNC_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n\nStopping sync service...")
            logger.info(f"Final stats: Synced {self.sync_count} | Errors {self.error_count}")
            logger.info("✓ Sync service stopped")


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'PYTHONANYWHERE_URL',
        'ADMIN_USERNAME',
        'ADMIN_PASSWORD',
        'BIOMETRIC_DEVICE_IP',
        'BIOMETRIC_DEVICE_PORT'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("✗ Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("\nPlease create a .env file with all required variables.")
        return False
    
    logger.info("✓ All required environment variables are set")
    return True


if __name__ == '__main__':
    logger.info("Starting Android Device Sync Service (Simple Version)...")
    logger.info(f"Python version: {sys.version}")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Start sync service
    sync_service = SimpleAndroidSync()
    sync_service.run()
