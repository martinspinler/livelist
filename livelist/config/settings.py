"""
Flask configuration settings
"""


class Config:
    """Base configuration"""

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///livelist.db'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
