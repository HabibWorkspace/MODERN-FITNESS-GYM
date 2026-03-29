"""Biometric device communication service for ZKTeco iFace900."""
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from zk import ZK

logger = logging.getLogger(__name__)


class AttendanceLog:
    """Data class representing an attendance log entry from the device."""
    
    def __init__(self, device_user_id: str, timestamp: datetime, device_serial: str):
        """
        Initialize attendance log entry.
        
        Args:
            device_user_id: User ID from the biometric device
            timestamp: Timestamp of the attendance event
            device_serial: Serial number of the device
        """
        self.device_user_id = device_user_id
        self.timestamp = timestamp
        self.device_serial = device_serial
    
    def __repr__(self):
        return f"AttendanceLog(device_user_id={self.device_user_id}, timestamp={self.timestamp}, device_serial={self.device_serial})"


class BiometricDeviceClient:
    """Client for communicating with ZKTeco iFace900 biometric device."""
    
    def __init__(self, ip: str, port: int, timeout: int = 5):
        """
        Initialize device client with connection parameters.
        
        Args:
            ip: IP address of the biometric device
            port: Port number for device communication
            timeout: Connection timeout in seconds (default: 5)
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.zk = ZK(ip, port=port, timeout=timeout)
        self.conn = None
        self._is_connected = False
        self._last_successful_connection = None
        
        # Retry configuration - more aggressive for better reliability
        self.retry_intervals = [10, 20, 30, 60]  # seconds: 10s, 20s, 30s, max 60s
        self.current_retry_index = 0
        self.last_connection_attempt = None
        
        logger.info(f"BiometricDeviceClient initialized for {ip}:{port}")
    
    def connect(self) -> bool:
        """
        Establish connection to the biometric device.
        
        Implements exponential backoff retry logic:
        - 60s, 120s, 240s, max 300s between retries
        - Continues retry attempts indefinitely
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        # Store previous connection state to detect status changes
        was_connected = self._is_connected
        
        try:
            self.last_connection_attempt = datetime.now(timezone.utc)
            logger.info(f"Attempting to connect to biometric device at {self.ip}:{self.port}")
            
            self.conn = self.zk.connect()
            self._is_connected = True
            self._last_successful_connection = datetime.now(timezone.utc)
            
            # Reset retry index on successful connection
            self.current_retry_index = 0
            
            # Log connection status change if state changed from disconnected to connected
            if not was_connected:
                logger.info(
                    f"Device connection status changed: DISCONNECTED -> CONNECTED. "
                    f"Device: {self.ip}:{self.port}. "
                    f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
                )
            
            logger.info(f"Successfully connected to biometric device at {self.ip}:{self.port}")
            return True
            
        except Exception as e:
            self._is_connected = False
            
            # Log connection status change if state changed from connected to disconnected
            if was_connected:
                logger.warning(
                    f"Device connection status changed: CONNECTED -> DISCONNECTED. "
                    f"Device: {self.ip}:{self.port}. "
                    f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
                )
            
            # Calculate next retry interval using exponential backoff
            retry_interval = self.retry_intervals[min(self.current_retry_index, len(self.retry_intervals) - 1)]
            self.current_retry_index = min(self.current_retry_index + 1, len(self.retry_intervals) - 1)
            
            logger.error(
                f"Failed to connect to biometric device at {self.ip}:{self.port}. "
                f"Error: {str(e)}. Will retry in {retry_interval} seconds.",
                exc_info=True
            )
            
            return False
    
    def disconnect(self) -> None:
        """
        Close device connection and cleanup resources.
        
        Ensures proper cleanup of the connection and resets connection state.
        """
        # Store previous connection state to detect status changes
        was_connected = self._is_connected
        
        try:
            if self.conn is not None:
                self.conn.disconnect()
                logger.info(f"Disconnected from biometric device at {self.ip}:{self.port}")
        except Exception as e:
            logger.error(
                f"Error during disconnect: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
        finally:
            # Log connection status change if state changed from connected to disconnected
            if was_connected:
                logger.info(
                    f"Device connection status changed: CONNECTED -> DISCONNECTED. "
                    f"Device: {self.ip}:{self.port}. "
                    f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
                )
            
            self.conn = None
            self._is_connected = False
    
    def get_attendance_logs(self) -> List[AttendanceLog]:
        """
        Fetch all attendance logs from the device.
        
        Returns:
            List[AttendanceLog]: List of attendance log entries from the device
            
        Raises:
            ConnectionError: If device is not connected
        """
        if not self.is_connected():
            raise ConnectionError("Device is not connected. Call connect() first.")
        
        try:
            logger.info("Fetching attendance logs from device")
            
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
                    # Log error for individual attendance entry but continue processing
                    logger.error(
                        f"Error processing attendance entry: {str(e)}. "
                        f"Error type: {type(e).__name__}. "
                        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                        exc_info=True
                    )
                    # Continue with next entry (graceful degradation)
                    continue
            
            logger.info(f"Successfully fetched {len(attendance_logs)} attendance logs from device")
            return attendance_logs
            
        except Exception as e:
            logger.error(
                f"Error fetching attendance logs: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            # Mark connection as failed
            self._is_connected = False
            raise
    
    def is_connected(self) -> bool:
        """
        Check if device connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected and self.conn is not None
    
    def _get_device_serial(self) -> str:
        """
        Get the serial number of the connected device.
        
        Returns:
            str: Device serial number
        """
        try:
            # Get device serial number from the connection
            serial = self.conn.get_serialnumber()
            return serial if serial else "UNKNOWN"
        except Exception as e:
            logger.warning(
                f"Could not retrieve device serial number: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
            )
            return "UNKNOWN"
    
    def get_next_retry_interval(self) -> int:
        """
        Get the next retry interval in seconds based on exponential backoff.
        
        Returns:
            int: Number of seconds until next retry attempt
        """
        return self.retry_intervals[min(self.current_retry_index, len(self.retry_intervals) - 1)]
    
    def clear_attendance_logs(self) -> bool:
        """
        Clear all attendance logs from the device.
        
        WARNING: This will permanently delete all attendance records from the device.
        Make sure you have synced all important data before calling this method.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ConnectionError: If device is not connected
        """
        if not self.is_connected():
            raise ConnectionError("Device is not connected. Call connect() first.")
        
        try:
            logger.warning("Clearing all attendance logs from device - this cannot be undone!")
            
            # Clear attendance records from device
            self.conn.clear_attendance()
            
            logger.info("Successfully cleared all attendance logs from device")
            return True
            
        except Exception as e:
            logger.error(
                f"Error clearing attendance logs: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            return False
