"""
Flask configuration settings
"""

import os


class Config:
    """Base configuration"""

    # Database — override via LIVELIST_DATABASE_URI env var
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "LIVELIST_DATABASE_URI", "sqlite:///livelist.db"
    )

    # The app's main domains (e.g. ['livelist.org']).
    # Used to distinguish subdomains from the bare domains and to set the
    # shared cookie domain. Required for subdomain-based routing to work.
    # Set via LIVELIST_DOMAINS env var.
    # For local dev with /etc/hosts use something like 'livelist.dev'.
    DOMAINS = list(filter(None, os.environ.get("LIVELIST_DOMAINS", "").split(":")))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
