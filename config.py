import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email Configuration
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT')) if os.getenv('EMAIL_PORT') else 587
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Database Configuration - SQLite (portable, no service required)
# Works on Windows and Linux VPS identically
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///ezwai_smm.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask Configuration
DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())