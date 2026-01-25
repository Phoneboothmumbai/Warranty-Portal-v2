"""
Application configuration module
Loads environment variables and defines constants
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timezone, timedelta

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# MongoDB Configuration
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# osTicket Configuration
OSTICKET_URL = os.environ.get('OSTICKET_URL', '')
OSTICKET_API_KEY = os.environ.get('OSTICKET_API_KEY', '')

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'warranty-portal-secret-key-change-in-prod')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours - reasonable session length

# Security settings
MAX_LOGIN_ATTEMPTS = 5  # Per minute
PASSWORD_MIN_LENGTH = 8

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))
