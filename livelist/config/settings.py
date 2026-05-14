"""
Flask configuration settings
"""


class Config:
    """Base configuration"""

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///livelist.db'

    # Cookie domain for shared subdomain authentication.
    # Set this to share the auth cookie across subdomains, e.g. '.livelist.org'.
    # On production this is auto-detected from the request host.
    # For local development with subdomains, set this to your dev domain
    # (e.g. '.livelist.dev' if you added '127.0.0.1 myband.livelist.dev' to /etc/hosts).
    # Leave as None for auto-detection (falls back to host-only cookies on localhost).
    COOKIE_DOMAIN = None


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
