"""Tests for game service, run lifecycle, and concurrency controls."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.session import StudentSession
from app.models.run import MissionRun
from app.services.game_service import start_or_resume_run, submit_activity, start_new_replay
from seed import run_all_seeds


def test_run_start_and_reuse(app):
    """Starting a run initializes state and subsequent starts reuse the active run."""
    with app.app_context():
        run_all_seeds()
        session = StudentSession(
            token_hash="sample_hash_001",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.session.add(session)
        db.session.commit()

        # 1. Start run
        run1, is_new1 = start_or_resume_run(session, "clear-the-airway")
        assert is_new1 is True
        assert run1.status == "in_progress"
        assert run1.patient_state_json["spo2"] == 91
        assert run1.current_activity_id is not None
        assert run1.state_revision == 1

        # 2. Start again -> reuses existing
        run2, is_new2 = start_or_resume_run(session, "clear-the-airway")
        assert is_new2 is False
        assert run2.id == run1.id


def test_stale_revision_conflict_rejection(app):
    """Submissions with an outdated state revision are rejected with 409 conflict."""
    with app.app_context():
        run_all_seeds()
        session = StudentSession(
            token_hash="sample_hash_002",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.session.add(session)
        db.session.commit()

        run, _ = start_or_resume_run(session, "clear-the-airway")
        activity_id = run.current_activity_id

        # Submit with wrong expected revision (e.g. 99 instead of 1)
        res = submit_activity(
            run_id=run.id,
            activity_id=activity_id,
            payload={"acknowledged": True},
            expected_revision=99,
        )
        assert "error" in res
        assert res["error"]["code"] == "stale_state"


def test_idempotent_duplicate_submission(app):
    """Submissions with duplicate idempotency_key return cached results without reapplying effects."""
    with app.app_context():
        run_all_seeds()
        session = StudentSession(
            token_hash="sample_hash_003",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.session.add(session)
        db.session.commit()

        run, _ = start_or_resume_run(session, "clear-the-airway")
        activity_id = run.current_activity_id
        key = "unique_request_key_abc"

        # First submission
        res1 = submit_activity(
            run_id=run.id,
            activity_id=activity_id,
            payload={"acknowledged": True},
            idempotency_key=key,
        )
        assert res1["success"] is True

        # Duplicate submission with same key
        res2 = submit_activity(
            run_id=run.id,
            activity_id=activity_id,
            payload={"acknowledged": True},
            idempotency_key=key,
        )
        assert res2["is_idempotent"] is True
        assert res2["result_type"] == "success"


def test_replay_preserves_previous_run(app):
    """Replaying starts a fresh run and leaves previous records intact."""
    with app.app_context():
        run_all_seeds()
        session = StudentSession(
            token_hash="sample_hash_004",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.session.add(session)
        db.session.commit()

        run1, _ = start_or_resume_run(session, "clear-the-airway")
        replay_run = start_new_replay(session, "clear-the-airway")

        assert replay_run.id != run1.id
        assert replay_run.status == "in_progress"

        old_run = db.session.get(MissionRun, run1.id)
        assert old_run.status == "abandoned"
