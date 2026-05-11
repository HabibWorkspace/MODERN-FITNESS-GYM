"""
Android Device Sync Service
Run this on an Android device using Termux to sync biometric device data to PythonAnywhere.

This script:
1. Connects to your local biometric device (iFace950 ZKT)
2. Fetches attendance logs every 3 seconds
3. Pushes new records to your PythonAnywhere backend via API
4. Runs continuously in the background

Requirements:
    - Termux (from F-Droid)
    - Python packages: pyzk, requests, python-dotenv
    
Usage:
    python android_device_sync.py
"""
import os
import sys
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging

# Configure logging for Android
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
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 3))  # seconds
DEVICE_IP = os.getenv('BIOMETRIC_DEVICE_IP', '192.168.100.35')
DEVICE_PORT = int(os.getenv('BIOMETRIC_DEVICE_PORT', 4370))

# Admin credentials for API authentication
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Pusher configuration (optional - for real-time notifications)
PUSHER_APP_ID = os.getenv('PUSHER_APP_ID')
PUSHER_KEY = os.getenv('PUSHER_KEY')
PUSHER_SECRET = os.getenv('PUSHER_SECRET')
PUSHER_CLUSTER = os.getenv('PUSHER_CLUSTER', 'mt1')


class AttendanceLog:
    """Data class representing an attendance log entry from the device."""
    
    def __init__(self, device_user_id: str, timestamp: datetime, device_serial: str):
        self.device_user_id = device_user_id
        self.timestamp = timestamp
        self.device_serial = device_serial
    
    def __repr__(self):
        return f"AttendanceLog(device_user_id={self.device_user_id}, timestamp={self.timestamp})"


class BiometricDeviceClient:
    """Lightweight client for ZKTeco iFace950 biometric device - Android optimized."""
    
    def __init__(self, ip: str, port: int, timeout: int = 10):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        # Use UDP mode for Android - more reliable than TCP on Termux
        self.zk = ZK(ip, port=port, timeout=timeout, force_udp=True, ommit_ping=True)
        self.conn = None
        self._is_connected = False
        self.last_connection_time = None
        self.connection_lifetime = 20  # Reconnect every 20 seconds
        self.max_retries = 3
        logger.info(f"BiometricDeviceClient initialized for {ip}:{port} (UDP mode for Android)")
    
    def connect(self) -> bool:
        """Establish connection to the biometric device."""
        for attempt in range(self.max_retries):
            try:
                # Disconnect if already connected
                if self.conn is not None:
                    try:
                        self.conn.disconnect()
                    except:
                        pass
                    self.conn = None
                    time.sleep(0.5)  # Small delay between disconnect and connect
                
                logger.info(f"Attempting to connect to biometric device at {self.ip}:{self.port} (attempt {attempt + 1}/{self.max_retries})")
                
                # Enable keep-alive for the connection
                self.conn = self.zk.connect()
                
                if self.conn:
                    # Test the connection by getting device info
                    try:
                        _ = self.conn.get_serialnumber()
                        self._is_connected = True
                        self.last_connection_time = time.time()
                        logger.info(f"✓ Successfully connected to biometric device")
                        return True
                    except:
                        # Connection established but not working, try again
                        if self.conn:
                            try:
                                self.conn.disconnect()
                            except:
                                pass
                        self.conn = None
                        if attempt < self.max_retries - 1:
                            logger.warning(f"Connection test failed, retrying...")
                            time.sleep(1)
                            continue
                        
            except Exception as e:
                self._is_connected = False
                logger.error(f"✗ Failed to connect (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
        
        self._is_connected = False
        return False
    
    def disconnect(self) -> None:
        """Close device connection."""
        try:
            if self.conn is not None:
                self.conn.disconnect()
                logger.info(f"Disconnected from biometric device")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
        finally:
            self.conn = None
            self._is_connected = False
            self.last_connection_time = None
    
    def get_attendance_logs(self):
        """Fetch all attendance logs from the device."""
        if not self.is_connected():
            raise ConnectionError("Device is not connected. Call connect() first.")
        
        # Check if connection is stale (older than connection_lifetime seconds)
        if self.last_connection_time and (time.time() - self.last_connection_time) > self.connection_lifetime:
            logger.info("Connection is stale, reconnecting...")
            self.disconnect()
            time.sleep(0.5)
            if not self.connect():
                raise ConnectionError("Failed to reconnect to device")
        
        retry_count = 0
        max_retries = 2
        
        while retry_count < max_retries:
            try:
                # Get device serial number
                device_serial = self._get_device_serial()
                
                # Fetch attendance records from device
                attendances = self.conn.get_attendance()
                
                # Convert to AttendanceLog objects
                attendance_logs = []
                for att in attendances:
                    try:
                        log = AttendanceLog(
                            device_user_id=str(att.user_id),
                            timestamp=att.timestamp,
                            device_serial=device_serial
                        )
                        attendance_logs.append(log)
                    except Exception as e:
                        logger.error(f"Error processing attendance entry: {str(e)}")
                        continue
                
                return attendance_logs
                
            except (BrokenPipeError, ConnectionError, OSError, IOError) as e:
                retry_count += 1
                logger.error(f"Connection error (attempt {retry_count}/{max_retries}): {str(e)}")
                self._is_connected = False
                
                if retry_count < max_retries:
                    logger.info("Attempting to reconnect...")
                    self.disconnect()
                    time.sleep(1)
                    if self.connect():
                        logger.info("Reconnected successfully, retrying fetch...")
                        continue
                    else:
                        raise ConnectionError("Failed to reconnect after broken pipe")
                else:
                    raise ConnectionError(f"Failed after {max_retries} attempts")
                    
            except Exception as e:
                logger.error(f"Error fetching attendance logs: {str(e)}")
                self._is_connected = False
                raise
    
    def is_connected(self) -> bool:
        """Check if device connection is active."""
        return self._is_connected and self.conn is not None
    
    def _get_device_serial(self) -> str:
        """Get the serial number of the connected device."""
        try:
            serial = self.conn.get_serialnumber()
            return serial if serial else "UNKNOWN"
        except Exception as e:
            logger.warning(f"Could not retrieve device serial number: {str(e)}")
            return "UNKNOWN"


class AndroidDeviceSync:
    """Syncs local biometric device data to remote PythonAnywhere backend - Android optimized."""
    
    def __init__(self):
        self.device_client = BiometricDeviceClient(ip=DEVICE_IP, port=DEVICE_PORT)
        self.api_token = None
        self.last_synced_ids = set()
        self.sync_count = 0
        self.error_count = 0
        self.last_successful_sync = None
        
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
                logger.error(f"  Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ Authentication error: {e}")
            return False
    
    def sync_attendance_logs(self):
        """Fetch logs from device and push to PythonAnywhere."""
        if not self.device_client.is_connected():
            logger.info("Connecting to biometric device...")
            if not self.device_client.connect():
                logger.error("✗ Failed to connect to device")
                self.error_count += 1
                return 0
            logger.info("✓ Connected to biometric device")
        
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
                        self.sync_count += 1
                        self.last_successful_sync = datetime.now()
                        logger.info(f"✓ Synced attendance log for user {log.device_user_id}")
                    else:
                        logger.error(f"✗ Failed to sync log: {response.status_code} - {response.text}")
                        self.error_count += 1
                        
                except Exception as e:
                    logger.error(f"✗ Error syncing log: {e}")
                    self.error_count += 1
                    continue
            
            if synced_count > 0:
                logger.info(f"✓ Synced {synced_count} new attendance logs (Total: {self.sync_count})")
            
            # Disconnect after successful sync to avoid keeping connection open
            self.device_client.disconnect()
            
            return synced_count
            
        except (BrokenPipeError, ConnectionError, OSError, IOError) as e:
            logger.error(f"✗ Connection error: {e}")
            logger.info("Disconnecting and will reconnect on next cycle...")
            self.device_client.disconnect()
            self.error_count += 1
            return 0
        except Exception as e:
            logger.error(f"✗ Sync error: {e}")
            self.device_client.disconnect()
            self.error_count += 1
            return 0
    
    def print_status(self):
        """Print current sync status."""
        logger.info("=" * 60)
        logger.info(f"Sync Status:")
        logger.info(f"  Total synced: {self.sync_count}")
        logger.info(f"  Errors: {self.error_count}")
        logger.info(f"  Last sync: {self.last_successful_sync or 'Never'}")
        logger.info(f"  Device connected: {self.device_client.is_connected()}")
        logger.info("=" * 60)
    
    def run(self):
        """Main sync loop - optimized for Android."""
        logger.info("=" * 60)
        logger.info("Android Device Sync Service")
        logger.info("=" * 60)
        logger.info(f"Device: {DEVICE_IP}:{DEVICE_PORT}")
        logger.info(f"Remote: {PYTHONANYWHERE_URL}")
        logger.info(f"Sync Interval: {SYNC_INTERVAL}s")
        logger.info("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            logger.error("Failed to authenticate. Exiting.")
            return
        
        logger.info("\nStarting sync loop... (Press Ctrl+C to stop)")
        logger.info("Tip: You can close Termux and it will keep running in background")
        logger.info("     Use 'termux-wake-lock' to prevent Android from killing the process")
        logger.info("")
        
        status_counter = 0
        
        try:
            while True:
                self.sync_attendance_logs()
                
                # Print status every 20 cycles (60 seconds if interval is 3s)
                status_counter += 1
                if status_counter >= 20:
                    self.print_status()
                    status_counter = 0
                
                time.sleep(SYNC_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n\nStopping sync service...")
            if self.device_client.is_connected():
                self.device_client.disconnect()
            self.print_status()
            logger.info("✓ Sync service stopped")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if self.device_client.is_connected():
                self.device_client.disconnect()


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
    logger.info("Starting Android Device Sync Service...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Start sync service
    sync_service = AndroidDeviceSync()
    sync_service.run()
