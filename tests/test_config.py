"""Tests for environment configuration and secret safety."""

from __future__ import annotations

import pytest
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig


def test_production_rejects_empty_or_placeholder_secret():
    """Verify production strictly rejects default, placeholder, or short secrets."""
    # Test placeholder secret
    class InsecureProdConfig(ProductionConfig):
        SECRET_KEY = "dev-secret-key-change-in-production-min-32-chars"

    with pytest.raises(ValueError, match="SECRET_KEY"):
        InsecureProdConfig.validate()

    # Test short secret
    class ShortProdConfig(ProductionConfig):
        SECRET_KEY = "too-short"

    with pytest.raises(ValueError, match="SECRET_KEY"):
        ShortProdConfig.validate()


def test_production_accepts_strong_secret():
    """Verify production accepts valid cryptographically random secret."""
    class ValidProdConfig(ProductionConfig):
        SECRET_KEY = "a-very-strong-and-long-random-secret-key-for-prod-32chars"

    # Should not raise
    ValidProdConfig.validate()
    assert ValidProdConfig.DEBUG is False
    assert ValidProdConfig.SESSION_COOKIE_SECURE is True


def test_instance_path_resolution(tmp_path):
    """Verify SQLite instance path resolves appropriately."""
    config = Config()
    assert config.INSTANCE_DIR.name == "instance"
    assert "sqlite:///" in config.SQLALCHEMY_DATABASE_URI
