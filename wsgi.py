import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/MODERN-FITNESS-GYM'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Add backend directory
backend_path = os.path.join(project_home, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(backend_path, '.env')
load_dotenv(env_path)

# Import Flask app
from backend.app import app as application
