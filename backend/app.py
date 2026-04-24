"""Flask application factory."""
# Updated: 2026-02-16 - Added profile picture support
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# DISABLE PYTHON BYTECODE CACHING - Prevents .pyc cache issues
sys.dont_write_bytecode = True

# Load environment variables FIRST before importing config
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Now import everything else
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_mail import Mail
from database import db
from config import get_config

# Initialize extensions
jwt = JWTManager()
socketio = SocketIO()
mail = Mail()


def create_app(config=None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Disable strict slashes to handle both /path and /path/
    app.url_map.strict_slashes = False
    
    # Load configuration
    if config is None:
        config = get_config()
    app.config.from_object(config)
    
    # Enable detailed logging
    import logging
    
    # Configure logging based on environment
    if app.config.get('ENV') == 'production':
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app.logger.setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
    
    # Configure attendance logging with rotation
    from logging_config import setup_attendance_logging
    setup_attendance_logging()
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Initialize Flask-SocketIO with CORS support
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode='threading',
                     logger=True,
                     engineio_logger=True)
    
    # Debug: Log email configuration
    app.logger.info(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    app.logger.info(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    app.logger.info(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    app.logger.info(f"MAIL_PASSWORD: {'*' * len(app.config.get('MAIL_PASSWORD', '')) if app.config.get('MAIL_PASSWORD') else 'NOT SET'}")
    
    # Configure CORS - Production-ready with environment-based origins
    allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # In production, use specific origins only
    if app.config.get('ENV') == 'production':
        allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
    else:
        # Development: allow localhost
        allowed_origins = "*"
    
    CORS(app, 
         resources={r"/api/*": {
             "origins": allowed_origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Cache-Control", "X-Requested-With"],
             "supports_credentials": True if app.config.get('ENV') == 'production' else False,
             "expose_headers": ["Content-Type", "Authorization"],
             "max_age": 3600
         }})
    
    # Register blueprints - Admin Only
    from routes.auth import auth_bp
    from routes.admin_complete import admin_complete_bp
    from routes.finance import finance_bp
    from routes.packages import packages_bp
    
    try:
        from routes.attendance import attendance_bp
        app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    except ImportError as e:
        app.logger.warning(f"Could not import attendance blueprint: {e}")
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_complete_bp, url_prefix='/api/admin')
    app.register_blueprint(finance_bp, url_prefix='/api/finance')
    app.register_blueprint(packages_bp, url_prefix='/api/packages')
    
    # Add request logging (only in development)
    if app.config.get('ENV') != 'production':
        @app.before_request
        def log_request():
            app.logger.info(f"\n{'='*60}")
            app.logger.info(f"INCOMING REQUEST:")
            app.logger.info(f"Path: {request.path}")
            app.logger.info(f"Method: {request.method}")
            app.logger.info(f"Blueprint: {request.blueprint}")
            app.logger.info(f"Endpoint: {request.endpoint}")
            app.logger.info(f"Headers: {dict(request.headers)}")
            app.logger.info(f"{'='*60}\n")
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Strict transport security (HTTPS only in production)
        if app.config.get('ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:"
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permissions policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
    
    # Health check endpoint for uptime monitoring
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint to keep server alive."""
        return jsonify({
            'status': 'healthy',
            'message': 'FitCore backend is running'
        }), 200
    
    # Debug endpoint to check frontend path
    @app.route('/api/debug/frontend-path', methods=['GET'])
    def debug_frontend_path():
        """Debug endpoint to check frontend directory path."""
        import os
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
        assets_dir = os.path.join(frontend_dir, 'assets')
        return jsonify({
            'frontend_dir': frontend_dir,
            'frontend_exists': os.path.exists(frontend_dir),
            'assets_dir': assets_dir,
            'assets_exists': os.path.exists(assets_dir),
            'assets_files': os.listdir(assets_dir) if os.path.exists(assets_dir) else [],
            '__file__': __file__,
            'dirname': os.path.dirname(__file__)
        }), 200
    
    # Serve frontend static files (must be after API routes)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve frontend files for SPA routing."""
        from flask import send_from_directory
        import os
        
        # Don't serve frontend for API routes
        if path.startswith('api/'):
            return jsonify({'error': 'Not found', 'path': request.path}), 404
        
        # Get absolute path to frontend dist directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        frontend_dir = os.path.join(project_root, 'frontend', 'dist')
        
        app.logger.info(f"Serving path: {path}")
        app.logger.info(f"Frontend dir: {frontend_dir}")
        
        # Serve assets directory files directly with correct MIME types
        if path.startswith('assets/'):
            file_path = os.path.join(frontend_dir, path)
            app.logger.info(f"Asset request: {file_path}, exists: {os.path.exists(file_path)}")
            if os.path.exists(file_path):
                return send_from_directory(frontend_dir, path)
            return jsonify({'error': 'Asset not found', 'path': path, 'full_path': file_path}), 404
        
        # If requesting a file that exists, serve it
        if path and os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        
        # Otherwise serve index.html for SPA routing
        index_path = os.path.join(frontend_dir, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(frontend_dir, 'index.html')
        
        return jsonify({'error': 'Frontend not found', 'frontend_dir': frontend_dir}), 404
    
    # Add catch-all 404 handler
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'path': request.path}), 404
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Initialize attendance service
    attendance_service = None
    try:
        from services.biometric_service import BiometricDeviceClient
        from services.attendance_service import AttendanceService
        from services.notification_service import NotificationService
        from services.pusher_service import PusherService
        
        app.logger.info("Initializing attendance service...")
        
        # Create biometric device client
        device_ip = os.getenv('BIOMETRIC_DEVICE_IP', '192.168.0.201')
        device_port = int(os.getenv('BIOMETRIC_DEVICE_PORT', 4370))
        device_client = BiometricDeviceClient(ip=device_ip, port=device_port)
        
        # Create notification service
        notification_service = NotificationService(socketio=socketio)
        
        # Create Pusher service for real-time notifications
        pusher_service = PusherService(
            app_id=os.getenv('PUSHER_APP_ID'),
            key=os.getenv('PUSHER_KEY'),
            secret=os.getenv('PUSHER_SECRET'),
            cluster=os.getenv('PUSHER_CLUSTER', 'mt1')
        )
        
        # Create attendance service with dependencies
        with app.app_context():
            attendance_service = AttendanceService(
                device_client=device_client,
                db_session=db.session,
                notification_emitter=notification_service,
                app=app,
                pusher_service=pusher_service
            )
            
            # Start sync loop (3-second interval for near-instant notifications)
            attendance_service.start_sync_loop(interval_seconds=3)
            
            app.logger.info("Attendance service initialized and sync loop started")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize attendance service: {str(e)}", exc_info=True)
        attendance_service = None
    
    # Store attendance service and device client in app config for access in routes
    app.config['attendance_service'] = attendance_service
    app.config['pusher_service'] = pusher_service if 'pusher_service' in locals() else None
    if 'device_client' in locals():
        app.config['biometric_device_client'] = device_client
    
    # Register shutdown handler for graceful cleanup
    def shutdown_handler():
        """Handle graceful shutdown of attendance service."""
        try:
            if attendance_service and attendance_service._is_running:
                app.logger.info("Shutting down attendance service...")
                attendance_service.stop_sync_loop()
                if attendance_service.device_client.is_connected():
                    attendance_service.device_client.disconnect()
                app.logger.info("Attendance service shut down successfully")
        except Exception as e:
            app.logger.error(f"Error during attendance service shutdown: {str(e)}", exc_info=True)
    
    import atexit
    atexit.register(shutdown_handler)
    
    return app, socketio


if __name__ == '__main__':
    app, socketio_instance = create_app()
    port = int(os.getenv('PORT', 5000))
    socketio_instance.run(app, host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development', use_reloader=False)
else:
    # For gunicorn
    app, socketio_instance = create_app()
