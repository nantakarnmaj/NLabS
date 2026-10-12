"""End-to-end integration test completing Room 502: Support the Breath (Oxygen Therapy Mission)."""

from __future__ import annotations

from sqlalchemy import select
from app.extensions import db
from app.models.run import MissionRun
from app.models.progress import MissionProgress
from app.models.badge import SessionBadge, Badge
from seed import run_all_seeds


def test_room_502_full_playthrough_and_badge_award(client, app):
    """Verify learner completes all 10 activities of Room 502, earns 'Oxygen Guardian', and sees completion on ward."""
    with app.app_context():
        run_all_seeds()

    # 1. Start student session
    start_res = client.post("/session/start")
    assert start_res.status_code == 302

    # 2. Access Room 502
    mission_res = client.get("/missions/support-the-breath")
    assert mission_res.status_code == 200
    html = mission_res.get_data(as_text=True)
    assert "Activity 1 of 10" in html
    assert "Meet Ms. Anong" in html
    assert "Oxygen Therapy" in html

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
        json={"payload": {"selected_keys": ["spo2_88", "tachypnea_rr28", "tachycardia_hr104", "dyspnea_anxiety"]}},
    )
    assert res2.status_code == 200
    assert res2.json["success"] is True

    # 5. Step 3: Equipment Select (Initial Oxygen Device)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res3 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": ["nasal_cannula_3l"]}},
    )
    assert res3.status_code == 200
    assert res3.json["success"] is True

    # 6. Step 4: Sequence (Administration Flow)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res4 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"ordered_keys": [
            "step_verify_source",
            "step_set_flow",
            "step_verify_gas_flow",
            "step_insert_prongs",
            "step_loop_ears_snug",
        ]}},
    )
    assert res4.status_code == 200
    assert res4.json["success"] is True

    # 7. Step 5: Safety Check (Fire Precautions)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res5 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": ["no_smoking_signs", "sterile_water_level", "grounded_electrical", "avoid_petroleum"]}},
    )
    assert res5.status_code == 200
    assert res5.json["success"] is True

    # 8. Step 6: Troubleshooting (Watch the Monitor Trend)
    # Verify patient improved on monitor after receiving oxygen in Step 4
    play_res_step6 = client.get("/missions/support-the-breath")
    assert play_res_step6.status_code == 200
    html_s6 = play_res_step6.get_data(as_text=True)
    assert "95%" in html_s6
    assert "82 bpm" in html_s6
    assert "18 /min" in html_s6
    assert "คงที่ / สงบ" in html_s6
    assert "เสียงกรอบแกรบ" in html_s6
    assert "Stridor" not in html_s6

    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res6 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "maintain_and_reassess"}},
    )
    assert res6.status_code == 200
    assert res6.json["success"] is True

    # 9. Step 7: Matching (Oxygen Device Match Challenge)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    # Test wrong matching retry first
    res7_wrong = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"pairs": {
            "case_mild_postop": "nasal_cannula",
            "case_copd_precise": "nrb_mask",  # wrong
            "case_severe_hypoxemia": "nrb_mask",
            "case_tracheostomy": "tracheostomy_collar",
        }}},
    )
    assert res7_wrong.status_code == 200
    assert res7_wrong.json["success"] is False
    assert res7_wrong.json["result_type"] == "retry"

    # Now correct matching
    res7_correct = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"pairs": {
            "case_mild_postop": "nasal_cannula",
            "case_copd_precise": "nasal_cannula_copd",
            "case_severe_hypoxemia": "nrb_mask",
            "case_tracheostomy": "tracheostomy_collar",
        }}},
    )
    assert res7_correct.status_code == 200
    assert res7_correct.json["success"] is True

    # 10. Step 8: Decision (Sudden Desaturation)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res8 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "check_patient_and_tubing"}},
    )
    assert res8.status_code == 200
    assert res8.json["success"] is True

    # 11. Step 9: Aftercare (Comfort & Skin Protection)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res9 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": ["ear_padding", "nares_water_lube", "reassure_anxiety", "document_care"]}},
    )
    assert res9.status_code == 200
    assert res9.json["success"] is True

    # 12. Step 10: Debrief (Reflection) -> Completes Mission & Awards Badge!
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res10 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"reflection_text": "I learned to calibrate FiO2 according to patient need and avoid combustible petroleum products during oxygen therapy."}},
    )
    assert res10.status_code == 200
    assert res10.json["success"] is True
    assert res10.json["is_mission_completed"] is True
    assert res10.json["badge_awarded"] is not None
    assert "Oxygen Guardian" in res10.json["badge_awarded"]["name"]

    # 13. Verify Database Records
    with app.app_context():
        completed_run = db.session.get(MissionRun, run_id)
        assert completed_run.status == "completed"

        progress = db.session.execute(select(MissionProgress)).scalars().first()
        assert progress.status == "completed"

        session_badge = db.session.execute(select(SessionBadge)).scalars().first()
        assert session_badge is not None
        badge = db.session.get(Badge, session_badge.badge_id)
        assert badge.slug == "oxygen-guardian"

    # 14. Verify Ward Display reflects completion and earned badge
    ward_res = client.get("/ward")
    assert ward_res.status_code == 200
    ward_html = ward_res.get_data(as_text=True)
    assert "Completed" in ward_html
    assert "Review / Replay mission" in ward_html
    assert "Oxygen Guardian" in ward_html
    assert "Unlocked & Earned!" in ward_html
