"""Finance routes."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.transaction import Transaction, TransactionStatus, TransactionType
from models.member_profile import MemberProfile
from models.package import Package
from models.user import User
from middleware.rbac import require_admin
from database import db
from datetime import datetime, date
from sqlalchemy import func

finance_bp = Blueprint('finance', __name__)


# ============================================================================
# FINANCE ENDPOINTS
# ============================================================================

@finance_bp.route('/transactions', methods=['GET'])
@require_admin
def list_transactions():
    """
    List all transactions.
    
    Query parameters:
        - status: Filter by status (PENDING, COMPLETED, OVERDUE)
        - member_id: Filter by member ID
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
    
    Returns:
        - 200: {"transactions": [...], "total": count, "page": page, "per_page": per_page}
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    member_id = request.args.get('member_id')
    
    # Validate pagination parameters
    if page < 1 or per_page < 1:
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    
    # Build query
    query = Transaction.query
    
    # Filter by status if provided
    if status:
        try:
            status_enum = TransactionStatus[status.upper()]
            query = query.filter_by(status=status_enum)
        except KeyError:
            return jsonify({'error': 'Invalid status'}), 400
    
    # Filter by member_id if provided
    if member_id:
        query = query.filter_by(member_id=member_id)
    
    # Order by created_at descending
    query = query.order_by(Transaction.created_at.desc())
    
    # Apply pagination
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    transactions = [transaction.to_dict() for transaction in paginated.items]
    
    return jsonify({
        'transactions': transactions,
        'total': paginated.total,
        'page': page,
        'per_page': per_page
    }), 200


@finance_bp.route('/transactions/<transaction_id>/mark-paid', methods=['POST'])
@require_admin
def mark_payment_received(transaction_id):
    """
    Mark a payment as received.
    
    Request body:
        {
            "paid_date": "ISO datetime (optional, defaults to now)"
        }
    
    Returns:
        - 200: {"id": "transaction_id", "status": "COMPLETED", "paid_date": "...", "timestamp": "..."}
        - 404: {"error": "Transaction not found"}
    """
    transaction = Transaction.query.get(transaction_id)
    
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    data = request.get_json() or {}
    
    # Parse paid_date if provided, otherwise use current time
    paid_date = datetime.utcnow()
    if 'paid_date' in data and data['paid_date']:
        try:
            paid_date = datetime.fromisoformat(data['paid_date'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({'error': 'Invalid paid_date format'}), 400
    
    try:
        transaction.status = TransactionStatus.COMPLETED
        transaction.paid_date = paid_date
        db.session.commit()
        
        return jsonify({
            'id': transaction.id,
            'status': transaction.status.name,
            'paid_date': transaction.paid_date.isoformat() if transaction.paid_date else None,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@finance_bp.route('/overdue', methods=['GET'])
@require_admin
def get_overdue_payments():
    """
    Get overdue payments (members whose package expiry date has passed without payment).
    
    Query parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
    
    Returns:
        - 200: {"overdue_payments": [...], "total": count, "page": page, "per_page": per_page}
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Validate pagination parameters
    if page < 1 or per_page < 1:
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    
    # Query overdue transactions
    query = Transaction.query.filter_by(status=TransactionStatus.OVERDUE)
    query = query.order_by(Transaction.due_date.asc())
    
    # Apply pagination
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    overdue_payments = [transaction.to_dict() for transaction in paginated.items]
    
    return jsonify({
        'overdue_payments': overdue_payments,
        'total': paginated.total,
        'page': page,
        'per_page': per_page
    }), 200


@finance_bp.route('/reports', methods=['GET'])
@require_admin
def get_financial_reports():
    """
    Get financial reports: total revenue, pending payments, overdue amounts.
    
    Returns:
        - 200: {
            "total_revenue": amount,
            "pending_payments": amount,
            "overdue_payments": amount,
            "completed_transactions_count": count,
            "pending_transactions_count": count,
            "overdue_transactions_count": count
          }
    """
    try:
        # Total revenue (completed transactions)
        total_revenue = db.session.query(
            func.sum(Transaction.amount)
        ).filter_by(status=TransactionStatus.COMPLETED).scalar() or 0
        
        # Pending payments
        pending_payments = db.session.query(
            func.sum(Transaction.amount)
        ).filter_by(status=TransactionStatus.PENDING).scalar() or 0
        
        # Overdue payments
        overdue_payments = db.session.query(
            func.sum(Transaction.amount)
        ).filter_by(status=TransactionStatus.OVERDUE).scalar() or 0
        
        # Transaction counts
        completed_count = Transaction.query.filter_by(status=TransactionStatus.COMPLETED).count()
        pending_count = Transaction.query.filter_by(status=TransactionStatus.PENDING).count()
        overdue_count = Transaction.query.filter_by(status=TransactionStatus.OVERDUE).count()
        
        return jsonify({
            'total_revenue': round(float(total_revenue), 2),
            'pending_payments': round(float(pending_payments), 2),
            'overdue_payments': round(float(overdue_payments), 2),
            'completed_transactions_count': completed_count,
            'pending_transactions_count': pending_count,
            'overdue_transactions_count': overdue_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@finance_bp.route('/settings', methods=['GET'])
@require_admin
def get_settings():
    """
    Get current settings (admission fees, package prices).
    
    Returns:
        - 200: {
            "admission_fee": amount,
            "packages": [
              {"id": "package_id", "name": "name", "duration_days": days, "price": amount},
              ...
            ]
          }
    """
    try:
        # For now, we'll return all packages as settings
        # In a real system, we'd have a Settings model
        packages = Package.query.filter_by(is_active=True).all()
        
        # Get admission fee from first member's transaction (placeholder)
        # In a real system, this would be stored in a Settings model
        admission_fee = 0
        admission_transaction = Transaction.query.filter_by(
            transaction_type=TransactionType.ADMISSION
        ).first()
        if admission_transaction:
            admission_fee = float(admission_transaction.amount)
        
        return jsonify({
            'admission_fee': admission_fee,
            'packages': [package.to_dict() for package in packages]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@finance_bp.route('/settings', methods=['PUT'])
@require_admin
def update_settings():
    """
    Update settings (admission fees and package prices).
    
    Request body:
        {
            "admission_fee": "number (optional)",
            "packages": [
              {"id": "package_id", "name": "name", "duration_days": days, "price": amount},
              ...
            ]
        }
    
    Returns:
        - 200: {"message": "Settings updated successfully", "admission_fee": amount, "packages": [...]}
        - 400: {"error": "Invalid input"}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        # Update admission fee if provided
        admission_fee = data.get('admission_fee')
        
        # Update packages if provided
        if 'packages' in data:
            for package_data in data['packages']:
                package = Package.query.get(package_data.get('id'))
                if not package:
                    return jsonify({'error': f"Package {package_data.get('id')} not found"}), 404
                
                # Validate price
                try:
                    price = float(package_data.get('price', package.price))
                    if price < 0:
                        return jsonify({'error': 'Package price must be non-negative'}), 400
                except (ValueError, TypeError):
                    return jsonify({'error': 'Package price must be a valid number'}), 400
                
                # Validate duration
                try:
                    duration = int(package_data.get('duration_days', package.duration_days))
                    if duration <= 0:
                        return jsonify({'error': 'Package duration must be positive'}), 400
                except (ValueError, TypeError):
                    return jsonify({'error': 'Package duration must be a valid integer'}), 400
                
                # Update package
                package.name = package_data.get('name', package.name)
                package.duration_days = duration
                package.price = price
        
        db.session.commit()
        
        # Return updated settings
        packages = Package.query.filter_by(is_active=True).all()
        return jsonify({
            'message': 'Settings updated successfully',
            'admission_fee': admission_fee or 0,
            'packages': [package.to_dict() for package in packages]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
