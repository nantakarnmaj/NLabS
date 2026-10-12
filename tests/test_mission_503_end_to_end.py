"""End-to-end integration test completing Room 503: Open the Airway (Nebulization Mission)."""

from __future__ import annotations

from sqlalchemy import select
from app.extensions import db
from app.models.run import MissionRun
from app.models.progress import MissionProgress
from app.models.badge import SessionBadge, Badge
from seed import run_all_seeds


def test_room_503_full_playthrough_and_badge_award(client, app):
    """Verify learner completes all 10 activities of Room 503, earns 'Nebulizer Navigator', and sees completion on ward."""
    with app.app_context():
        run_all_seeds()

    # 1. Start student session
    start_res = client.post("/session/start")
    assert start_res.status_code == 302

    # 2. Access Room 503
    mission_res = client.get("/missions/open-the-airway")
    assert mission_res.status_code == 200
    html = mission_res.get_data(as_text=True)
    assert "Activity 1 of 10" in html
    assert "Meet Ms. Mali" in html
    assert "Acute Bronchospasm" in html

    with app.app_context():
        run = db.session.execute(
            select(MissionRun).order_by(MissionRun.id.desc())
        ).scalars().first()
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
        json={"payload": {"selected_keys": [
            "expiratory_wheezing", "chest_tightness", "tachypnea_rr24", "mild_hypoxemia_93"
        ]}},
    )
    assert res2.status_code == 200
    assert res2.json["success"] is True

    # 5. Step 3: Medication Check (10 Rights) - Test Hazard first, then retry
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    # Hazard attempt: dilute with distilled water
    res3_hazard = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": [
            "right_patient_mali", "right_drug_salbutamol", "dilute_with_distilled_water"
        ]}},
    )
    assert res3_hazard.status_code == 200
    assert res3_hazard.json["success"] is False
    assert res3_hazard.json["result_type"] == "retry"
    assert "Sterile Water" in res3_hazard.json["title"] or "น้ำกลั่น" in res3_hazard.json["title"]

    # Retry with correct 10 Rights
    res3 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": [
            "right_patient_mali", "right_drug_salbutamol", "right_dose_2_5mg",
            "right_route_inhalation", "right_time_stat", "check_expiry_and_clarity",
            "right_reason_indication", "right_assessment_evaluation",
            "right_education_patient", "right_documentation"
        ]}},
    )
    assert res3.status_code == 200
    assert res3.json["success"] is True

    # 6. Step 4: Sequence (Circuit Assembly)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res4 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"ordered_keys": [
            "step_inspect_parts",
            "step_instill_salbutamol",
            "step_seal_cup",
            "step_attach_mouthpiece",
            "step_connect_tubing_source",
        ]}},
    )
    assert res4.status_code == 200
    assert res4.json["success"] is True

    # 7. Step 5: Safety Check (Positioning & 6-8 L/min Flow Rate)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res5 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": [
            "high_fowlers_position", "flow_rate_6_to_8_lpm", "keep_cup_vertical"
        ]}},
    )
    assert res5.status_code == 200
    assert res5.json["success"] is True

    # 8. Step 6: Troubleshooting ("Why No Mist?")
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res6 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": ["check_tubing_and_cup_orientation", "check_liquid_below_baffle"]}},
    )
    assert res6.status_code == 200
    assert res6.json["success"] is True

    # 9. Step 7: Decision (Coaching Inhalation Technique)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res7 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "slow_deep_mouth_breath_hold"}},
    )
    assert res7.status_code == 200
    assert res7.json["success"] is True

    # 10. Step 8: Troubleshooting / Decision (Adverse Effects Challenge) - Test Hazard first
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res8_hazard = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "give_iv_beta_blocker"}},
    )
    assert res8_hazard.status_code == 200
    assert res8_hazard.json["success"] is False
    assert res8_hazard.json["result_type"] == "retry"
    assert "Contraindication" in res8_hazard.json["title"]

    res8 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "reassure_and_monitor_expected_saba_effects"}},
    )
    assert res8.status_code == 200
    assert res8.json["success"] is True

    # 11. Step 9: Aftercare (Lung Auscultation & Post-Care)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res9 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": [
            "reauscultate_bilateral_lungs", "rinse_mouth_spit",
            "rinse_and_air_dry_cup", "document_response"
        ]}},
    )
    assert res9.status_code == 200
    assert res9.json["success"] is True

    # 12. Step 10: Debrief (Reflection) -> Completes Mission & Awards Badge!
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res10 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"reflection_text": "I learned to verify the 10 rights of medication, calibrate gas flow to 6-8 L/min, instruct slow mouth breathing, and monitor beta-2 adverse effects with reassurance."}},
    )
    assert res10.status_code == 200
    assert res10.json["success"] is True
    assert res10.json["is_mission_completed"] is True
    assert res10.json["badge_awarded"] is not None
    assert "Nebulizer Navigator" in res10.json["badge_awarded"]["name"]

    # 13. Verify Database Records
    with app.app_context():
        completed_run = db.session.get(MissionRun, run_id)
        assert completed_run.status == "completed"

        progress = db.session.execute(
            select(MissionProgress).join(MissionRun, MissionProgress.session_id == MissionRun.session_id).where(
                MissionProgress.status == "completed"
            )
        ).scalars().first()
        assert progress is not None
        assert progress.status == "completed"

        session_badges = db.session.execute(select(SessionBadge)).scalars().all()
        badge_slugs = []
        for sb in session_badges:
            b = db.session.get(Badge, sb.badge_id)
            badge_slugs.append(b.slug)
        assert "nebulizer-navigator" in badge_slugs

    # 14. Verify Ward Display reflects completion and earned badge
    ward_res = client.get("/ward")
    assert ward_res.status_code == 200
    ward_html = ward_res.get_data(as_text=True)
    assert "Completed" in ward_html
    assert "Nebulizer Navigator" in ward_html
    assert "Unlocked & Earned!" in ward_html
