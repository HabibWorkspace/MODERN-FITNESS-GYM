"""Package routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.package import Package
from models.member_profile import MemberProfile
from models.user import User, UserRole
from middleware.rbac import require_admin
from database import db
from datetime import datetime, timedelta

packages_bp = Blueprint('packages', __name__)


# ============================================================================
# ADMIN PACKAGE CRUD ENDPOINTS
# ============================================================================

@packages_bp.route('/', methods=['POST'])
@require_admin
def create_package():
    """
    Create a new package (Admin only).
    
    Request body:
        {
            "name": "string",
            "duration_days": "integer",
            "price": "number",
            "description": "string (optional)",
            "is_active": "boolean (optional, default: true)"
        }
    
    Returns:
        - 201: {"id": "package_id", ...}
        - 400: {"error": "Missing required fields"}
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'duration_days', 'price']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate duration_days is positive integer
    try:
        duration_days = int(data['duration_days'])
        if duration_days <= 0:
            return jsonify({'error': 'Duration must be positive'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Duration must be a valid integer'}), 400
    
    # Validate price is positive number
    try:
        price = float(data['price'])
        if price <= 0:
            return jsonify({'error': 'Price must be positive'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Price must be a valid number'}), 400
    
    try:
        package = Package(
            name=data['name'],
            duration_days=duration_days,
            price=price,
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(package)
        db.session.commit()
        
        return jsonify(package.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@packages_bp.route('/', methods=['GET'])
@jwt_required()
def list_packages():
    """
    List all packages (All roles).
    
    Query parameters:
        - active_only: Filter active packages only (default: false)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
    
    Returns:
        - 200: {"packages": [...], "total": count, "page": page, "per_page": per_page}
    """
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Validate pagination parameters
    if page < 1 or per_page < 1:
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    
    # Build query
    query = Package.query
    
    if active_only:
        query = query.filter_by(is_active=True)
    
    # Order by price ascending
    query = query.order_by(Package.price.asc())
    
    # Apply pagination
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    packages = [package.to_dict() for package in paginated.items]
    
    return jsonify({
        'packages': packages,
        'total': paginated.total,
        'page': page,
        'per_page': per_page
    }), 200


@packages_bp.route('/<package_id>', methods=['GET'])
@jwt_required()
def get_package(package_id):
    """
    Get package details (All roles).
    
    Returns:
        - 200: {"id": "package_id", ...}
        - 404: {"error": "Package not found"}
    """
    package = Package.query.get(package_id)
    
    if not package:
        return jsonify({'error': 'Package not found'}), 404
    
    return jsonify(package.to_dict()), 200


@packages_bp.route('/<package_id>', methods=['PUT'])
@require_admin
def update_package(package_id):
    """
    Update package information (Admin only).
    
    Request body:
        {
            "name": "string (optional)",
            "duration_days": "integer (optional)",
            "price": "number (optional)",
            "description": "string (optional)",
            "is_active": "boolean (optional)"
        }
    
    Returns:
        - 200: {"id": "package_id", ...}
        - 404: {"error": "Package not found"}
        - 400: {"error": "Invalid input"}
    """
    package = Package.query.get(package_id)
    
    if not package:
        return jsonify({'error': 'Package not found'}), 404
    
    data = request.get_json()
    
    # Update name if provided
    if 'name' in data:
        package.name = data['name']
    
    # Update duration_days if provided
    if 'duration_days' in data:
        try:
            duration_days = int(data['duration_days'])
            if duration_days <= 0:
                return jsonify({'error': 'Duration must be positive'}), 400
            package.duration_days = duration_days
        except (ValueError, TypeError):
            return jsonify({'error': 'Duration must be a valid integer'}), 400
    
    # Update price if provided
    if 'price' in data:
        try:
            price = float(data['price'])
            if price <= 0:
                return jsonify({'error': 'Price must be positive'}), 400
            package.price = price
        except (ValueError, TypeError):
            return jsonify({'error': 'Price must be a valid number'}), 400
    
    # Update description if provided
    if 'description' in data:
        package.description = data['description']
    
    # Update is_active if provided
    if 'is_active' in data:
        package.is_active = data['is_active']
    
    try:
        db.session.commit()
        return jsonify(package.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@packages_bp.route('/<package_id>', methods=['DELETE'])
@require_admin
def delete_package(package_id):
    """
    Delete a package (Admin only).
    Note: Cannot delete if members are currently using this package.
    
    Returns:
        - 200: {"message": "Package deleted successfully"}
        - 404: {"error": "Package not found"}
        - 409: {"error": "Cannot delete package with active members"}
    """
    package = Package.query.get(package_id)
    
    if not package:
        return jsonify({'error': 'Package not found'}), 404
    
    # Check if any members are using this package
    members_count = MemberProfile.query.filter_by(current_package_id=package_id).count()
    
    if members_count > 0:
        return jsonify({
            'error': f'Cannot delete package with {members_count} active member(s). Please reassign members first.'
        }), 409
    
    try:
        db.session.delete(package)
        db.session.commit()
        return jsonify({'message': 'Package deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MEMBER PACKAGE ENDPOINTS
# ============================================================================

@packages_bp.route('/purchase', methods=['POST'])
@jwt_required()
def purchase_package():
    """
    Purchase/upgrade a package (Member only).
    
    Request body:
        {
            "package_id": "string"
        }
    
    Returns:
        - 200: {"message": "Package purchased successfully", "package_expiry_date": "ISO datetime"}
        - 400: {"error": "Missing package_id"}
        - 401: {"error": "Only members can purchase packages"}
        - 404: {"error": "Package or member profile not found"}
    """
    user_id = get_jwt_identity()
    
    # Get user and verify they are a member
    user = User.query.get(user_id)
    if not user or user.role != UserRole.MEMBER:
        return jsonify({'error': 'Only members can purchase packages'}), 401
    
    data = request.get_json()
    
    if not data or 'package_id' not in data:
        return jsonify({'error': 'Missing package_id'}), 400
    
    package_id = data['package_id']
    
    # Verify package exists and is active
    package = Package.query.get(package_id)
    if not package:
        return jsonify({'error': 'Package not found'}), 404
    
    if not package.is_active:
        return jsonify({'error': 'Package is not available'}), 400
    
    # Get member profile
    member = MemberProfile.query.filter_by(user_id=user_id).first()
    if not member:
        return jsonify({'error': 'Member profile not found'}), 404
    
    try:
        # Update member package
        member.current_package_id = package_id
        member.package_start_date = datetime.utcnow()
        member.package_expiry_date = member.package_start_date + timedelta(days=package.duration_days)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Package purchased successfully',
            'package_id': package_id,
            'package_name': package.name,
            'package_start_date': member.package_start_date.isoformat(),
            'package_expiry_date': member.package_expiry_date.isoformat()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# TRAINER PACKAGE ENDPOINTS
# ============================================================================

@packages_bp.route('/members-by-package', methods=['GET'])
@jwt_required()
def get_members_by_package():
    """
    Get members grouped by their current package (Trainer/Admin).
    
    Query parameters:
        - package_id: Filter by specific package (optional)
    
    Returns:
        - 200: {"packages": [{"package": {...}, "members": [...]}]}
        - 401: {"error": "Unauthorized"}
    """
    user_id = get_jwt_identity()
    
    # Get user and verify they are trainer or admin
    user = User.query.get(user_id)
    if not user or user.role not in [UserRole.TRAINER, UserRole.ADMIN]:
        return jsonify({'error': 'Only trainers and admins can view this information'}), 401
    
    package_id = request.args.get('package_id')
    
    try:
        if package_id:
            # Get specific package with members
            package = Package.query.get(package_id)
            if not package:
                return jsonify({'error': 'Package not found'}), 404
            
            members = MemberProfile.query.filter_by(current_package_id=package_id).all()
            
            # Include username for each member
            members_data = []
            for member in members:
                member_dict = member.to_dict()
                user_obj = User.query.get(member.user_id)
                if user_obj:
                    member_dict['username'] = user_obj.username
                members_data.append(member_dict)
            
            return jsonify({
                'package': package.to_dict(),
                'members': members_data,
                'count': len(members_data)
            }), 200
        else:
            # Get all packages with their members
            packages = Package.query.order_by(Package.price.asc()).all()
            
            result = []
            for package in packages:
                members = MemberProfile.query.filter_by(current_package_id=package.id).all()
                
                # Include username for each member
                members_data = []
                for member in members:
                    member_dict = member.to_dict()
                    user_obj = User.query.get(member.user_id)
                    if user_obj:
                        member_dict['username'] = user_obj.username
                    members_data.append(member_dict)
                
                result.append({
                    'package': package.to_dict(),
                    'members': members_data,
                    'count': len(members_data)
                })
            
            # Also include members with no package
            no_package_members = MemberProfile.query.filter_by(current_package_id=None).all()
            no_package_data = []
            for member in no_package_members:
                member_dict = member.to_dict()
                user_obj = User.query.get(member.user_id)
                if user_obj:
                    member_dict['username'] = user_obj.username
                no_package_data.append(member_dict)
            
            if no_package_data:
                result.append({
                    'package': {'id': None, 'name': 'No Package', 'duration_days': 0, 'price': 0},
                    'members': no_package_data,
                    'count': len(no_package_data)
                })
            
            return jsonify({'packages': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
