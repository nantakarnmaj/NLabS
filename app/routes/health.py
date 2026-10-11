"""Health check endpoints for process liveness and database readiness."""

from __future__ import annotations

import logging
from flask import Blueprint, jsonify
from sqlalchemy import text
from app.extensions import db

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("/live", methods=["GET"])
def liveness() -> tuple[dict, int]:
    """Process liveness probe.

    Does not query database or create application data.
    """
    return jsonify({"status": "alive"}), 200


@health_bp.route("/ready", methods=["GET"])
def readiness() -> tuple[dict, int]:
    """Database and schema readiness probe.

    Verifies the required missions table is accessible.
    Returns 503 on database or schema error without leaking internal details.
    """
    try:
        # Check that the database is reachable and the missions table exists
        db.session.execute(text("SELECT 1 FROM missions LIMIT 1"))
        return jsonify({"status": "ready"}), 200
    except Exception as exc:
        logger.warning("Readiness probe failed: %s", type(exc).__name__)
        return jsonify({"status": "unready"}), 503
