"""BreathQuest Flask application factory."""

from __future__ import annotations

import os
from typing import Any
from flask import Flask, render_template, request, url_for
from flask_wtf.csrf import CSRFError
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config, get_config
from app.extensions import db, migrate, csrf
from app.routes import main_bp, health_bp, api_bp, auth_bp, admin_bp
from app.commands import register_commands
import app.models  # noqa: F401


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """Enforce SQLite foreign key constraints on every database connection."""
    # Check if connection is sqlite3
    if hasattr(dbapi_connection, "cursor"):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
        finally:
            cursor.close()


def create_app(config_override: dict[str, Any] | type[Config] | None = None) -> Flask:
    """Create and configure the BreathQuest Flask application.

    Args:
        config_override: Optional configuration dictionary or Config class.
    """
    # Resolve configuration class
    if isinstance(config_override, type) and issubclass(config_override, Config):
        config_class = config_override
        override_dict = None
    elif isinstance(config_override, dict):
        config_class = get_config(config_override.get("FLASK_ENV"))
        override_dict = config_override
    else:
        config_class = get_config()
        override_dict = None

    # Enforce configuration validation
    config_class.validate()

    # Ensure instance directory exists safely without clearing contents
    instance_dir = str(config_class.INSTANCE_DIR)
    os.makedirs(instance_dir, exist_ok=True)

    app = Flask(
        __name__,
        instance_relative_config=True,
        instance_path=instance_dir,
    )

    # Load base configuration from class
    app.config.from_object(config_class)

    # Apply specific overrides if passed as a dictionary
    if override_dict:
        app.config.update(override_dict)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register CLI commands
    register_commands(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    from app.routes.equipment import equipment_bp
    app.register_blueprint(equipment_bp)

    # Auto-sync mission content if outdated seed text is detected in database
    if not app.config.get("TESTING"):
        with app.app_context():
            try:
                from sqlalchemy import select
                from app.models.activity import ActivityOption
                has_old_phrase = db.session.execute(
                    select(ActivityOption.id).where(ActivityOption.label.like("%รายงานด้วยวาจา%"))
                ).first()
                if has_old_phrase:
                    from seed.suction_mission_seed import seed_suction_mission
                    seed_suction_mission()
            except Exception as e:
                app.logger.warning("Auto-sync suction seed skipped: %s", e)

    # Context processors
    @app.context_processor
    def inject_auth_context():
        from app.routes.auth import get_current_user
        return {"current_user": get_current_user()}

    # Error handlers
    def _is_api_request() -> bool:
        return request.path.startswith("/api/") or request.is_json

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error: CSRFError):
        app.logger.warning("CSRF validation failure on %s: %s", request.path, error.description)
        if _is_api_request():
            from flask import jsonify
            return jsonify({
                "error": {
                    "code": "csrf_error",
                    "message": "Session or CSRF token verification failed. Please reload the page.",
                }
            }), 400
        return render_template(
            "errors/400.html",
            title="Session Verification Required",
            message="Your request could not be validated. Please reload the page and try again.",
            back_url=url_for("main.home"),
        ), 400

    @app.errorhandler(400)
    def handle_bad_request(error):
        if _is_api_request():
            from flask import jsonify
            return jsonify({
                "error": {
                    "code": "bad_request",
                    "message": getattr(error, "description", "The request was invalid."),
                }
            }), 400
        return render_template(
            "errors/400.html",
            title="Bad Request",
            message="The request was invalid or could not be processed.",
            back_url=url_for("main.home"),
        ), 400

    @app.errorhandler(403)
    def handle_forbidden(error):
        if _is_api_request():
            from flask import jsonify
            return jsonify({
                "error": {
                    "code": "forbidden",
                    "message": getattr(error, "description", "You do not have access to this resource."),
                }
            }), 403
        return render_template(
            "errors/403.html",
            title="Access Restricted",
            message=getattr(error, "description", "You do not have access to this resource."),
            back_url=url_for("main.ward"),
        ), 403

    @app.errorhandler(404)
    def handle_not_found(error):
        if _is_api_request():
            from flask import jsonify
            return jsonify({
                "error": {
                    "code": "not_found",
                    "message": getattr(error, "description", "The requested resource was not found."),
                }
            }), 404
        return render_template(
            "errors/404.html",
            title="Page Not Found",
            message="The requested room or page does not exist in the simulated ward.",
            back_url=url_for("main.ward"),
        ), 404

    @app.errorhandler(500)
    def handle_server_error(error):
        app.logger.error("Internal server error: %s", error)
        if _is_api_request():
            from flask import jsonify
            return jsonify({
                "error": {
                    "code": "server_error",
                    "message": "A temporary internal system error occurred. Please try again.",
                }
            }), 500
        return render_template(
            "errors/500.html",
            title="Ward System Error",
            message="A temporary system error occurred. Please return to the ward.",
            back_url=url_for("main.ward"),
        ), 500

    # Security headers
    @app.after_request
    def apply_security_headers(response):
        # Strict local-only CSP allowing self assets and data URI images
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self';",
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    return app
