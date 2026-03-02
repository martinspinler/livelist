"""
Flask configuration settings
"""

import os
from typing import Dict, Any
from . import load_config


# Load configuration from YAML
config_data = load_config()


class Config:
    """Base configuration"""
    # Flask
    # python -c 'import secrets; print(secrets.token_hex())'
    SECRET_KEY = os.environ.get('SECRET_KEY') or config_data.get('server', {}).get('secret_key', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1' or config_data.get('server', {}).get('debug', False)

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or config_data.get('database', {}).get('uri', 'sqlite:///livelist.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', '0') == '1' or config_data.get('database', {}).get('echo', False)

    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')

    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # WebSocket
    SOCKETIO_ASYNC_MODE = 'eventlet' if os.environ.get('USE_EVENTLET') else 'threading'

    # Application specific
    HOST = os.environ.get('HOST') or config_data.get('server', {}).get('host', '127.0.0.1')
    PORT = int(os.environ.get('PORT') or config_data.get('server', {}).get('port', 5000))

    # Sync settings
    SYNC_ENABLED = config_data.get('sync', {}).get('enabled', False)
    SYNC_SERVER_ID = config_data.get('sync', {}).get('server_id')
    SYNC_INTERVAL = config_data.get('sync', {}).get('sync_interval', 300)

    # Store configuration (from YAML)
    STORES = config_data.get('stores', {})
    PREFIXES = config_data.get('prefixes', {})
    DEFAULT_STORE = config_data.get('defaultStore', 'pt')

    # Band configuration (from YAML, will be loaded into database)
    BANDS_CONFIG = config_data.get('bands', {})


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Use environment variable for secret key in production
    # We don't raise an error here to avoid import-time errors
    # The app should check this in production mode
    SECRET_KEY = os.environ.get('SECRET_KEY', None)

    # Use PostgreSQL in production if DATABASE_URL is set
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
