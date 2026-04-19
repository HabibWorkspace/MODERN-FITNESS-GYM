"""Pusher service for real-time notifications."""
import os
import logging
from typing import Dict, Any, Optional
import pusher

logger = logging.getLogger(__name__)


class PusherService:
    """Service for sending real-time notifications via Pusher."""
    
    def __init__(self, app_id: str = None, key: str = None, secret: str = None, cluster: str = None):
        """Initialize Pusher client."""
        self.app_id = app_id or os.getenv('PUSHER_APP_ID')
        self.key = key or os.getenv('PUSHER_KEY')
        self.secret = secret or os.getenv('PUSHER_SECRET')
        self.cluster = cluster or os.getenv('PUSHER_CLUSTER', 'mt1')
        
        self.enabled = all([self.app_id, self.key, self.secret])
        
        if self.enabled:
            try:
                self.client = pusher.Pusher(
                    app_id=self.app_id,
                    key=self.key,
                    secret=self.secret,
                    cluster=self.cluster,
                    ssl=True
                )
                logger.info(f"Pusher service initialized (cluster: {self.cluster})")
            except Exception as e:
                logger.error(f"Failed to initialize Pusher: {e}")
                self.enabled = False
                self.client = None
        else:
            logger.warning("Pusher credentials not configured - real-time notifications disabled")
            self.client = None
    
    def trigger_event(self, channel: str, event: str, data: Dict[str, Any]) -> bool:
        """
        Trigger a Pusher event.
        
        Args:
            channel: Channel name (e.g., 'attendance-updates')
            event: Event name (e.g., 'check-in', 'check-out')
            data: Event data payload
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            logger.debug(f"Pusher disabled - skipping event: {channel}/{event}")
            return False
        
        try:
            self.client.trigger(channel, event, data)
            logger.info(f"Pusher event triggered: {channel}/{event}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger Pusher event {channel}/{event}: {e}")
            return False
    
    def trigger_check_in(self, person_data: Dict[str, Any]) -> bool:
        """
        Trigger a check-in event.
        
        Args:
            person_data: Dictionary with person info (id, name, type, timestamp, etc.)
        """
        return self.trigger_event('attendance-updates', 'check-in', person_data)
    
    def trigger_check_out(self, person_data: Dict[str, Any]) -> bool:
        """
        Trigger a check-out event.
        
        Args:
            person_data: Dictionary with person info (id, name, type, timestamp, stay_duration, etc.)
        """
        return self.trigger_event('attendance-updates', 'check-out', person_data)
    
    def trigger_dashboard_update(self, summary_data: Dict[str, Any]) -> bool:
        """
        Trigger a dashboard summary update event.
        
        Args:
            summary_data: Dictionary with dashboard stats (total_inside, members_inside, etc.)
        """
        return self.trigger_event('attendance-updates', 'dashboard-update', summary_data)
    
    def is_enabled(self) -> bool:
        """Check if Pusher is enabled and configured."""
        return self.enabled
