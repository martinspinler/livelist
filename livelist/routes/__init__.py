"""
Blueprint registration for routes
"""

from flask import Blueprint

# Create blueprints
api_bp = Blueprint('api', __name__)
views_bp = Blueprint('views', __name__)
auth_bp = Blueprint('auth', __name__)

# Import routes to register them with blueprints
from . import api, views, auth
