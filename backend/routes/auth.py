"""Authentication routes."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.user import User, UserRole
from services.auth_service import AuthService
from services.password_service import PasswordService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """
    User login endpoint.
    
    Accepts username and password, validates credentials, and returns JWT token.
    
    Request body:
        {
            "username": "string",
            "password": "string"
        }
    
    Returns:
        - 200: {"access_token": "jwt_token", "user": {...}}
        - 400: {"error": "Missing username or password"}
        - 401: {"error": "Invalid credentials"}
        - 403: {"error": "Account is frozen"}
    """
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        # Validate credentials
        if not user or not PasswordService.verify_password(password, user.password_hash):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if account is active
        if not user.is_active:
            return jsonify({'error': 'Account is frozen'}), 403
        
        # Generate JWT token
        token = AuthService.generate_token(user.id, user.username, user.role.value)
        
        # Get full_name from member or trainer profile
        user_dict = user.to_dict()
        if user.role == UserRole.MEMBER and user.member_profile:
            user_dict['full_name'] = user.member_profile.full_name
        elif user.role == UserRole.TRAINER and user.trainer_profile:
            user_dict['full_name'] = None  # Trainers don't have full_name yet
        
        return jsonify({
            'access_token': token,
            'user': user_dict
        }), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint.
    
    Invalidates the current JWT token by removing it from the client.
    Note: Token invalidation is handled client-side by removing the token.
    
    Returns:
        - 200: {"message": "Logged out successfully"}
    """
    # In a production system, you might want to maintain a token blacklist
    # For now, we rely on client-side token removal
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """
    Refresh JWT token endpoint.
    
    Generates a new JWT token for the authenticated user.
    
    Returns:
        - 200: {"access_token": "new_jwt_token"}
        - 401: {"error": "Unauthorized"}
    """
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Get user to verify they still exist and are active
    user = User.query.get(user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Generate new token
    token = AuthService.generate_token(user.id, user.username, user.role.value)
    
    return jsonify({'access_token': token}), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password using token.
    
    Request body:
        {
            "token": "reset_token",
            "new_password": "new_password"
        }
    
    Returns:
        - 200: {"message": "Password reset successfully"}
        - 400: {"error": "Missing required fields"}
        - 401: {"error": "Invalid or expired token"}
    """
    data = request.get_json()
    
    if not data or not data.get('token') or not data.get('new_password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    token = data.get('token')
    new_password = data.get('new_password')
    
    # Validate password length
    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    try:
        # Find user by reset token
        user = User.query.filter_by(reset_token=token).first()
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check if token is expired
        from datetime import datetime
        if not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Update password
        user.password_hash = PasswordService.hash_password(new_password)
        
        # Clear reset token
        user.reset_token = None
        user.reset_token_expiry = None
        
        from database import db
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        from database import db
        db.session.rollback()
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({'error': 'Failed to reset password'}), 500
