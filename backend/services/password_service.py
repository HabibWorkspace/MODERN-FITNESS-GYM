"""Password hashing service using bcrypt."""
import bcrypt
from typing import Tuple


class PasswordService:
    """Service for password hashing and verification using bcrypt."""
    
    # Minimum 12 rounds as specified in requirements
    BCRYPT_ROUNDS = 12
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plaintext password using bcrypt.
        
        Args:
            password: Plaintext password to hash
            
        Returns:
            Bcrypt password hash string
        """
        # Generate salt and hash password with minimum 12 rounds
        salt = bcrypt.gensalt(rounds=PasswordService.BCRYPT_ROUNDS)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a plaintext password against a bcrypt hash.
        
        Args:
            password: Plaintext password to verify
            password_hash: Bcrypt hash to verify against
            
        Returns:
            True if password matches hash, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
