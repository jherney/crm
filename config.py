import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('CRM_SECRET_KEY', 'dev-change-me-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'CRM_DATABASE_URL',
        f'sqlite:///{BASE_DIR / "crm.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PORT = int(os.environ.get('PORT', os.environ.get('CRM_PORT', '5001')))
    DEBUG = os.environ.get('CRM_DEBUG', '1').lower() in ('1', 'true', 'yes')
    CORS_ORIGIN = os.environ.get('CRM_CORS_ORIGIN', '*')
