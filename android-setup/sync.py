"""
Android Device Sync Service - ULTRA STABLE VERSION
Maintains PERMANENT connection with no auto-reconnect.
Only reconnects on actual errors.

Run this on an Android device using Termux.
"""
import os
import sys
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import struct

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
SYNC_INTERVAL = 2  # 2 seconds for real-time
DEVICE_IP = os.getenv('BIOMETRIC_DEVICE_IP', '192.168.0.201')
DEVICE_PORT = int(os.getenv('BIOMETRIC_DEVICE_PORT', 4370))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Connection settings - PERMANENT CONNECTION
DEVICE_TIMEOUT = 8  # Increased timeout to avoid timeout errors
MAX_CONSECUTIVE_ERRORS = 10  # High tolerance before reconnecting
RECONNECT_DELAY = 3  # Quick reconnection when needed


class UltraStableSync:
    """Ultra stable sync with PERMANENT connection."""
    
    def __init__(self):
        self.api_token = None
        self.synced_records = set()
        self.last_sync_time = datetime.now() - timedelta(hours=24)
        self.sync_count = 0
        self.error_count = 0
        self.consecutive_errors = 0
        self.last_heartbeat = 0
        self.connection_start_time = 0
        
        # Connection objects
        self.zk = None
        self.conn = None
        
        # Error tracking
        self.unpack_errors = 0
        self.timeout_errors = 0
        
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
                logger.info(f"✓ Authenticated successfully")
                return True
            else:
                logger.error(f"✗ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"✗ Authentication error: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to server."""
        try:
            current_time = time.time()
            if current_time - self.last_heartbeat < 30:
                return
            
            headers = {'Content-Type': 'application/json'}
            payload = {'device_ip': DEVICE_IP}
            
            response = requests.post(
                f'{PYTHONANYWHERE_URL}/api/attendance/heartbeat',
                json=payload,
                headers=headers,
                timeout=3
            )
            
            if response.status_code == 200:
                self.last_heartbeat = current_time
                logger.debug("✓ Heartbeat sent")
                
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")
    
    def connect_to_device(self):
        """Establish PERMANENT connection to biometric device."""
        try:
            logger.info(f"Connecting to {DEVICE_IP}:{DEVICE_PORT}...")
            
            # Create ZK instance with optimized settings for stability
            self.zk = ZK(
                DEVICE_IP, 
                port=DEVICE_PORT, 
                timeout=DEVICE_TIMEOUT,
                force_udp=True,  # UDP is more stable on Android
                ommit_ping=False  # Enable ping for connection check
            )
            
            # Connect
            self.conn = self.zk.connect()
            
            if not self.conn:
                logger.error("✗ Failed to connect")
                return False
            
            # Test connection
            try:
                serial = self.conn.get_serialnumber()
                logger.info(f"✓ PERMANENT CONNECTION ESTABLISHED (Serial: {serial})")
            except:
                logger.info("✓ PERMANENT CONNECTION ESTABLISHED")
            
            self.connection_start_time = time.time()
            self.consecutive_errors = 0
            self.unpack_errors = 0
            self.timeout_errors = 0
            
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
                logger.info("✓ Disconnected")
        except Exception as e:
            logger.debug(f"Disconnect error (ignored): {e}")
        finally:
            self.conn = None
            self.zk = None
    
    def should_reconnect(self):
        """Only reconnect on ACTUAL failures, not on timers."""
        # Only reconnect if too many consecutive errors
        if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            logger.error(f"⚠ {self.consecutive_errors} consecutive errors - FORCED RECONNECT")
            return True
        
        # Only reconnect if no connection
        if not self.conn:
            logger.warning("⚠ No connection - reconnecting...")
            return True
        
        # NO AUTO-RECONNECT based on time
        return False
    
    def fetch_and_sync(self):
        """Fetch recent attendance logs and sync immediately."""
        try:
            # Check if we MUST reconnect (only on errors)
            if self.should_reconnect():
                self.disconnect_from_device()
                time.sleep(RECONNECT_DELAY)
                if not self.connect_to_device():
                    self.consecutive_errors += 1
                    return 0
            
            # Ensure connection
            if not self.conn:
                if not self.connect_to_device():
                    self.consecutive_errors += 1
                    return 0
            
            # Get device serial
            try:
                device_serial = self.conn.get_serialnumber()
            except:
                device_serial = "ANDROID_SYNC"
            
            # Fetch attendance logs with error handling
            try:
                attendances = self.conn.get_attendance()
                
                # Filter to only recent records (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                recent_attendances = [
                    att for att in attendances 
                    if att.timestamp >= cutoff_time
                ]
                
                logger.debug(f"Fetched {len(recent_attendances)} recent records")
                
            except struct.error as e:
                # Handle "unpack requires a buffer of 4 bytes" error
                self.unpack_errors += 1
                logger.warning(f"⚠ Unpack error #{self.unpack_errors}: {e}")
                
                # If too many unpack errors, reconnect
                if self.unpack_errors >= 5:
                    logger.error("Too many unpack errors - reconnecting...")
                    self.consecutive_errors = MAX_CONSECUTIVE_ERRORS
                    return 0
                
                # Otherwise, just skip this cycle
                return 0
                
            except TimeoutError as e:
                # Handle timeout errors
                self.timeout_errors += 1
                logger.warning(f"⚠ Timeout error #{self.timeout_errors}: {e}")
                
                # If too many timeouts, reconnect
                if self.timeout_errors >= 3:
                    logger.error("Too many timeout errors - reconnecting...")
                    self.consecutive_errors = MAX_CONSECUTIVE_ERRORS
                    return 0
                
                # Otherwise, just skip this cycle
                return 0
                
            except Exception as e:
                logger.error(f"✗ Failed to fetch attendance: {e}")
                self.consecutive_errors += 1
                return 0
            
            # Process and sync new records IMMEDIATELY
            synced_count = 0
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            for att in recent_attendances:
                try:
                    # Create unique key
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
                    
                    # Send to server
                    response = requests.post(
                        f'{PYTHONANYWHERE_URL}/api/attendance/sync-log',
                        json=payload,
                        headers=headers,
                        timeout=5
                    )
                    
                    if response.status_code in [200, 201]:
                        self.synced_records.add(record_key)
                        synced_count += 1
                        self.sync_count += 1
                        logger.info(f"✓ SYNCED: User {att.user_id} at {att.timestamp.strftime('%H:%M:%S')}")
                    elif response.status_code == 404:
                        self.synced_records.add(record_key)
                        logger.warning(f"⚠ No mapping for user {att.user_id}")
                    else:
                        logger.error(f"✗ Sync failed: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"✗ Error syncing record: {e}")
            
            if synced_count > 0:
                logger.info(f"🚀 SYNCED {synced_count} records | Total: {self.sync_count}")
            
            # Reset error counters on success
            self.consecutive_errors = 0
            self.unpack_errors = 0
            self.timeout_errors = 0
            
            # Clean up old synced records
            if len(self.synced_records) > 1000:
                records_list = list(self.synced_records)
                self.synced_records = set(records_list[-800:])
                logger.debug("Cleaned up synced records cache")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"✗ Sync error: {e}")
            self.consecutive_errors += 1
            self.error_count += 1
            return 0
    
    def run(self):
        """Main sync loop - PERMANENT CONNECTION MODE."""
        logger.info("=" * 70)
        logger.info("🔒 ULTRA STABLE Android Device Sync - PERMANENT CONNECTION")
        logger.info("=" * 70)
        logger.info(f"Device: {DEVICE_IP}:{DEVICE_PORT}")
        logger.info(f"Remote: {PYTHONANYWHERE_URL}")
        logger.info(f"Sync Interval: {SYNC_INTERVAL}s")
        logger.info(f"Device Timeout: {DEVICE_TIMEOUT}s")
        logger.info(f"Mode: UDP + PERMANENT CONNECTION (No Auto-Reconnect)")
        logger.info("=" * 70)
        
        # Authenticate
        if not self.authenticate():
            logger.error("Failed to authenticate. Exiting.")
            return
        
        # Initial connection
        if not self.connect_to_device():
            logger.error("Failed to connect to device. Exiting.")
            return
        
        logger.info("\n🔒 PERMANENT CONNECTION ACTIVE - Will NOT auto-disconnect")
        logger.info("Only reconnects on actual errors (not on timers)")
        logger.info("Press Ctrl+C to stop\n")
        
        cycle_count = 0
        last_status_time = time.time()
        
        try:
            while True:
                cycle_count += 1
                
                # Send heartbeat
                self.send_heartbeat()
                
                # Fetch and sync
                self.fetch_and_sync()
                
                # Status every 60 seconds
                current_time = time.time()
                if current_time - last_status_time >= 60:
                    uptime = int(current_time - self.connection_start_time) if self.conn else 0
                    uptime_mins = uptime // 60
                    uptime_secs = uptime % 60
                    
                    logger.info("=" * 70)
                    logger.info(f"📊 Status: Synced {self.sync_count} | Errors {self.error_count}")
                    logger.info(f"🔒 Connection Uptime: {uptime_mins}m {uptime_secs}s (PERMANENT)")
                    logger.info(f"⚠️  Unpack Errors: {self.unpack_errors} | Timeout Errors: {self.timeout_errors}")
                    logger.info("=" * 70)
                    
                    last_status_time = current_time
                
                time.sleep(SYNC_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n\n⏹ Stopping sync service...")
            self.disconnect_from_device()
            
            total_uptime = int(time.time() - self.connection_start_time)
            uptime_mins = total_uptime // 60
            uptime_secs = total_uptime % 60
            
            logger.info(f"📊 Final: Synced {self.sync_count} | Errors {self.error_count}")
            logger.info(f"🔒 Total Uptime: {uptime_mins}m {uptime_secs}s")
            logger.info("✓ Service stopped")


def check_environment():
    """Check environment variables."""
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
        logger.error(f"✗ Missing: {', '.join(missing)}")
        logger.error("Create .env file with required variables")
        return False
    
    return True


if __name__ == '__main__':
    if not check_environment():
        sys.exit(1)
    
    sync = UltraStableSync()
    sync.run()
