"""BreathQuest configuration module.

Supports Development, Testing, and Production environments.
Reads settings from environment variables with safe defaults for local development.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application repository
BASE_DIR = Path(__file__).resolve().parent

# Automatically load .env file if present in BASE_DIR
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Common insecure/placeholder secrets that must be rejected in production
DISALLOWED_PRODUCTION_SECRETS = {
    "",
    "dev-secret-key-change-in-production-min-32-chars",
    "change-this-in-production-use-python-secrets-token-hex-32",
    "secret",
    "secret_key",
    "changeme",
    "password",
    "default",
}


class Config:
    """Base configuration shared across environments."""

    ENV_NAME = "base"
    DEBUG = False
    TESTING = False

    # Base directory and instance directory resolution
    BASE_DIR = BASE_DIR
    INSTANCE_DIR = BASE_DIR / "instance"

    # Secret key configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-min-32-chars")

    # Database configuration - defaults to instance-relative SQLite database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///breathquest.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookie configuration
    LEARNER_COOKIE_NAME = "bq_learner"
    SESSION_COOKIE_NAME = "bq_flask_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600 * 24  # 24 hours

    # Microsoft 365 / Entra ID SSO settings
    M365_TENANT_DOMAIN = os.getenv("M365_TENANT_DOMAIN", "nursingmu.org").lower()
    M365_CLIENT_ID = os.getenv("M365_CLIENT_ID", "")
    M365_CLIENT_SECRET = os.getenv("M365_CLIENT_SECRET", "")
    M365_TENANT_ID = os.getenv("M365_TENANT_ID", "common")
    M365_REDIRECT_URI = os.getenv("M365_REDIRECT_URI", "")

    @classmethod
    def validate(cls) -> None:
        """Validate configuration parameters."""
        if not cls.TESTING and not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in non-testing environments.")


class DevelopmentConfig(Config):
    """Configuration for local development."""

    ENV_NAME = "development"
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Configuration for automated test execution."""

    ENV_NAME = "testing"
    TESTING = True
    DEBUG = False
    # Use isolated in-memory or temp SQLite by default for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key-only-used-in-automated-tests"
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Configuration for production deployment behind reverse proxy (e.g. Apache/Waitress)."""

    ENV_NAME = "production"
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls) -> None:
        """Enforce strict production security checks."""
        super().validate()
        secret = (cls.SECRET_KEY or "").strip()
        if not secret or secret in DISALLOWED_PRODUCTION_SECRETS or len(secret) < 32:
            raise ValueError(
                "In production, SECRET_KEY must be a cryptographically secure random string "
                "with at least 32 characters, and cannot be a default or placeholder value. "
                "Generate one using: python3 -c 'import secrets; print(secrets.token_hex(32))'"
            )


CONFIG_MAP: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None) -> type[Config]:
    """Resolve configuration class from name or FLASK_ENV environment variable."""
    if env_name is None:
        env_name = os.getenv("FLASK_ENV", "development").lower()
    config_class = CONFIG_MAP.get(env_name, DevelopmentConfig)
    return config_class
