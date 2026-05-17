"""Simple Flask runner without SocketIO."""
import os
import sys

# Prevent double initialization
if __name__ == '__main__':
    # Import after checking __name__ to avoid double init
    from app import create_app
    
    app, socketio_instance = create_app()
    port = int(os.getenv('PORT', 5001))  # Changed to 5001 to avoid conflict
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting Flask server on http://0.0.0.0:{port}")
    print(f"📱 Android tablet can reach at: http://172.20.176.1:{port}")
    print(f"💻 Local browser can reach at: http://127.0.0.1:{port}")
    print(f"{'='*60}\n")
    
    # Run with standard Flask development server (no SocketIO)
    try:
        app.run(
            host='0.0.0.0',  # Listen on all network interfaces
            port=port,
            debug=False,  # Disable debug to prevent reloader
            use_reloader=False,
            threaded=True
        )
    except OSError as e:
        if "address already in use" in str(e).lower() or "10048" in str(e):
            print(f"\n❌ Port {port} is already in use!")
            print(f"💡 Try: netstat -ano | findstr :{port}")
            print(f"💡 Then: taskkill /PID <PID> /F\n")
            sys.exit(1)
        else:
            raise
