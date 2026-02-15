"""Flask application factory."""
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
from flask_mail import Mail
from database import db
from config import get_config

# Initialize extensions
jwt = JWTManager()
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
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Debug: Log email configuration
    app.logger.info(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    app.logger.info(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    app.logger.info(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    app.logger.info(f"MAIL_PASSWORD: {'*' * len(app.config.get('MAIL_PASSWORD', '')) if app.config.get('MAIL_PASSWORD') else 'NOT SET'}")
    
    # Configure CORS - COMPREHENSIVE CONFIGURATION
    CORS(app, 
         resources={r"/api/*": {
             "origins": [
                 "http://localhost:3000", 
                 "http://localhost:3001",
                 "http://localhost:5000", 
                 "http://localhost:5173", 
                 "http://127.0.0.1:3000", 
                 "http://127.0.0.1:3001",
                 "http://127.0.0.1:5000", 
                 "http://127.0.0.1:5173",
                 "https://habibworkspace.github.io",
                 "https://habibworkspace.github.io/MODERN-FITNESS-GYM"
             ],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Cache-Control", "X-Requested-With", "Pragma", "Expires", "If-None-Match", "If-Modified-Since"],
             "supports_credentials": True,
             "expose_headers": ["Content-Type", "Authorization"],
             "max_age": 3600
         }})
    
    # Register blueprints - Admin Only
    from routes.auth import auth_bp
    from routes.admin_complete import admin_complete_bp
    from routes.finance import finance_bp
    from routes.packages import packages_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_complete_bp, url_prefix='/api/admin')
    app.register_blueprint(finance_bp, url_prefix='/api/finance')
    app.register_blueprint(packages_bp, url_prefix='/api/packages')
    
    # Add request logging
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
    
    # Health check endpoint for uptime monitoring
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint to keep server alive."""
        return jsonify({
            'status': 'healthy',
            'message': 'FitCore backend is running'
        }), 200
    
    # Add catch-all 404 handler
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'path': request.path}), 404
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development', use_reloader=False)
else:
    # For gunicorn
    app = create_app()
