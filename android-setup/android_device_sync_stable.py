"""
Android Device Sync Service - STABLE VERSION
Maintains persistent connection with smart reconnection logic.

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
DEVICE_PORT = int(os.getenv('BIOMETRIC_DEVICE_PORT', 4370))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Connection settings
MAX_CONNECTION_AGE = 300  # Reconnect every 5 minutes (300 seconds)
MAX_CONSECUTIVE_ERRORS = 3  # Reconnect after 3 consecutive errors
RECONNECT_DELAY = 10  # Wait 10 seconds before reconnecting


class StableAndroidSync:
    """Stable sync with persistent connection and smart reconnection."""
    
    def __init__(self):
        self.api_token = None
        self.synced_records = set()  # Track synced records by timestamp+user_id
        self.sync_count = 0
        self.error_count = 0
        self.consecutive_errors = 0
        self.last_heartbeat = 0
        self.connection_start_time = 0
        
        # Connection objects
        self.zk = None
        self.conn = None
        
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
    
    def connect_to_device(self):
        """Establish connection to biometric device."""
        try:
            logger.info(f"Connecting to device {DEVICE_IP}:{DEVICE_PORT}...")
            
            # Create ZK instance with UDP mode for Android
            self.zk = ZK(
                DEVICE_IP, 
                port=DEVICE_PORT, 
                timeout=15,  # Increased timeout
                force_udp=True,
                ommit_ping=True
            )
            
            # Connect
            self.conn = self.zk.connect()
            
            if not self.conn:
                logger.error("✗ Failed to connect to device")
                return False
            
            # Test connection by getting serial number
            try:
                serial = self.conn.get_serialnumber()
                logger.info(f"✓ Connected to device (Serial: {serial})")
            except:
                logger.info("✓ Connected to device")
            
            self.connection_start_time = time.time()
            self.consecutive_errors = 0
            return True
            
        except Exception as e:
            logger.error(f"✗ Connection error: {e}")
            self.conn = None
            self.zk = None
            return False
    
    def disconnect_from_device(self):
        """Safely disconnect from device."""
        try:
            if self.conn:
                self.conn.disconnect()
                logger.info("✓ Disconnected from device")
        except Exception as e:
            logger.debug(f"Disconnect error (ignored): {e}")
        finally:
            self.conn = None
            self.zk = None
    
    def should_reconnect(self):
        """Check if we should reconnect to the device."""
        # Reconnect if too many consecutive errors
        if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            logger.warning(f"⚠ {self.consecutive_errors} consecutive errors - reconnecting...")
            return True
        
        # Reconnect if connection is too old
        if self.conn and (time.time() - self.connection_start_time) > MAX_CONNECTION_AGE:
            logger.info(f"ℹ Connection age exceeded {MAX_CONNECTION_AGE}s - reconnecting...")
            return True
        
        # Reconnect if no connection
        if not self.conn:
            return True
        
        return False
    
    def fetch_and_sync(self):
        """Fetch attendance logs and sync to server."""
        try:
            # Check if we need to reconnect
            if self.should_reconnect():
                self.disconnect_from_device()
                time.sleep(RECONNECT_DELAY)
                if not self.connect_to_device():
                    self.consecutive_errors += 1
                    return 0
            
            # Ensure we have a connection
            if not self.conn:
                if not self.connect_to_device():
                    self.consecutive_errors += 1
                    return 0
            
            # Get device serial
            try:
                device_serial = self.conn.get_serialnumber()
            except:
                device_serial = "UNKNOWN"
            
            # Fetch attendance logs
            try:
                attendances = self.conn.get_attendance()
                logger.debug(f"Fetched {len(attendances)} total records from device")
            except Exception as e:
                logger.error(f"✗ Failed to fetch attendance: {e}")
                self.consecutive_errors += 1
                return 0
            
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
            
            if synced_count > 0:
                logger.info(f"✓ Synced {synced_count} new records (Total: {self.sync_count})")
            
            # Reset consecutive errors on success
            self.consecutive_errors = 0
            return synced_count
            
        except Exception as e:
            logger.error(f"✗ Sync error: {e}")
            self.consecutive_errors += 1
            self.error_count += 1
            return 0
    
    def run(self):
        """Main sync loop."""
        logger.info("=" * 60)
        logger.info("Android Device Sync Service - STABLE VERSION")
        logger.info("=" * 60)
        logger.info(f"Device: {DEVICE_IP}:{DEVICE_PORT}")
        logger.info(f"Remote: {PYTHONANYWHERE_URL}")
        logger.info(f"Sync Interval: {SYNC_INTERVAL}s")
        logger.info(f"Reconnect Interval: {MAX_CONNECTION_AGE}s")
        logger.info(f"Mode: UDP (Android optimized)")
        logger.info("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            logger.error("Failed to authenticate. Exiting.")
            return
        
        # Initial connection
        if not self.connect_to_device():
            logger.error("Failed to connect to device. Exiting.")
            return
        
        logger.info("\nStarting sync loop... (Press Ctrl+C to stop)")
        logger.info("Connection will auto-reconnect every 5 minutes or on errors")
        logger.info("")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.debug(f"--- Cycle {cycle_count} ---")
                
                # Send heartbeat
                self.send_heartbeat()
                
                # Fetch and sync
                self.fetch_and_sync()
                
                # Status every 20 cycles (approx 100 seconds)
                if cycle_count % 20 == 0:
                    connection_age = int(time.time() - self.connection_start_time) if self.conn else 0
                    logger.info("=" * 60)
                    logger.info(f"Status: Synced {self.sync_count} | Errors {self.error_count} | Connection Age: {connection_age}s")
                    logger.info("=" * 60)
                
                time.sleep(SYNC_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n\nStopping sync service...")
            self.disconnect_from_device()
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
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"✗ Missing required environment variables: {', '.join(missing)}")
        logger.error("Please create a .env file with all required variables")
        return False
    
    return True


if __name__ == '__main__':
    if not check_environment():
        sys.exit(1)
    
    sync = StableAndroidSync()
    sync.run()
