"""API endpoints for interactive gameplay submissions and replay handling."""

from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request, abort, redirect, url_for
from app.extensions import db
from app.models.run import MissionRun
from app.services.session_service import get_current_session
from app.services.game_service import submit_activity, start_new_replay

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/runs/<int:run_id>/activities/<int:activity_id>/submit", methods=["POST"])
def submit_activity_endpoint(run_id: int, activity_id: int):
    """Handle student activity submission within an active run."""
    session = get_current_session()
    if not session:
        return jsonify({"error": {"code": "unauthorized", "message": "Valid learner session required."}}), 401

    run = db.session.get(MissionRun, run_id)
    if not run or run.session_id != session.id:
        return jsonify({"error": {"code": "not_found", "message": "Mission run not found or unauthorized."}}), 404

    data = request.get_json(silent=True) or {}
    payload = data.get("payload", {})
    idempotency_key = data.get("idempotency_key")
    expected_revision = data.get("expected_revision")

    result = submit_activity(
        run_id=run.id,
        activity_id=activity_id,
        payload=payload,
        idempotency_key=idempotency_key,
        expected_revision=expected_revision,
    )

    if "error" in result:
        status_code = 409 if result["error"].get("code") == "stale_state" else 400
        return jsonify(result), status_code

    return jsonify(result), 200


@api_bp.route("/runs/<int:run_id>/replay", methods=["POST"])
def replay_endpoint(run_id: int):
    """Start a fresh replay run for a completed or active mission."""
    session = get_current_session()
    if not session:
        abort(401)

    run = db.session.get(MissionRun, run_id)
    if not run or run.session_id != session.id:
        abort(404)

    mission_slug = run.mission.slug
    replay_run = start_new_replay(session, mission_slug)
    logger.info("Started replay run %s for session %s", replay_run.id, session.id)

    return redirect(url_for("main.mission_view", slug=mission_slug))
