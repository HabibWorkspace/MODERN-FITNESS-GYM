"""Attendance service for orchestrating biometric attendance tracking."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta, date
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from services.biometric_service import BiometricDeviceClient, AttendanceLog
from models.attendance_record import AttendanceRecord
from models.device_user_mapping import DeviceUserMapping
from models.sync_state import SyncState
from models.daily_attendance_summary import DailyAttendanceSummary

logger = logging.getLogger(__name__)


class SyncResult:
    """Data class representing the result of a sync operation."""
    
    def __init__(self, success: bool, records_processed: int, message: str):
        """
        Initialize sync result.
        
        Args:
            success: Whether the sync operation was successful
            records_processed: Number of attendance records processed
            message: Descriptive message about the sync operation
        """
        self.success = success
        self.records_processed = records_processed
        self.message = message
    
    def __repr__(self):
        return f"SyncResult(success={self.success}, records_processed={self.records_processed}, message={self.message})"


class PersonMapping:
    """Data class representing a person mapping result."""
    
    def __init__(self, person_type: str, person_id: str):
        """
        Initialize person mapping.
        
        Args:
            person_type: Type of person ('member' or 'trainer')
            person_id: ID of the person in the respective table
        """
        self.person_type = person_type
        self.person_id = person_id
    
    def __repr__(self):
        return f"PersonMapping(person_type={self.person_type}, person_id={self.person_id})"


class AttendanceService:
    """Service for orchestrating attendance tracking operations."""
    
    def __init__(self, device_client: BiometricDeviceClient, 
                 db_session: Session, notification_emitter=None, app=None, pusher_service=None):
        """
        Initialize attendance service with dependencies.
        
        Args:
            device_client: BiometricDeviceClient instance for device communication
            db_session: SQLAlchemy database session
            notification_emitter: Optional notification service for real-time updates
            app: Flask application instance for app context
            pusher_service: Optional Pusher service for real-time push notifications
        """
        self.device_client = device_client
        self.db_session = db_session
        self.notification_emitter = notification_emitter
        self.app = app
        self.pusher_service = pusher_service
        self.scheduler = None
        self._is_running = False
        
        logger.info("AttendanceService initialized")
    
    def start_sync_loop(self, interval_seconds: int = 45):
        """
        Start background sync loop using APScheduler.
        
        Args:
            interval_seconds: Interval between sync operations (default: 45 seconds)
        """
        if self._is_running:
            logger.warning("Sync loop is already running")
            return
        
        try:
            logger.info(f"Starting attendance sync loop with {interval_seconds}s interval")
            
            # Initialize APScheduler with BackgroundScheduler
            self.scheduler = BackgroundScheduler()
            
            # Add job to run sync_attendance_logs every interval_seconds
            # Default is 5 seconds for near-instant notifications
            self.scheduler.add_job(
                func=self._sync_with_app_context,
                trigger='interval',
                seconds=interval_seconds,
                id='attendance_sync',
                name='Attendance Log Synchronization',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            self._is_running = True
            
            logger.info("Attendance sync loop started successfully")
            
        except Exception as e:
            logger.error(
                f"Error starting sync loop: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            # Cleanup on error
            self.scheduler = None
            self._is_running = False
            raise
    
    def stop_sync_loop(self):
        """Stop the background sync loop and cleanup resources."""
        if not self._is_running:
            logger.warning("Sync loop is not running")
            return
        
        try:
            logger.info("Stopping attendance sync loop")
            
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                self.scheduler = None
            
            self._is_running = False
            logger.info("Attendance sync loop stopped")
            
        except Exception as e:
            logger.error(
                f"Error stopping sync loop: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            # Force cleanup even on error
            self.scheduler = None
            self._is_running = False
    
    def _sync_with_app_context(self):
        """Wrapper method to run sync_attendance_logs within Flask app context."""
        if self.app:
            with self.app.app_context():
                # Import db here to get the correct scoped session for this thread
                from database import db
                # Temporarily replace self.db_session with the thread-local session
                original_session = self.db_session
                self.db_session = db.session
                try:
                    return self.sync_attendance_logs()
                finally:
                    # Restore original session reference
                    self.db_session = original_session
        else:
            logger.warning("No Flask app instance available, running without app context")
            return self.sync_attendance_logs()
    
    def sync_attendance_logs(self) -> SyncResult:
        """
        Fetch and process new attendance logs from the device.
        
        This is the main orchestration method that:
        1. Connects to the device (if not connected)
        2. Fetches attendance logs
        3. Pre-filters logs using in-memory sync state cache
        4. Processes each new log entry
        5. Handles errors gracefully
        
        Returns:
            SyncResult: Result of the sync operation
        """
        logger.info("Starting attendance log synchronization")
        
        try:
            # Check device connection
            if not self.device_client.is_connected():
                logger.info("Device not connected, attempting to connect")
                
                try:
                    connected = self.device_client.connect()
                    
                    if not connected:
                        message = "Failed to connect to biometric device"
                        logger.error(
                            f"{message}. "
                            f"Error type: ConnectionError. "
                            f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
                        )
                        return SyncResult(success=False, records_processed=0, message=message)
                        
                except Exception as e:
                    message = f"Exception during device connection: {str(e)}"
                    logger.error(
                        f"{message}. "
                        f"Error type: {type(e).__name__}. "
                        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                        exc_info=True
                    )
                    return SyncResult(success=False, records_processed=0, message=message)
            
            # Fetch attendance logs from device
            try:
                logger.info("Fetching attendance logs from device")
                attendance_logs = self.device_client.get_attendance_logs()
                
                logger.info(f"Retrieved {len(attendance_logs)} attendance logs from device")
                
            except Exception as e:
                message = f"Failed to fetch attendance logs: {str(e)}"
                logger.error(
                    f"{message}. "
                    f"Error type: {type(e).__name__}. "
                    f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                    exc_info=True
                )
                return SyncResult(success=False, records_processed=0, message=message)
            
            # Pre-filter logs using sync state cache (OPTIMIZATION)
            # Fetch all sync states once instead of querying for each log
            try:
                sync_states = self.db_session.query(SyncState).all()
                # Ensure all timestamps in the map are timezone-aware
                sync_state_map = {}
                for state in sync_states:
                    ts = state.last_processed_timestamp
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    sync_state_map[state.device_user_id] = ts
                logger.debug(f"Loaded {len(sync_state_map)} sync states for filtering")
            except Exception as e:
                logger.warning(f"Failed to load sync states, will process all logs: {str(e)}")
                sync_state_map = {}
            
            # Filter logs to only new ones
            new_logs = []
            for log in attendance_logs:
                # Ensure timestamp is timezone-aware
                log_timestamp = log.timestamp
                if log_timestamp.tzinfo is None:
                    log_timestamp = log_timestamp.replace(tzinfo=timezone.utc)
                
                # Check if this log is newer than last processed
                last_processed = sync_state_map.get(log.device_user_id)
                if last_processed is None or log_timestamp > last_processed:
                    new_logs.append(log)
            
            logger.info(f"Filtered to {len(new_logs)} new logs (skipped {len(attendance_logs) - len(new_logs)} old logs)")
            
            # Process each new log entry
            records_processed = 0
            for log in new_logs:
                try:
                    result = self.process_attendance_log(log)
                    if result:
                        records_processed += 1
                except Exception as e:
                    logger.error(
                        f"Error processing attendance log {log}: {str(e)}. "
                        f"Error type: {type(e).__name__}. "
                        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                        exc_info=True
                    )
                    # Continue processing remaining logs (graceful degradation)
                    continue
            
            # Log successful sync
            message = f"Successfully processed {records_processed} new attendance records"
            logger.info(message)
            
            return SyncResult(success=True, records_processed=records_processed, message=message)
            
        except Exception as e:
            message = f"Sync operation failed: {str(e)}"
            logger.error(
                f"{message}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            return SyncResult(success=False, records_processed=0, message=message)
    
    def is_duplicate_log(self, device_user_id: str, timestamp: datetime, 
                        device_serial: str) -> bool:
        """
        Check if an attendance log entry is a duplicate.
        
        A log is considered duplicate if there's an existing record with:
        - Same device_user_id
        - Timestamp within 1 second
        - Same device_serial
        
        Args:
            device_user_id: User ID from the biometric device
            timestamp: Timestamp of the attendance scan
            device_serial: Serial number of the device
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        try:
            # Ensure timestamp is timezone-aware (UTC)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            # Define time window: 1 second before and after
            time_window_start = timestamp - timedelta(seconds=1)
            time_window_end = timestamp + timedelta(seconds=1)
            
            # Query for existing record with matching criteria
            existing_record = self.db_session.query(AttendanceRecord).filter(
                AttendanceRecord.device_user_id == device_user_id,
                AttendanceRecord.check_in_time >= time_window_start,
                AttendanceRecord.check_in_time <= time_window_end,
                AttendanceRecord.device_serial == device_serial
            ).first()
            
            if existing_record:
                logger.warning(
                    f"Duplicate attendance log detected: device_user_id={device_user_id}, "
                    f"timestamp={timestamp.isoformat()}, device_serial={device_serial}"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                f"Error checking for duplicate log: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            # On error, assume not duplicate to avoid blocking attendance tracking (graceful degradation)
            return False
    
    def process_attendance_log(self, log: AttendanceLog) -> Optional[AttendanceRecord]:
        """
        Process a single attendance log entry and create/update attendance record.
        
        This is the main orchestration method that:
        1. Extracts device_user_id, timestamp, device_serial from log
        2. Checks if log should be skipped (already processed)
        3. Checks for duplicates (skips if found)
        4. Maps device user to person (logs warning if unmapped)
        5. Determines check-in or check-out
        6. Creates new record or updates existing record
        7. Calculates stay_duration for check-outs
        8. Updates sync state and daily summary
        9. Commits to database
        10. Returns created/updated AttendanceRecord
        
        Args:
            log: AttendanceLog entry from the device
            
        Returns:
            Optional[AttendanceRecord]: Created or updated attendance record, or None if skipped
        """
        try:
            # Step 1: Extract data from log
            device_user_id = log.device_user_id
            timestamp = log.timestamp
            device_serial = log.device_serial
            
            logger.debug(f"Processing attendance log: device_user_id={device_user_id}, "
                        f"timestamp={timestamp.isoformat()}, device_serial={device_serial}")
            
            # Step 2: Check if log should be skipped (already processed)
            if self.should_skip_log(device_user_id, timestamp, device_serial):
                logger.info(f"Skipping already processed log for device_user_id={device_user_id}")
                return None
            
            # Step 3: Check for duplicates
            if self.is_duplicate_log(device_user_id, timestamp, device_serial):
                logger.info(f"Skipping duplicate attendance log for device_user_id={device_user_id}")
                # Update sync state even for duplicates to prevent re-processing
                self.update_sync_state(device_user_id, timestamp, device_serial)
                return None
            
            # Step 4: Map device user to person
            person_mapping = self.map_device_user_to_person(device_user_id)
            
            if person_mapping is None:
                logger.warning(f"Skipping attendance log for unmapped device_user_id={device_user_id}")
                return None
            
            person_type = person_mapping.person_type
            person_id = person_mapping.person_id
            
            # Fetch actual person name
            person_name = self.get_person_name(person_id, person_type)
            
            # Step 4: Determine check-in or check-out
            check_type = self.determine_check_type(person_id, person_type, timestamp)
            
            # Skip if this is a duplicate scan within 30 seconds
            if check_type == 'skip':
                logger.info(f"Skipping duplicate scan for {person_type} {person_name} within 30 seconds")
                # Update sync state to prevent re-processing
                self.update_sync_state(device_user_id, timestamp, device_serial)
                return None
            
            logger.debug(f"Determined check type: {check_type} for {person_type} {person_id}")
            
            # Step 5 & 6: Create new record or update existing record
            if check_type == 'check_in':
                # Create new attendance record
                try:
                    # Ensure timestamp is timezone-aware (UTC)
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    
                    record = AttendanceRecord(
                        device_user_id=device_user_id,
                        person_type=person_type,
                        person_id=person_id,
                        person_name=person_name,
                        check_in_time=timestamp,
                        check_out_time=None,
                        stay_duration=None,
                        device_serial=device_serial
                    )
                    
                    self.db_session.add(record)
                    self.db_session.commit()
                    
                    logger.info(f"Created check-in record for {person_type} {person_name} at {timestamp.isoformat()}")
                    
                    # Update sync state to prevent re-processing
                    self.update_sync_state(device_user_id, timestamp, device_serial)
                    
                    # Update daily summary
                    self.update_daily_summary(person_id, person_name, person_type, timestamp)
                    
                    # Emit check-in notification if notification emitter is available
                    if self.notification_emitter:
                        try:
                            self.notification_emitter.emit_check_in(
                                person_name=person_name,
                                person_type=person_type,
                                check_in_time=timestamp
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to emit check-in notification: {str(e)}. "
                                f"Error type: {type(e).__name__}. "
                                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                                exc_info=True
                            )
                            # Continue processing (graceful degradation)
                    
                    # Trigger Pusher event for real-time updates
                    if self.pusher_service and self.pusher_service.is_enabled():
                        try:
                            # Fetch additional member details for richer notifications
                            member_details = self._get_member_details(person_id, person_type)
                            
                            pusher_data = {
                                'id': record.id,
                                'person_id': person_id,
                                'person_name': person_name,
                                'person_type': person_type,
                                'check_in_time': timestamp.isoformat(),
                                'timestamp': timestamp.isoformat()
                            }
                            
                            # Add member-specific details if available
                            if member_details:
                                pusher_data.update(member_details)
                            
                            self.pusher_service.trigger_check_in(pusher_data)
                        except Exception as e:
                            logger.error(f"Failed to trigger Pusher check-in event: {str(e)}", exc_info=True)
                    
                    return record
                    
                except Exception as e:
                    logger.error(
                        f"Error creating check-in record: {str(e)}. "
                        f"Error type: {type(e).__name__}. "
                        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                        exc_info=True
                    )
                    # Rollback transaction on database error
                    self.db_session.rollback()
                    raise
                
            else:  # check_type == 'check_out'
                # Update existing open record with check-out time
                try:
                    # Ensure timestamp is timezone-aware (UTC)
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    
                    # Find the open record for this person on the same day
                    start_of_day = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_of_day = timestamp.replace(hour=23, minute=59, second=59, microsecond=999999)
                    
                    record = self.db_session.query(AttendanceRecord).filter(
                        AttendanceRecord.person_id == person_id,
                        AttendanceRecord.person_type == person_type,
                        AttendanceRecord.check_in_time >= start_of_day,
                        AttendanceRecord.check_in_time <= end_of_day,
                        AttendanceRecord.check_out_time.is_(None)
                    ).first()
                    
                    if record:
                        # Update record with check-out time and calculate stay duration
                        record.check_out_time = timestamp
                        
                        # Ensure check_in_time is timezone-aware for duration calculation
                        check_in_time = record.check_in_time
                        if check_in_time.tzinfo is None:
                            check_in_time = check_in_time.replace(tzinfo=timezone.utc)
                        
                        record.stay_duration = self.calculate_stay_duration(check_in_time, timestamp)
                        record.person_name = person_name  # Update name in case it changed
                        record.updated_at = datetime.now(timezone.utc)
                        
                        self.db_session.commit()
                        
                        logger.info(f"Updated check-out record for {person_type} {person_name} at {timestamp.isoformat()}, "
                                   f"stay_duration={record.stay_duration} minutes")
                        
                        # Update sync state to prevent re-processing
                        self.update_sync_state(device_user_id, timestamp, device_serial)
                        
                        # Update daily summary with check-out info
                        self.update_daily_summary(person_id, person_name, person_type, check_in_time, timestamp, record.stay_duration)
                        
                        # Emit check-out notification if notification emitter is available
                        if self.notification_emitter:
                            try:
                                self.notification_emitter.emit_check_out(
                                    person_name=person_name,
                                    person_type=person_type,
                                    check_in_time=record.check_in_time,
                                    stay_duration=record.stay_duration
                                )
                            except Exception as e:
                                logger.error(
                                    f"Failed to emit check-out notification: {str(e)}. "
                                    f"Error type: {type(e).__name__}. "
                                    f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                                    exc_info=True
                                )
                                # Continue processing (graceful degradation)
                        
                        # Trigger Pusher event for real-time updates
                        if self.pusher_service and self.pusher_service.is_enabled():
                            try:
                                # Fetch additional member details for richer notifications
                                member_details = self._get_member_details(person_id, person_type)
                                
                                pusher_data = {
                                    'id': record.id,
                                    'person_id': person_id,
                                    'person_name': person_name,
                                    'person_type': person_type,
                                    'check_in_time': record.check_in_time.isoformat(),
                                    'check_out_time': timestamp.isoformat(),
                                    'stay_duration': record.stay_duration,
                                    'timestamp': timestamp.isoformat()
                                }
                                
                                # Add member-specific details if available
                                if member_details:
                                    pusher_data.update(member_details)
                                
                                self.pusher_service.trigger_check_out(pusher_data)
                            except Exception as e:
                                logger.error(f"Failed to trigger Pusher check-out event: {str(e)}", exc_info=True)
                        
                        return record
                    else:
                        logger.error(
                            f"No open record found for check-out: {person_type} {person_name} at {timestamp.isoformat()}. "
                            f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
                        )
                        return None
                        
                except Exception as e:
                    logger.error(
                        f"Error updating check-out record: {str(e)}. "
                        f"Error type: {type(e).__name__}. "
                        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                        exc_info=True
                    )
                    # Rollback transaction on database error
                    self.db_session.rollback()
                    raise
            
        except Exception as e:
            logger.error(
                f"Error processing attendance log: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            # Rollback already handled in inner try-except blocks
            return None
    
    def get_person_name(self, person_id: str, person_type: str) -> str:
        """
        Fetch the actual name of a person from the database.
        
        Args:
            person_id: ID of the person
            person_type: Type of person ('member' or 'trainer')
            
        Returns:
            str: Person's full name or a fallback identifier
        """
        try:
            if person_type == 'member':
                from models.member_profile import MemberProfile
                person = self.db_session.query(MemberProfile).filter_by(id=person_id).first()
                if person and person.full_name:
                    return person.full_name
            elif person_type == 'trainer':
                from models.trainer_profile import TrainerProfile
                person = self.db_session.query(TrainerProfile).filter_by(id=person_id).first()
                if person and person.full_name:
                    return person.full_name
            
            # Fallback if name not found
            return f"{person_type.capitalize()} {person_id[:8]}"
            
        except Exception as e:
            logger.error(
                f"Error fetching person name for {person_type} {person_id}: {str(e)}. "
                f"Error type: {type(e).__name__}",
                exc_info=True
            )
            return f"{person_type.capitalize()} {person_id[:8]}"
    
    def map_device_user_to_person(self, device_user_id: str) -> Optional[PersonMapping]:
        """
        Map device user ID to a member or trainer.
        
        Args:
            device_user_id: User ID from the biometric device
            
        Returns:
            Optional[PersonMapping]: Person mapping if found, None otherwise
        """
        try:
            # Query DeviceUserMapping table by device_user_id
            mapping = self.db_session.query(DeviceUserMapping).filter_by(
                device_user_id=device_user_id
            ).first()
            
            if mapping:
                logger.debug(f"Mapped device_user_id {device_user_id} to {mapping.person_type} {mapping.person_id}")
                return PersonMapping(
                    person_type=mapping.person_type,
                    person_id=mapping.person_id
                )
            else:
                logger.warning(f"Unmapped device_user_id: {device_user_id}")
                return None
                
        except Exception as e:
            logger.error(
                f"Error mapping device_user_id {device_user_id}: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            return None
    
    def determine_check_type(self, person_id: str, person_type: str, 
                            timestamp: datetime) -> str:
        """
        Determine if a scan is a check-in or check-out.
        
        This method checks if there's an open attendance record (check_out_time is null)
        for the person on the same day. If an open record exists, this is a check-out.
        Otherwise, it's a check-in (including third scan after completed visit).
        
        Args:
            person_id: ID of the person
            person_type: Type of person ('member' or 'trainer')
            timestamp: Timestamp of the scan
            
        Returns:
            str: 'check_in' or 'check_out'
        """
        try:
            # Get the start and end of the day for the timestamp
            # Ensure timestamp is timezone-aware (UTC)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            # Calculate start of day (00:00:00) and end of day (23:59:59.999999)
            start_of_day = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = timestamp.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Query for existing attendance record on same day with null check_out_time
            open_record = self.db_session.query(AttendanceRecord).filter(
                AttendanceRecord.person_id == person_id,
                AttendanceRecord.person_type == person_type,
                AttendanceRecord.check_in_time >= start_of_day,
                AttendanceRecord.check_in_time <= end_of_day,
                AttendanceRecord.check_out_time.is_(None)
            ).first()
            
            if open_record:
                # Check if enough time has passed since check-in (minimum 30 seconds)
                # Ensure both timestamps are timezone-aware for comparison
                check_in_time = open_record.check_in_time
                if check_in_time.tzinfo is None:
                    check_in_time = check_in_time.replace(tzinfo=timezone.utc)
                
                time_since_checkin = (timestamp - check_in_time).total_seconds()
                if time_since_checkin < 30:
                    logger.warning(
                        f"Ignoring scan for {person_type} {person_id} - only {time_since_checkin:.1f} seconds since check-in. "
                        f"Minimum 30 seconds required."
                    )
                    # Return special value to indicate this should be skipped entirely
                    return 'skip'
                
                # Open record exists and enough time passed, this is a check-out
                logger.debug(f"Found open record for {person_type} {person_id}, determining as check-out")
                return 'check_out'
            else:
                # No open record, this is a check-in (including third scan after completed visit)
                logger.debug(f"No open record for {person_type} {person_id}, determining as check-in")
                return 'check_in'
                
        except Exception as e:
            logger.error(
                f"Error determining check type for {person_type} {person_id}: {str(e)}. "
                f"Error type: {type(e).__name__}. "
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
                exc_info=True
            )
            # Default to check-in on error to avoid blocking attendance tracking (graceful degradation)
            return 'check_in'
    
    def calculate_stay_duration(self, check_in: datetime, check_out: datetime) -> int:
        """
        Calculate stay duration in minutes.
        
        Args:
            check_in: Check-in timestamp
            check_out: Check-out timestamp
            
        Returns:
            int: Stay duration in minutes
        """
        # Calculate the time difference
        duration = check_out - check_in
        
        # Convert to minutes (total_seconds returns float, convert to int)
        minutes = int(duration.total_seconds() / 60)
        
        return minutes

    
    def should_skip_log(self, device_user_id: str, timestamp: datetime, device_serial: str) -> bool:
        """
        Check if a log should be skipped based on sync state.
        
        This prevents re-processing old logs that have already been processed.
        
        Args:
            device_user_id: User ID from the biometric device
            timestamp: Timestamp of the attendance scan
            device_serial: Serial number of the device
            
        Returns:
            bool: True if log should be skipped, False if it should be processed
        """
        try:
            # Ensure timestamp is timezone-aware (UTC)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            # Get the last processed timestamp for this device user
            sync_state = self.db_session.query(SyncState).filter_by(
                device_user_id=device_user_id
            ).first()
            
            if sync_state:
                # Ensure sync_state timestamp is timezone-aware
                last_processed = sync_state.last_processed_timestamp
                if last_processed.tzinfo is None:
                    last_processed = last_processed.replace(tzinfo=timezone.utc)
                
                # Skip if this log is older than the last processed timestamp
                # Use < instead of <= to allow multiple scans at the same timestamp
                if timestamp < last_processed:
                    logger.debug(
                        f"Skipping old log for device_user_id={device_user_id}, "
                        f"timestamp={timestamp.isoformat()} < last_processed={last_processed.isoformat()}"
                    )
                    return True
            
            return False
            
        except Exception as e:
            logger.error(
                f"Error checking sync state: {str(e)}. "
                f"Error type: {type(e).__name__}",
                exc_info=True
            )
            # On error, don't skip to avoid blocking attendance tracking
            return False
    
    def update_sync_state(self, device_user_id: str, timestamp: datetime, device_serial: str):
        """
        Update the sync state with the latest processed timestamp.
        
        Args:
            device_user_id: User ID from the biometric device
            timestamp: Timestamp of the attendance scan
            device_serial: Serial number of the device
        """
        try:
            # Ensure timestamp is timezone-aware (UTC)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            # Get or create sync state
            sync_state = self.db_session.query(SyncState).filter_by(
                device_user_id=device_user_id
            ).first()
            
            if sync_state:
                # Update existing sync state
                sync_state.last_processed_timestamp = timestamp
                sync_state.device_serial = device_serial
                sync_state.updated_at = datetime.now(timezone.utc)
            else:
                # Create new sync state
                sync_state = SyncState(
                    device_user_id=device_user_id,
                    last_processed_timestamp=timestamp,
                    device_serial=device_serial
                )
                self.db_session.add(sync_state)
            
            self.db_session.commit()
            logger.debug(f"Updated sync state for device_user_id={device_user_id}, timestamp={timestamp.isoformat()}")
            
        except Exception as e:
            logger.error(
                f"Error updating sync state: {str(e)}. "
                f"Error type: {type(e).__name__}",
                exc_info=True
            )
            self.db_session.rollback()
    
    def update_daily_summary(self, person_id: str, person_name: str, person_type: str, 
                            check_in_time: datetime, check_out_time: Optional[datetime] = None,
                            stay_duration: Optional[int] = None):
        """
        Update the daily attendance summary for a person.
        
        Args:
            person_id: ID of the person
            person_name: Name of the person
            person_type: Type of person ('member' or 'trainer')
            check_in_time: Check-in timestamp
            check_out_time: Optional check-out timestamp
            stay_duration: Optional stay duration in minutes
        """
        try:
            # Get the date from check_in_time
            attendance_date = check_in_time.date()
            
            # Get or create daily summary
            summary = self.db_session.query(DailyAttendanceSummary).filter_by(
                date=attendance_date,
                person_id=person_id
            ).first()
            
            if summary:
                # Update existing summary
                # Update last check-out if provided
                if check_out_time:
                    summary.last_check_out = check_out_time
                
                # Update total time if provided
                if stay_duration is not None and stay_duration > 0:
                    if summary.total_time_minutes:
                        summary.total_time_minutes += stay_duration
                    else:
                        summary.total_time_minutes = stay_duration
                
                # Increment visit count if this is a new check-in
                if not check_out_time:
                    summary.visit_count += 1
                
                summary.updated_at = datetime.now(timezone.utc)
            else:
                # Create new summary
                summary = DailyAttendanceSummary(
                    date=attendance_date,
                    person_id=person_id,
                    person_name=person_name,
                    person_type=person_type,
                    status='Present',
                    first_check_in=check_in_time,
                    last_check_out=check_out_time,
                    total_time_minutes=stay_duration if stay_duration and stay_duration > 0 else None,
                    visit_count=1
                )
                self.db_session.add(summary)
            
            self.db_session.commit()
            logger.debug(f"Updated daily summary for {person_name} on {attendance_date}")
            
        except Exception as e:
            logger.error(
                f"Error updating daily summary: {str(e)}. "
                f"Error type: {type(e).__name__}",
                exc_info=True
            )
            self.db_session.rollback()
    
    def _get_member_details(self, person_id: str, person_type: str) -> Optional[Dict[str, Any]]:
        """
        Fetch additional member details for rich notifications.
        
        Args:
            person_id: ID of the person
            person_type: Type of person ('member' or 'trainer')
            
        Returns:
            Dictionary with member details or None
        """
        try:
            if person_type != 'member':
                return None
            
            from models.member_profile import MemberProfile
            from models.package import Package
            
            member = self.db_session.query(MemberProfile).filter_by(id=person_id).first()
            if not member:
                return None
            
            details = {
                'member_number': member.member_number,
                'phone': member.phone,
                'package_start_date': member.package_start_date.isoformat() if member.package_start_date else None,
                'package_expiry_date': member.package_expiry_date.isoformat() if member.package_expiry_date else None,
                'is_frozen': member.is_frozen,
                'profile_picture': member.profile_picture
            }
            
            # Calculate days until expiry
            if member.package_expiry_date:
                now = datetime.now(timezone.utc)
                expiry = member.package_expiry_date
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                
                days_left = (expiry - now).days
                details['days_until_expiry'] = days_left
                
                # Add status based on days left
                if days_left < 0:
                    details['package_status'] = 'expired'
                elif days_left <= 3:
                    details['package_status'] = 'expiring_soon'
                elif days_left <= 7:
                    details['package_status'] = 'expiring_this_week'
                else:
                    details['package_status'] = 'active'
            
            # Get package name and duration
            if member.current_package_id:
                package = self.db_session.query(Package).filter_by(id=member.current_package_id).first()
                if package:
                    details['package_name'] = package.name
                    details['package_duration_days'] = package.duration_days
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching member details: {str(e)}", exc_info=True)
            return None
