"""End-to-end integration test completing Room 501: Clear the Airway."""

from __future__ import annotations

from sqlalchemy import select
from app.extensions import db
from app.models.run import MissionRun
from app.models.progress import MissionProgress
from app.models.badge import SessionBadge, Badge
from seed import run_all_seeds


def test_room_501_full_playthrough_and_badge_award(client, app):
    """Verify learner can complete all 10 activities of Room 501, earn the badge, and see completion on ward."""
    with app.app_context():
        run_all_seeds()

    # 1. Start student session
    start_res = client.post("/session/start")
    assert start_res.status_code == 302

    # 2. Access Room 501
    mission_res = client.get("/missions/clear-the-airway")
    assert mission_res.status_code == 200
    html = mission_res.get_data(as_text=True)
    assert "Activity 1 of 10" in html
    assert "Meet Mr. Somchai" in html

    with app.app_context():
        run = db.session.execute(select(MissionRun)).scalars().first()
        assert run is not None
        run_id = run.id

    # 3. Step 1: Intro (acknowledge)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res1 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"acknowledged": True}},
    )
    assert res1.status_code == 200
    assert res1.json["success"] is True

    # 4. Step 2: Clinical Cues
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res2 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": ["audible_gurgling", "rhonchi", "desaturation"]}},
    )
    assert res2.status_code == 200
    assert res2.json["success"] is True

    # 5. Step 3: Equipment Select
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res3 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": ["suction_set", "vacuum_100_120", "sterile_saline", "face_shield"]}},
    )
    assert res3.status_code == 200
    assert res3.json["success"] is True

    # 6. Step 4: Safety Check
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res4 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": ["pre_oxygenate", "semi_fowler", "monitor_vitals"]}},
    )
    assert res4.status_code == 200
    assert res4.json["success"] is True

    # 7. Step 5: Sequence
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res5 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"ordered_keys": [
            "step_preox",
            "step_don_sterile",
            "step_insert_no_suction",
            "step_suction_withdraw",
            "step_post_oxygenate"
        ]}},
    )
    assert res5.status_code == 200
    assert res5.json["success"] is True

    # 8. Step 6: Critical Decision
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res6 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "only_on_withdraw"}},
    )
    assert res6.status_code == 200
    assert res6.json["success"] is True

    # 9. Step 7: Troubleshooting (Monitor Challenge)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res7 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "abort_and_oxygenate"}},
    )
    assert res7.status_code == 200
    assert res7.json["success"] is True

    # 10. Step 8: Aftercare
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res8 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": ["re_auscultate", "flush_tubing", "restore_fio2", "document_care"]}},
    )
    assert res8.status_code == 200
    assert res8.json["success"] is True

    # 11. Step 9: Outcome
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res9 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"acknowledged": True}},
    )
    assert res9.status_code == 200
    assert res9.json["success"] is True

    # 12. Step 10: Debrief (Reflection) -> Completes Mission & Awards Badge!
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res10 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"reflection_text": "I learned to always hyper-oxygenate prior to suctioning and immediately stop when bradycardia occurs."}},
    )
    assert res10.status_code == 200
    assert res10.json["success"] is True
    assert res10.json["is_mission_completed"] is True
    assert res10.json["badge_awarded"] is not None
    assert "Airway Explorer" in res10.json["badge_awarded"]["name"]

    # 13. Verify Database Records
    with app.app_context():
        completed_run = db.session.get(MissionRun, run_id)
        assert completed_run.status == "completed"

        progress = db.session.execute(select(MissionProgress)).scalars().first()
        assert progress.status == "completed"

        session_badge = db.session.execute(select(SessionBadge)).scalars().first()
        assert session_badge is not None
        badge = db.session.get(Badge, session_badge.badge_id)
        assert badge.slug == "airway-explorer"

    # 14. Verify Ward Display reflects completion and earned badge
    ward_res = client.get("/ward")
    assert ward_res.status_code == 200
    ward_html = ward_res.get_data(as_text=True)
    assert "Completed" in ward_html
    assert "Review / Replay mission" in ward_html
    assert "Unlocked & Earned!" in ward_html
