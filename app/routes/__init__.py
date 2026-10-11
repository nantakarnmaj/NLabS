"""Routes package export."""

from app.routes.main import main_bp
from app.routes.health import health_bp
from app.routes.api import api_bp
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp

__all__ = ["main_bp", "health_bp", "api_bp", "auth_bp", "admin_bp"]

