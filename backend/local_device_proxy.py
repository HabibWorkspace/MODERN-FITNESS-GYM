"""
Local Device Proxy Service
Run this on your local machine where the biometric device is accessible.
It will expose the device via a REST API that PythonAnywhere can access through ngrok.

Installation:
1. pip install flask pyngrok pyzk
2. python local_device_proxy.py

This will create a public URL (via ngrok) that you can use in PythonAnywhere.
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from services.biometric_service import BiometricDeviceClient
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize device client
DEVICE_IP = os.getenv('BIOMETRIC_DEVICE_IP', '192.168.0.201')
DEVICE_PORT = int(os.getenv('BIOMETRIC_DEVICE_PORT', 4370))
device_client = BiometricDeviceClient(ip=DEVICE_IP, port=DEVICE_PORT)


@app.route('/health', methods=['GET'])
def health_check():
    """Check if the proxy service is running."""
    return jsonify({
        'status': 'healthy',
        'device_ip': DEVICE_IP,
        'device_port': DEVICE_PORT,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/device/status', methods=['GET'])
def device_status():
    """Check device connection status."""
    try:
        is_connected = device_client.is_connected()
        
        # Try to connect if not connected
        if not is_connected:
            is_connected = device_client.connect()
        
        return jsonify({
            'connected': is_connected,
            'device_ip': DEVICE_IP,
            'device_port': DEVICE_PORT,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error checking device status: {str(e)}", exc_info=True)
        return jsonify({
            'connected': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 200


@app.route('/device/logs', methods=['GET'])
def get_attendance_logs():
    """Fetch attendance logs from the device."""
    try:
        # Ensure connection
        if not device_client.is_connected():
            connected = device_client.connect()
            if not connected:
                return jsonify({
                    'success': False,
                    'error': 'Failed to connect to device',
                    'logs': []
                }), 200
        
        # Fetch logs
        logs = device_client.get_attendance_logs()
        
        # Convert to JSON-serializable format
        logs_data = [
            {
                'device_user_id': log.device_user_id,
                'timestamp': log.timestamp.isoformat(),
                'device_serial': log.device_serial
            }
            for log in logs
        ]
        
        return jsonify({
            'success': True,
            'count': len(logs_data),
            'logs': logs_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching attendance logs: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': []
        }), 500


@app.route('/device/clear-logs', methods=['POST'])
def clear_logs():
    """Clear attendance logs from the device."""
    try:
        # Ensure connection
        if not device_client.is_connected():
            connected = device_client.connect()
            if not connected:
                return jsonify({
                    'success': False,
                    'error': 'Failed to connect to device'
                }), 200
        
        # Clear logs
        success = device_client.clear_attendance_logs()
        
        return jsonify({
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    from pyngrok import ngrok
    
    # Start ngrok tunnel
    port = 5001
    public_url = ngrok.connect(port)
    
    logger.info("="*60)
    logger.info("LOCAL DEVICE PROXY SERVICE STARTED")
    logger.info("="*60)
    logger.info(f"Device IP: {DEVICE_IP}:{DEVICE_PORT}")
    logger.info(f"Local URL: http://localhost:{port}")
    logger.info(f"Public URL (use this in PythonAnywhere): {public_url}")
    logger.info("="*60)
    logger.info("\nCopy the Public URL above and update your PythonAnywhere")
    logger.info("environment variable: DEVICE_PROXY_URL")
    logger.info("="*60)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
