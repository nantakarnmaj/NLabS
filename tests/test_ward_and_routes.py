"""Tests for ward states, access control, Room 501 preview, and health checks."""

from __future__ import annotations

from sqlalchemy import select
from app.extensions import db
from app.models.progress import MissionProgress
from app.models.session import StudentSession


def test_ward_displays_all_four_required_room_states(seeded_client):
    """Verify ward presents the exact four rooms, titles, statuses, and notes."""
    res = seeded_client.get("/ward")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Room 501
    assert "Room 501" in html
    assert "Clear the Airway" in html
    assert "Ready" in html
    assert "View mission preview" in html
    assert "Mission preview — gameplay coming in Checkpoint B" in html
    # Must NOT say "Start mission"
    assert "Start mission" not in html

    # Room 502
    assert "Room 502" in html
    assert "Support the Breath" in html
    assert "Coming Soon" in html

    # Room 503
    assert "Room 503" in html
    assert "Open the Airway" in html
    assert "Coming Soon" in html

    # Room 504
    assert "Room 504" in html
    assert "Respiratory Rescue" in html
    assert "Locked" in html
    assert "Requires completion of" in html

    # Checkpoint A badges must be unearned/locked preview
    assert "Participation Badges" in html
    assert "Airway Explorer" in html
    assert "Oxygen Guardian" in html
    assert "Nebulizer Navigator" in html
    assert "Respiratory Ready" in html
    assert "Participate to discover" in html


def test_room_501_preview_does_not_modify_progress(seeded_client, seeded_app):
    """Accessing Room 501 preview must NOT create any MissionProgress records."""
    # Start a session first
    seeded_client.post("/session/start")

    # Visit preview
    res = seeded_client.get("/missions/clear-the-airway")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    assert "Clear the Airway" in html
    assert "Mission Preview — Gameplay Coming in Checkpoint B" in html
    assert "Simulated Patient Scenario Brief" in html
    assert "Return to Respiratory Ward" in html

    # Verify no MissionProgress records were created in the database
    with seeded_app.app_context():
        progress_count = len(db.session.execute(select(MissionProgress)).scalars().all())
        assert progress_count == 0


def test_direct_access_to_unavailable_rooms_is_restricted(seeded_client):
    """Direct GET to rooms 502, 503, 504 returns 403 Forbidden with explanatory content."""
    # Room 502
    res_502 = seeded_client.get("/missions/support-the-breath")
    assert res_502.status_code == 403
    assert "Room Coming Soon" in res_502.get_data(as_text=True)

    # Room 503
    res_503 = seeded_client.get("/missions/open-the-airway")
    assert res_503.status_code == 403
    assert "Room Coming Soon" in res_503.get_data(as_text=True)

    # Room 504
    res_504 = seeded_client.get("/missions/respiratory-rescue")
    assert res_504.status_code == 403
    assert "Room Locked" in res_504.get_data(as_text=True)

    # Non-existent room -> 404
    res_nonexistent = seeded_client.get("/missions/room-999")
    assert res_nonexistent.status_code == 404


def test_health_liveness(client):
    """Health liveness returns 200 without creating any data."""
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json == {"status": "alive"}


def test_health_readiness(seeded_client, app, tmp_path):
    """Health readiness returns 200 when DB and schema exist, and 503 when schema is absent."""
    # With seeded app
    res = seeded_client.get("/health/ready")
    assert res.status_code == 200
    assert res.json == {"status": "ready"}

    # On an empty, unmigrated database
    unmigrated_db = tmp_path / "unready.db"
    from app import create_app
    unready_app = create_app({
        "TESTING": True,
        "FLASK_ENV": "testing",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{unmigrated_db}",
    })
    unready_client = unready_app.test_client()
    res_unready = unready_client.get("/health/ready")
    assert res_unready.status_code == 503
    assert res_unready.json == {"status": "unready"}
