"""Tests for seed command correctness and idempotency."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from app.extensions import db
from app.models.mission import Mission, MissionPrerequisite
from app.models.session import StudentSession
from app.models.progress import MissionProgress
from seed.rooms import seed_rooms


def test_seed_creates_exactly_four_rooms_and_three_prerequisites(app):
    """Seed must create rooms 501, 502, 503, 504 and 3 prerequisites for 504."""
    with app.app_context():
        results = seed_rooms()
        assert results["created_missions"] == 4
        assert results["created_prereqs"] == 3

        missions = db.session.execute(
            select(Mission).order_by(Mission.display_order.asc())
        ).scalars().all()
        assert len(missions) == 4

        room_numbers = [m.room_number for m in missions]
        assert room_numbers == ["501", "502", "503", "504"]

        # Verify room 501 availability is preview
        room_501 = missions[0]
        assert room_501.room_number == "501"
        assert room_501.availability == "preview"

        # Verify room 504 has 3 prerequisites
        room_504 = missions[3]
        assert room_504.room_number == "504"
        prereqs = db.session.execute(
            select(MissionPrerequisite).where(MissionPrerequisite.mission_id == room_504.id)
        ).scalars().all()
        assert len(prereqs) == 3


def test_seed_idempotency_and_preservation_of_edits_and_learner_data(app):
    """Re-running seed creates 0 duplicates, preserves customized fields, and preserves student sessions/progress."""
    with app.app_context():
        # First seed
        seed_rooms()

        # Modify an existing room attribute to simulate a customized description
        room_501 = db.session.execute(
            select(Mission).where(Mission.room_number == "501")
        ).scalar_one()
        custom_desc = "Customized clinical description for cohort 2026."
        room_501.description = custom_desc

        # Create learner session and progress
        session = StudentSession(
            token_hash="sample_hash_token_123456",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.session.add(session)
        db.session.flush()

        progress = MissionProgress(
            session_id=session.id,
            mission_id=room_501.id,
            status="in_progress",
        )
        db.session.add(progress)
        db.session.commit()

        # Re-run seed
        second_run = seed_rooms()
        assert second_run["created_missions"] == 0
        assert second_run["created_prereqs"] == 0

        # Verify no duplicate rooms
        total_missions = db.session.scalar(select(func.count(Mission.id)))
        assert total_missions == 4

        # Verify customized description was preserved
        refreshed_501 = db.session.execute(
            select(Mission).where(Mission.room_number == "501")
        ).scalar_one()
        assert refreshed_501.description == custom_desc

        # Verify learner session and progress are intact
        assert db.session.get(StudentSession, session.id) is not None
        assert db.session.get(MissionProgress, progress.id) is not None


def test_suction_mission_seed_has_no_verbal_report_phrase(app):
    """Verify suction mission seed does not contain the phrase (รายงานด้วยวาจา)."""
    from seed.suction_mission_seed import seed_suction_mission
    from app.models.activity import Activity, ActivityOption

    with app.app_context():
        seed_suction_mission()

        # Check options
        options = db.session.execute(select(ActivityOption)).scalars().all()
        for opt in options:
            assert "รายงานด้วยวาจา" not in opt.label, f"Option label contains phrase: {opt.label}"

        # Check activities
        activities = db.session.execute(select(Activity)).scalars().all()
        for act in activities:
            assert "รายงานด้วยวาจา" not in act.instruction, f"Activity instruction contains phrase: {act.instruction}"
            summary = act.content_json.get("summary", "") if act.content_json else ""
            assert "รายงานด้วยวาจา" not in summary, f"Activity summary contains phrase: {summary}"

