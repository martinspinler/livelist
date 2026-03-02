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
    # Base filesystem prefix for sheet stores, override via env var. The
    # per-band {patterns, instruments} layout now lives in each Band row's
    # sheet_store column (set via `flask set-sheet-store`). See
    # examples/sheet-store-band.json for a reference layout.
    SHEET_STORE_PATH = os.environ.get("LIVELIST_SHEET_STORE_PATH")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
