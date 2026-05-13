"""Attendance API routes."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, and_, or_
from database import db
from models.attendance_record import AttendanceRecord
from models.device_user_mapping import DeviceUserMapping
from models.member_profile import MemberProfile
from models.trainer_profile import TrainerProfile
from utils.formatters import format_stay_duration

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/sync', methods=['POST'])
@jwt_required()
def manual_sync():
    try:
        attendance_service = current_app.config.get('attendance_service')
        if not attendance_service:
            return jsonify({'error': 'Attendance service not initialized'}), 503
        records_processed = attendance_service.sync_attendance_logs()
        return jsonify({'success': True, 'records_processed': records_processed}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/sync-log', methods=['POST'])
@jwt_required()
def sync_log_from_local():
    """Receive attendance log from local device sync service."""
    try:
        data = request.get_json()
        device_user_id = data.get('device_user_id')
        timestamp_str = data.get('timestamp')
        device_serial = data.get('device_serial')
        
        if not all([device_user_id, timestamp_str]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Parse timestamp and ensure it's UTC
        from datetime import timezone as tz
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # If timestamp is naive (no timezone), assume it's UTC
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=tz.utc)
        
        # Convert to UTC if it has a different timezone
        timestamp = timestamp.astimezone(tz.utc)
        
        current_app.logger.info(f"Parsed timestamp: {timestamp} (UTC)")
        
        # Check if mapping exists
        mapping = DeviceUserMapping.query.filter_by(device_user_id=device_user_id).first()
        if not mapping:
            current_app.logger.warning(f"No mapping found for device_user_id: {device_user_id}")
            return jsonify({'error': 'No mapping found for device user'}), 404
        
        # Check if record already exists
        existing = AttendanceRecord.query.filter_by(
            person_id=mapping.person_id,
            person_type=mapping.person_type,
            check_in_time=timestamp
        ).first()
        
        if existing:
            return jsonify({'message': 'Record already exists', 'id': existing.id}), 200
        
        # Get person name
        person_name = None
        if mapping.person_type == 'member':
            person = MemberProfile.query.get(mapping.person_id)
            person_name = person.full_name if person and person.full_name else None
        elif mapping.person_type == 'trainer':
            person = TrainerProfile.query.get(mapping.person_id)
            person_name = person.full_name if person and person.full_name else None
        
        # Create new attendance record with UTC timestamp
        record = AttendanceRecord(
            person_id=mapping.person_id,
            person_type=mapping.person_type,
            person_name=person_name,
            check_in_time=timestamp,  # Now guaranteed to be UTC
            device_user_id=device_user_id,
            device_serial=device_serial or "ANDROID_SYNC"
        )
        
        db.session.add(record)
        db.session.commit()
        
        current_app.logger.info(f"Synced attendance log: {person_name} at {timestamp}")
        
        # Trigger Pusher event for real-time notification
        pusher_service = current_app.config.get('pusher_service')
        current_app.logger.info(f"Pusher service retrieved: {pusher_service is not None}")
        
        if pusher_service:
            current_app.logger.info(f"Pusher enabled: {pusher_service.is_enabled()}")
            
        if pusher_service and pusher_service.is_enabled():
            try:
                # Fetch additional member details for richer notifications
                pusher_data = {
                    'id': record.id,
                    'person_id': mapping.person_id,
                    'person_name': person_name or f"{mapping.person_type.capitalize()} {mapping.person_id[:8]}",
                    'person_type': mapping.person_type,
                    'check_in_time': timestamp.isoformat(),
                    'timestamp': timestamp.isoformat()
                }
                
                # Add member-specific details if it's a member
                if mapping.person_type == 'member':
                    member = MemberProfile.query.get(mapping.person_id)
                    if member:
                        pusher_data['member_number'] = member.member_number
                        pusher_data['phone'] = member.phone
                        # Don't send profile_picture - it's too large for Pusher
                        # pusher_data['profile_picture'] = member.profile_picture
                        pusher_data['is_frozen'] = member.is_frozen
                        pusher_data['package_start_date'] = member.package_start_date.isoformat() if member.package_start_date else None
                        
                        if member.package_expiry_date:
                            from datetime import timezone as tz
                            now = datetime.now(tz.utc)
                            expiry = member.package_expiry_date
                            if expiry.tzinfo is None:
                                expiry = expiry.replace(tzinfo=tz.utc)
                            
                            days_left = (expiry - now).days
                            pusher_data['package_expiry_date'] = member.package_expiry_date.isoformat()
                            pusher_data['days_until_expiry'] = days_left
                            
                            if days_left < 0:
                                pusher_data['package_status'] = 'expired'
                            elif days_left <= 3:
                                pusher_data['package_status'] = 'expiring_soon'
                            elif days_left <= 7:
                                pusher_data['package_status'] = 'expiring_this_week'
                            else:
                                pusher_data['package_status'] = 'active'
                        
                        if member.current_package_id:
                            from models.package import Package
                            package = Package.query.get(member.current_package_id)
                            if package:
                                pusher_data['package_name'] = package.name
                                pusher_data['package_duration_days'] = package.duration_days
                
                pusher_service.trigger_check_in(pusher_data)
                current_app.logger.info(f"✓ Pusher check-in event triggered for {person_name}")
            except Exception as e:
                current_app.logger.error(f"Failed to trigger Pusher event: {e}")
        else:
            current_app.logger.warning(f"Pusher not available - service: {pusher_service is not None}, enabled: {pusher_service.is_enabled() if pusher_service else False}")
        
        return jsonify({'success': True, 'id': record.id}), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error syncing log: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_attendance():
    try:
        today = datetime.utcnow().date()
        query = AttendanceRecord.query.filter(func.date(AttendanceRecord.check_in_time) == today)
        if request.args.get('person_type'):
            query = query.filter(AttendanceRecord.person_type == request.args.get('person_type'))
        records = query.order_by(AttendanceRecord.check_in_time.desc()).all()
        return jsonify({'success': True, 'count': len(records), 'records': [r.to_dict() for r in records]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/history', methods=['GET'])
@jwt_required()
def get_attendance_history():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        query = AttendanceRecord.query
        if request.args.get('start_date'):
            query = query.filter(func.date(AttendanceRecord.check_in_time) >= datetime.fromisoformat(request.args.get('start_date')).date())
        if request.args.get('end_date'):
            query = query.filter(func.date(AttendanceRecord.check_in_time) <= datetime.fromisoformat(request.args.get('end_date')).date())
        if request.args.get('person_type'):
            query = query.filter(AttendanceRecord.person_type == request.args.get('person_type'))
        if request.args.get('person_id'):
            query = query.filter(AttendanceRecord.person_id == request.args.get('person_id'))
        paginated = query.order_by(AttendanceRecord.check_in_time.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        # Enrich records with person names if missing
        records = []
        for r in paginated.items:
            record_dict = r.to_dict()
            if not record_dict.get('person_name'):
                if r.person_type == 'member':
                    person = MemberProfile.query.get(r.person_id)
                    record_dict['person_name'] = person.full_name if person and person.full_name else f"Member {r.person_id[:8]}"
                elif r.person_type == 'trainer':
                    person = TrainerProfile.query.get(r.person_id)
                    record_dict['person_name'] = person.full_name if person and person.full_name else f"Trainer {r.person_id[:8]}"
            records.append(record_dict)
        
        return jsonify({'success': True, 'total': paginated.total, 'page': page, 'per_page': per_page, 'pages': paginated.pages, 'records': records}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/live', methods=['GET'])
@jwt_required()
def get_currently_inside():
    try:
        records = AttendanceRecord.query.filter(AttendanceRecord.check_out_time.is_(None)).all()
        members, trainers = [], []
        for r in records:
            # Handle timezone-aware datetime comparison
            check_in_time = r.check_in_time
            if check_in_time.tzinfo is None:
                check_in_time = check_in_time.replace(tzinfo=timezone.utc)
            
            now = datetime.utcnow().replace(tzinfo=timezone.utc) if datetime.utcnow().tzinfo is None else datetime.utcnow()
            time_spent = int((now - check_in_time).total_seconds() / 60)
            
            # Get person name - fetch from database if not stored in record
            person_name = r.person_name
            if not person_name:
                if r.person_type == 'member':
                    person = MemberProfile.query.get(r.person_id)
                    person_name = person.full_name if person and person.full_name else f"Member {r.person_id[:8]}"
                elif r.person_type == 'trainer':
                    person = TrainerProfile.query.get(r.person_id)
                    person_name = person.full_name if person and person.full_name else f"Trainer {r.person_id[:8]}"
                else:
                    person_name = f"{r.person_type.capitalize()} {r.person_id[:8]}"
            
            data = {
                'id': r.id, 
                'person_id': r.person_id, 
                'person_name': person_name, 
                'person_type': r.person_type, 
                'check_in_time': r.check_in_time.isoformat(), 
                'time_spent_so_far': time_spent, 
                'time_spent_formatted': format_stay_duration(time_spent)
            }
            (members if r.person_type == 'member' else trainers).append(data)
        
        # Get recent events (last 20 check-ins/check-outs from today)
        # We need to create a list of events with their actual timestamps
        today = datetime.utcnow().date()
        all_records = AttendanceRecord.query.filter(
            func.date(AttendanceRecord.check_in_time) == today
        ).all()
        
        # Create events list with actual event timestamps
        events_list = []
        for r in all_records:
            # Get person name
            person_name = r.person_name
            if not person_name:
                if r.person_type == 'member':
                    person = MemberProfile.query.get(r.person_id)
                    person_name = person.full_name if person and person.full_name else f"Member {r.person_id[:8]}"
                elif r.person_type == 'trainer':
                    person = TrainerProfile.query.get(r.person_id)
                    person_name = person.full_name if person and person.full_name else f"Trainer {r.person_id[:8]}"
                else:
                    person_name = f"{r.person_type.capitalize()} {r.person_id[:8]}"
            
            # Add check-in event
            events_list.append({
                'id': f"{r.id}-in",
                'person_id': r.person_id,
                'person_name': person_name,
                'person_type': r.person_type,
                'status': 'Check-In',
                'timestamp': r.check_in_time.isoformat(),
                'sort_time': r.check_in_time
            })
            
            # Add check-out event if exists
            if r.check_out_time:
                events_list.append({
                    'id': f"{r.id}-out",
                    'person_id': r.person_id,
                    'person_name': person_name,
                    'person_type': r.person_type,
                    'status': 'Check-Out',
                    'timestamp': r.check_out_time.isoformat(),
                    'sort_time': r.check_out_time
                })
        
        # Sort by timestamp descending and take last 20
        events_list.sort(key=lambda x: x['sort_time'], reverse=True)
        recent_events = [
            {k: v for k, v in event.items() if k != 'sort_time'}
            for event in events_list[:20]
        ]
        
        return jsonify({
            'success': True, 
            'members': members, 
            'trainers': trainers, 
            'total_inside': len(members) + len(trainers),
            'recent_events': recent_events
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_currently_inside: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'members': [], 'trainers': [], 'total_inside': 0, 'recent_events': []}), 200

@attendance_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    try:
        # Use timezone-aware datetime for accurate date comparison
        from datetime import timezone as tz
        now_utc = datetime.now(tz.utc)
        today = now_utc.date()
        
        # Log for debugging
        current_app.logger.info(f"Dashboard summary requested for date: {today} (UTC: {now_utc})")
        
        # Query using date extraction from timezone-aware timestamps
        today_checkins = db.session.query(func.count(AttendanceRecord.id)).filter(
            func.date(AttendanceRecord.check_in_time) == today
        ).scalar() or 0
        
        current_app.logger.info(f"Today's check-ins count: {today_checkins}")
        
        # Also log a sample of recent records for debugging
        recent_records = db.session.query(AttendanceRecord).order_by(AttendanceRecord.check_in_time.desc()).limit(5).all()
        for r in recent_records:
            current_app.logger.info(f"Recent record: {r.person_name} at {r.check_in_time} (date: {r.check_in_time.date() if r.check_in_time else 'None'})")
        
        members_inside = db.session.query(func.count(AttendanceRecord.id)).filter(and_(AttendanceRecord.person_type == 'member', AttendanceRecord.check_out_time.is_(None))).scalar() or 0
        trainers_inside = db.session.query(func.count(AttendanceRecord.id)).filter(and_(AttendanceRecord.person_type == 'trainer', AttendanceRecord.check_out_time.is_(None))).scalar() or 0
        completed = db.session.query(AttendanceRecord).filter(and_(func.date(AttendanceRecord.check_in_time) == today, AttendanceRecord.check_out_time.isnot(None), AttendanceRecord.stay_duration.isnot(None), AttendanceRecord.stay_duration >= 0)).all()
        avg_stay = int(sum([r.stay_duration for r in completed]) / len(completed)) if completed else 0
        
        result = {
            'success': True, 
            'today_checkins': today_checkins, 
            'members_inside': members_inside, 
            'trainers_inside': trainers_inside, 
            'avg_stay_today': avg_stay, 
            'avg_stay_formatted': format_stay_duration(avg_stay)
        }
        
        current_app.logger.info(f"Dashboard summary result: {result}")
        
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error in dashboard summary: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/analytics/weekly', methods=['GET'])
@jwt_required()
def get_weekly_analytics():
    try:
        week_offset = request.args.get('week_offset', 0, type=int)
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset)
        week_end = week_start + timedelta(days=6)
        records = db.session.query(func.date(AttendanceRecord.check_in_time).label('date'), func.count(AttendanceRecord.id).label('count')).filter(and_(func.date(AttendanceRecord.check_in_time) >= week_start, func.date(AttendanceRecord.check_in_time) <= week_end)).group_by(func.date(AttendanceRecord.check_in_time)).all()
        data_dict = {r.date: r.count for r in records}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result = [{'date': (week_start + timedelta(days=i)).isoformat(), 'day': days[i], 'count': data_dict.get(week_start + timedelta(days=i), 0)} for i in range(7)]
        return jsonify({'success': True, 'week_start': week_start.isoformat(), 'week_end': week_end.isoformat(), 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/analytics/monthly', methods=['GET'])
@jwt_required()
def get_monthly_analytics():
    try:
        month_offset = request.args.get('month_offset', 0, type=int)
        today = datetime.utcnow().date()
        month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        for _ in range(month_offset):
            month_start = (month_start - timedelta(days=1)).replace(day=1)
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1) if month_start.month == 12 else month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        records = db.session.query(func.date(AttendanceRecord.check_in_time).label('date'), func.count(AttendanceRecord.id).label('count')).filter(and_(func.date(AttendanceRecord.check_in_time) >= month_start, func.date(AttendanceRecord.check_in_time) <= month_end)).group_by(func.date(AttendanceRecord.check_in_time)).all()
        data_dict = {r.date: r.count for r in records}
        result = []
        current = month_start
        while current <= month_end:
            result.append({'date': current.isoformat(), 'count': data_dict.get(current, 0)})
            current += timedelta(days=1)
        return jsonify({'success': True, 'month': month_start.strftime('%B %Y'), 'month_start': month_start.isoformat(), 'month_end': month_end.isoformat(), 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/analytics/top-members', methods=['GET'])
@jwt_required()
def get_top_members():
    try:
        limit = request.args.get('limit', 10, type=int)
        month_offset = request.args.get('month_offset', 0, type=int)
        today = datetime.utcnow().date()
        month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        for _ in range(month_offset):
            month_start = (month_start - timedelta(days=1)).replace(day=1)
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1) if month_start.month == 12 else month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        
        top_members = db.session.query(
            AttendanceRecord.person_id, 
            AttendanceRecord.person_name, 
            func.count(AttendanceRecord.id).label('visit_count')
        ).filter(
            and_(
                AttendanceRecord.person_type == 'member', 
                func.date(AttendanceRecord.check_in_time) >= month_start, 
                func.date(AttendanceRecord.check_in_time) <= month_end
            )
        ).group_by(
            AttendanceRecord.person_id, 
            AttendanceRecord.person_name
        ).order_by(
            func.count(AttendanceRecord.id).desc()
        ).limit(limit).all()
        
        result = [{'person_id': m.person_id, 'person_name': m.person_name or 'Unknown', 'visit_count': m.visit_count} for m in top_members]
        return jsonify({'success': True, 'month': month_start.strftime('%B %Y'), 'limit': limit, 'members': result}), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_top_members: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'members': []}), 200

@attendance_bp.route('/analytics/average-stay', methods=['GET'])
@jwt_required()
def get_average_stay():
    try:
        period = request.args.get('period', 'day')
        today = datetime.utcnow().date()
        start_date = today if period == 'day' else (today - timedelta(days=today.weekday()) if period == 'week' else today.replace(day=1))
        records = db.session.query(AttendanceRecord).filter(and_(func.date(AttendanceRecord.check_in_time) >= start_date, AttendanceRecord.check_out_time.isnot(None))).all()
        if not records:
            return jsonify({'success': True, 'period': period, 'average_minutes': 0, 'average_formatted': '0h 0m'}), 200
        average = int(sum([r.stay_duration for r in records if r.stay_duration]) / len(records))
        return jsonify({'success': True, 'period': period, 'average_minutes': average, 'average_formatted': format_stay_duration(average)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/analytics/monthly-records', methods=['GET'])
@jwt_required()
def get_monthly_attendance_records():
    """Get monthly attendance records for all members/trainers with aggregated stats."""
    try:
        # Get month parameter (default to current month)
        month_offset = request.args.get('month_offset', 0, type=int)
        search_query = request.args.get('search', '').strip().lower()
        
        today = datetime.utcnow().date()
        # Calculate month start
        month_start = today.replace(day=1)
        for _ in range(month_offset):
            month_start = (month_start - timedelta(days=1)).replace(day=1)
        
        # Calculate month end
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        
        # Get all attendance records for the month
        records = db.session.query(AttendanceRecord).filter(
            and_(
                func.date(AttendanceRecord.check_in_time) >= month_start,
                func.date(AttendanceRecord.check_in_time) <= month_end
            )
        ).all()
        
        # Aggregate by person
        person_stats = {}
        for r in records:
            key = (r.person_id, r.person_type)
            if key not in person_stats:
                # Get person name
                person_name = r.person_name
                if not person_name:
                    if r.person_type == 'member':
                        person = MemberProfile.query.get(r.person_id)
                        person_name = person.full_name if person and person.full_name else f"Member {r.person_id[:8]}"
                    elif r.person_type == 'trainer':
                        person = TrainerProfile.query.get(r.person_id)
                        person_name = person.full_name if person and person.full_name else f"Trainer {r.person_id[:8]}"
                    else:
                        person_name = f"{r.person_type.capitalize()} {r.person_id[:8]}"
                
                person_stats[key] = {
                    'person_id': r.person_id,
                    'person_name': person_name,
                    'person_type': r.person_type,
                    'total_visits': 0,
                    'total_time_minutes': 0,
                    'days_attended': set()
                }
            
            person_stats[key]['total_visits'] += 1
            if r.stay_duration:
                person_stats[key]['total_time_minutes'] += r.stay_duration
            person_stats[key]['days_attended'].add(r.check_in_time.date())
        
        # Convert to list and format
        result = []
        for stats in person_stats.values():
            # Apply search filter
            if search_query and search_query not in stats['person_name'].lower():
                continue
            
            days_count = len(stats['days_attended'])
            total_hours = stats['total_time_minutes'] // 60
            total_mins = stats['total_time_minutes'] % 60
            
            result.append({
                'person_id': stats['person_id'],
                'person_name': stats['person_name'],
                'person_type': stats['person_type'],
                'total_visits': stats['total_visits'],
                'days_attended': days_count,
                'total_time_formatted': f"{total_hours}h {total_mins}m",
                'total_time_minutes': stats['total_time_minutes']
            })
        
        # Sort by total visits descending
        result.sort(key=lambda x: x['total_visits'], reverse=True)
        
        return jsonify({
            'success': True,
            'month': month_start.strftime('%B %Y'),
            'month_start': month_start.isoformat(),
            'month_end': month_end.isoformat(),
            'count': len(result),
            'records': result
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_monthly_attendance_records: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'records': []}), 200

@attendance_bp.route('/mappings', methods=['POST'])
@jwt_required()
def create_mapping():
    try:
        data = request.get_json()
        if not all([data.get('device_user_id'), data.get('person_type'), data.get('person_id')]):
            return jsonify({'error': 'Missing required fields'}), 400
        if data['person_type'] not in ['member', 'trainer']:
            return jsonify({'error': 'Invalid person_type'}), 400
        person = (MemberProfile if data['person_type'] == 'member' else TrainerProfile).query.get(data['person_id'])
        if not person:
            return jsonify({'error': f"{data['person_type'].capitalize()} not found"}), 404
        if DeviceUserMapping.query.filter_by(device_user_id=data['device_user_id']).first():
            return jsonify({'error': 'Device user already mapped'}), 409
        mapping = DeviceUserMapping(device_user_id=data['device_user_id'], person_type=data['person_type'], person_id=data['person_id'])
        db.session.add(mapping)
        db.session.commit()
        return jsonify({'success': True, 'mapping': mapping.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/mappings', methods=['GET'])
@jwt_required()
def list_mappings():
    try:
        mappings = DeviceUserMapping.query.all()
        result = []
        for m in mappings:
            data = m.to_dict()
            person = (MemberProfile if m.person_type == 'member' else TrainerProfile).query.get(m.person_id)
            if person:
                data['person_name'] = person.full_name or person.name
            result.append(data)
        return jsonify({'success': True, 'count': len(result), 'mappings': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/mappings/<mapping_id>', methods=['PUT'])
@jwt_required()
def update_mapping(mapping_id):
    try:
        mapping = DeviceUserMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        data = request.get_json()
        if 'person_type' in data:
            if data['person_type'] not in ['member', 'trainer']:
                return jsonify({'error': 'Invalid person_type'}), 400
            mapping.person_type = data['person_type']
        if 'person_id' in data:
            mapping.person_id = data['person_id']
        db.session.commit()
        return jsonify({'success': True, 'mapping': mapping.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/mappings/<mapping_id>', methods=['DELETE'])
@jwt_required()
def delete_mapping(mapping_id):
    try:
        mapping = DeviceUserMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        db.session.delete(mapping)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Mapping deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/test-pusher', methods=['POST'])
@jwt_required()
def test_pusher():
    """Test endpoint to manually trigger a Pusher event."""
    try:
        pusher_service = current_app.config.get('pusher_service')
        
        if not pusher_service:
            return jsonify({
                'success': False,
                'error': 'Pusher service not initialized'
            }), 503
        
        if not pusher_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'Pusher service not enabled (check credentials)'
            }), 503
        
        # Create test data
        test_data = {
            'id': 'test-123',
            'person_id': 'test-person',
            'person_name': 'Test User',
            'person_type': 'member',
            'check_in_time': datetime.utcnow().isoformat(),
            'timestamp': datetime.utcnow().isoformat(),
            'member_number': '999',
            'package_name': 'Test Package',
            'days_until_expiry': 30,
            'package_status': 'active'
        }
        
        # Trigger test event
        success = pusher_service.trigger_check_in(test_data)
        
        return jsonify({
            'success': success,
            'message': 'Test Pusher event triggered' if success else 'Failed to trigger Pusher event',
            'pusher_enabled': pusher_service.is_enabled(),
            'test_data': test_data
        }), 200 if success else 500
        
    except Exception as e:
        current_app.logger.error(f"Error testing Pusher: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@attendance_bp.route('/heartbeat', methods=['POST'])
def sync_heartbeat():
    """Heartbeat endpoint for Android sync script to report it's alive."""
    try:
        # Store heartbeat timestamp in app config (in-memory)
        current_app.config['android_sync_last_heartbeat'] = datetime.utcnow()
        
        # Optional: Get sync script info
        data = request.get_json() or {}
        device_ip = data.get('device_ip', 'unknown')
        
        current_app.logger.debug(f"Android sync heartbeat received from device: {device_ip}")
        
        return jsonify({
            'success': True,
            'message': 'Heartbeat received',
            'server_time': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing heartbeat: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@attendance_bp.route('/health', methods=['GET'])
@jwt_required()
def health_check():
    try:
        attendance_service = current_app.config.get('attendance_service')
        device_client = current_app.config.get('biometric_device_client')
        pusher_service = current_app.config.get('pusher_service')
        
        # Check if we have recent syncs from Android (last 5 minutes)
        recent_sync = db.session.query(AttendanceRecord).filter(
            AttendanceRecord.created_at >= datetime.utcnow() - timedelta(minutes=5)
        ).first()
        
        # Check for Android sync heartbeat (last 60 seconds)
        last_heartbeat = current_app.config.get('android_sync_last_heartbeat')
        android_sync_active = False
        if last_heartbeat:
            time_since_heartbeat = (datetime.utcnow() - last_heartbeat).total_seconds()
            android_sync_active = time_since_heartbeat < 60  # Active if heartbeat within last 60 seconds
        
        # If no heartbeat but recent sync, also consider active
        if not android_sync_active and recent_sync:
            android_sync_active = True
        
        # Safely check device connection (for local PC sync)
        is_connected = False
        if device_client:
            try:
                is_connected = device_client.is_connected()
            except Exception as e:
                current_app.logger.error(f"Error checking device connection: {e}")
                is_connected = False
        
        # Device is considered connected if either local service OR Android sync is active
        device_connected = is_connected or android_sync_active
        
        # Safely check service running status
        is_running = False
        last_sync = None
        if attendance_service:
            try:
                is_running = getattr(attendance_service, '_is_running', False)
                if hasattr(attendance_service, 'last_sync_time') and attendance_service.last_sync_time:
                    last_sync = attendance_service.last_sync_time.isoformat()
            except Exception as e:
                current_app.logger.error(f"Error checking service status: {e}")
                is_running = False
        
        # Check Pusher status
        pusher_enabled = False
        pusher_configured = False
        if pusher_service:
            pusher_enabled = pusher_service.is_enabled()
            pusher_configured = True
        
        # If Android sync is active, use the most recent record's timestamp
        if android_sync_active and recent_sync:
            last_sync = recent_sync.created_at.isoformat()
        
        return jsonify({
            'success': True, 
            'service_running': is_running or android_sync_active,  # Either local or Android
            'device_connected': device_connected, 
            'last_sync': last_sync,
            'sync_method': 'android' if android_sync_active else ('local' if is_running else 'none'),
            'pusher_configured': pusher_configured,
            'pusher_enabled': pusher_enabled
        }), 200
    except Exception as e:
        current_app.logger.error(f"Health check error: {str(e)}", exc_info=True)
        # Return a safe response even on error
        return jsonify({
            'success': False, 
            'service_running': False, 
            'device_connected': False, 
            'last_sync': None,
            'error': str(e)
        }), 200


@attendance_bp.route('/daily-summary', methods=['GET'])
@jwt_required()
def get_daily_summary():
    """Get daily attendance summary - generated on-the-fly from attendance records."""
    try:
        # Use timezone-aware datetime
        from datetime import timezone as tz
        
        # Get date parameter (default to today)
        date_str = request.args.get('date')
        if date_str:
            target_date = datetime.fromisoformat(date_str).date()
        else:
            now_utc = datetime.now(tz.utc)
            target_date = now_utc.date()
        
        current_app.logger.info(f"Daily summary requested for date: {target_date}")
        
        # Get person type filter
        person_type = request.args.get('person_type')
        
        # Fetch all attendance records for today
        query = AttendanceRecord.query.filter(func.date(AttendanceRecord.check_in_time) == target_date)
        if person_type:
            query = query.filter(AttendanceRecord.person_type == person_type)
        
        records = query.all()
        
        current_app.logger.info(f"Found {len(records)} attendance records for {target_date}")
        
        # Log sample records for debugging
        if len(records) > 0:
            for r in records[:3]:
                current_app.logger.info(f"Sample record: {r.person_name} at {r.check_in_time}")
        
        # Group by person to create summary
        person_summary = {}
        
        for record in records:
            person_key = (record.person_id, record.person_type)
            
            if person_key not in person_summary:
                # Get person name
                person_name = record.person_name
                if not person_name:
                    if record.person_type == 'member':
                        person = MemberProfile.query.get(record.person_id)
                        person_name = person.full_name if person and person.full_name else f"Member {record.person_id[:8]}"
                    elif record.person_type == 'trainer':
                        person = TrainerProfile.query.get(record.person_id)
                        person_name = person.full_name if person and person.full_name else f"Trainer {record.person_id[:8]}"
                    else:
                        person_name = f"{record.person_type.capitalize()} {record.person_id[:8]}"
                
                # Get payment status for members
                payment_status = 'N/A'
                if record.person_type == 'member':
                    member = MemberProfile.query.get(record.person_id)
                    if member:
                        # Check if package is expired
                        if member.package_expiry_date:
                            from datetime import timezone as tz
                            now = datetime.now(tz.utc)
                            expiry = member.package_expiry_date
                            if expiry.tzinfo is None:
                                expiry = expiry.replace(tzinfo=tz.utc)
                            
                            if expiry < now:
                                payment_status = 'EXPIRED'
                            else:
                                payment_status = 'PAID'
                        else:
                            payment_status = 'PENDING'
                
                person_summary[person_key] = {
                    'id': record.id,
                    'person_id': record.person_id,
                    'person_name': person_name,
                    'person_type': record.person_type,
                    'status': 'Present',
                    'first_check_in': record.check_in_time,
                    'last_check_out': record.check_out_time,
                    'total_time_minutes': record.stay_duration or 0,
                    'visit_count': 1,
                    'payment_status': payment_status
                }
            else:
                # Update existing summary
                summary = person_summary[person_key]
                summary['visit_count'] += 1
                
                # Update first check-in if earlier
                if record.check_in_time < summary['first_check_in']:
                    summary['first_check_in'] = record.check_in_time
                
                # Update last check-out if later
                if record.check_out_time:
                    if not summary['last_check_out'] or record.check_out_time > summary['last_check_out']:
                        summary['last_check_out'] = record.check_out_time
                
                # Add to total time
                if record.stay_duration:
                    summary['total_time_minutes'] += record.stay_duration
        
        # Convert to list and format timestamps
        summaries = []
        for summary in person_summary.values():
            summary['first_check_in'] = summary['first_check_in'].isoformat() if summary['first_check_in'] else None
            summary['last_check_out'] = summary['last_check_out'].isoformat() if summary['last_check_out'] else None
            summaries.append(summary)
        
        # Sort by name
        summaries.sort(key=lambda x: x['person_name'])
        
        return jsonify({
            'success': True,
            'date': target_date.isoformat(),
            'count': len(summaries),
            'summaries': summaries
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_daily_summary: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'summaries': []}), 200
