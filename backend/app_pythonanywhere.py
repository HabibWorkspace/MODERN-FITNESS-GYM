"""Flask application for PythonAnywhere (NO WebSockets)."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# DISABLE PYTHON BYTECODE CACHING
sys.dont_write_bytecode = True

# Load environment variables
env_path = Path(__file__).parent / '.env.production'
if not env_path.exists():
    env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import Flask and extensions
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from database import db
from config import get_config

# Initialize extensions
jwt = JWTManager()
mail = Mail()


def create_app(config=None):
    """Create Flask application for PythonAnywhere."""
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    
    # Load configuration
    if config is None:
        config = get_config()
    app.config.from_object(config)
    
    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    app.logger.setLevel(logging.INFO)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Configure CORS
    allowed_origins = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS(app, 
         resources={r"/api/*": {
             "origins": allowed_origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Cache-Control"],
             "supports_credentials": False,
             "max_age": 3600
         }})
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin_complete import admin_complete_bp
    from routes.finance import finance_bp
    from routes.packages import packages_bp
    from routes.attendance import attendance_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_complete_bp, url_prefix='/api/admin')
    app.register_blueprint(finance_bp, url_prefix='/api/finance')
    app.register_blueprint(packages_bp, url_prefix='/api/packages')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://js.pusher.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' data: https://fonts.gstatic.com; img-src 'self' data: https: blob:; connect-src 'self' ws: wss: https://*.pusher.com"
        return response
    
    # Health check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Backend running'}), 200
    
    # Serve frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        from flask import send_from_directory
        import os
        
        if path.startswith('api/'):
            return jsonify({'error': 'Not found'}), 404
        
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        frontend_dir = os.path.join(project_root, 'frontend', 'dist')
        
        if path.startswith('assets/'):
            file_path = os.path.join(frontend_dir, path)
            if os.path.exists(file_path):
                return send_from_directory(frontend_dir, path)
            return jsonify({'error': 'Asset not found'}), 404
        
        if path and os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        
        index_path = os.path.join(frontend_dir, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(frontend_dir, 'index.html')
        
        return jsonify({'error': 'Frontend not found'}), 404
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Initialize Pusher service (NO attendance service - handled by Android sync)
    try:
        from services.pusher_service import PusherService
        
        pusher_service = PusherService(
            app_id=os.getenv('PUSHER_APP_ID'),
            key=os.getenv('PUSHER_KEY'),
            secret=os.getenv('PUSHER_SECRET'),
            cluster=os.getenv('PUSHER_CLUSTER', 'mt1')
        )
        
        app.config['pusher_service'] = pusher_service
        app.logger.info("Pusher service initialized")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize Pusher: {e}")
        app.config['pusher_service'] = None
    
    return app


# Create app instance for WSGI
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
