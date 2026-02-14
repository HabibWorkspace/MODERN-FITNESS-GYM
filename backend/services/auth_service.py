"""Authentication service for JWT token management."""
from flask_jwt_extended import create_access_token, decode_token
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import os


class AuthService:
    """Service for JWT token generation and validation."""
    
    @staticmethod
    def generate_token(user_id: str, username: str, role: str) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user_id: The user's unique identifier
            username: The user's username
            role: The user's role (admin, trainer, member)
            
        Returns:
            JWT token string valid for 24 hours
        """
        additional_claims = {
            'username': username,
            'role': role,
        }
        token = create_access_token(
            identity=user_id,
            additional_claims=additional_claims
        )
        return token
    
    @staticmethod
    def validate_token(token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a JWT token and extract claims.
        
        Args:
            token: JWT token string to validate
            
        Returns:
            Tuple of (is_valid, claims_dict)
            - is_valid: Boolean indicating if token is valid
            - claims_dict: Dictionary with token claims if valid, None otherwise
        """
        try:
            claims = decode_token(token)
            return True, claims
        except Exception as e:
            return False, None
    
    @staticmethod
    def get_token_expiration() -> datetime:
        """
        Get the expiration time for a new token.
        
        Returns:
            datetime object representing when the token will expire
        """
        # JWT_ACCESS_TOKEN_EXPIRES is set to 24 hours in config
        return datetime.utcnow() + timedelta(hours=24)
