"""End-to-end integration test completing Room 504: Respiratory Rescue (Integrated Emergency Scenario).

Tests:
1. Prerequisite enforcement: Room 504 is locked until Rooms 501, 502, and 503 are all completed.
2. Dynamic unlocking on the Ward map once prerequisites are completed.
3. Complete playthrough of all 10 activities with formative feedback and hazard triggers.
4. Capstone badge award ('Respiratory Ready') and Ward showcase update with all 4 badges unlocked.
"""

from __future__ import annotations

from sqlalchemy import select
from app.extensions import db
from app.models.run import MissionRun
from app.models.progress import MissionProgress
from app.models.badge import SessionBadge, Badge
from seed import run_all_seeds


def _complete_room_501(client, app, run_id: int):
    """Helper to complete Room 501 activities."""
    steps_payloads = [
        {"acknowledged": True},
        {"selected_keys": ["audible_gurgling", "rhonchi", "desaturation"]},
        {"selected_keys": ["suction_set", "vacuum_100_120", "sterile_saline", "face_shield"]},
        {"selected_keys": ["pre_oxygenate", "semi_fowler", "monitor_vitals"]},
        {"ordered_keys": ["step_preox", "step_don_sterile", "step_insert_no_suction", "step_suction_withdraw", "step_post_oxygenate"]},
        {"chosen_key": "only_on_withdraw"},
        {"chosen_key": "abort_and_oxygenate"},
        {"selected_keys": ["re_auscultate", "flush_tubing", "restore_fio2", "document_care"]},
        {"acknowledged": True},
        {"reflection_text": "I learned to always hyper-oxygenate prior to suctioning."},
    ]
    for p in steps_payloads:
        with app.app_context():
            run = db.session.get(MissionRun, run_id)
            act_id = run.current_activity_id
        r = client.post(f"/api/runs/{run_id}/activities/{act_id}/submit", json={"payload": p})
        assert r.status_code == 200
        assert r.json["success"] is True


def _complete_room_502(client, app, run_id: int):
    """Helper to complete Room 502 activities."""
    steps_payloads = [
        {"acknowledged": True},
        {"selected_keys": ["spo2_88", "tachypnea_rr28", "tachycardia_hr104", "dyspnea_anxiety"]},
        {"selected_keys": ["nasal_cannula_3l"]},
        {"ordered_keys": ["step_verify_source", "step_set_flow", "step_verify_gas_flow", "step_insert_prongs", "step_loop_ears_snug"]},
        {"selected_keys": ["no_smoking_signs", "sterile_water_level", "grounded_electrical", "avoid_petroleum"]},
        {"chosen_key": "maintain_and_reassess"},
        {"pairs": {
            "case_mild_postop": "nasal_cannula",
            "case_copd_precise": "nasal_cannula_copd",
            "case_severe_hypoxemia": "nrb_mask",
            "case_tracheostomy": "tracheostomy_collar",
        }},
        {"chosen_key": "check_patient_and_tubing"},
        {"selected_keys": ["ear_padding", "nares_water_lube", "reassure_anxiety", "document_care"]},
        {"reflection_text": "I learned to calibrate FiO2 according to patient need."},
    ]
    for i, p in enumerate(steps_payloads):
        with app.app_context():
            run = db.session.get(MissionRun, run_id)
            act_id = run.current_activity_id
        r = client.post(f"/api/runs/{run_id}/activities/{act_id}/submit", json={"payload": p})
        assert r.status_code == 200
        assert r.json["success"] is True, f"Failed at Room 502 step {i}: payload={p}, res={r.json}"


def _complete_room_503(client, app, run_id: int):
    """Helper to complete Room 503 activities."""
    steps_payloads = [
        {"acknowledged": True},
        {"selected_keys": ["expiratory_wheezing", "chest_tightness", "tachypnea_rr24", "mild_hypoxemia_93"]},
        {"selected_keys": [
            "right_patient_mali", "right_drug_salbutamol", "right_dose_2_5mg",
            "right_route_inhalation", "right_time_stat", "check_expiry_and_clarity",
            "right_reason_indication", "right_assessment_evaluation",
            "right_education_patient", "right_documentation"
        ]},
        {"ordered_keys": ["step_inspect_parts", "step_instill_salbutamol", "step_seal_cup", "step_attach_mouthpiece", "step_connect_tubing_source"]},
        {"selected_keys": ["high_fowlers_position", "flow_rate_6_to_8_lpm", "keep_cup_vertical"]},
        {"chosen_key": "check_tubing_and_cup_orientation"},
        {"chosen_key": "slow_deep_mouth_breath_hold"},
        {"chosen_key": "reassure_and_monitor_expected_saba_effects"},
        {"selected_keys": ["reauscultate_bilateral_lungs", "rinse_mouth_spit", "rinse_and_air_dry_cup", "document_response"]},
        {"reflection_text": "I learned to calibrate flow rate to 6-8 L/min."},
    ]
    for p in steps_payloads:
        with app.app_context():
            run = db.session.get(MissionRun, run_id)
            act_id = run.current_activity_id
        r = client.post(f"/api/runs/{run_id}/activities/{act_id}/submit", json={"payload": p})
        assert r.status_code == 200
        assert r.json["success"] is True


def test_room_504_prerequisites_and_full_rescue_playthrough(client, app):
    """Comprehensive test for Room 504:

    1. Verify Room 504 is locked initially.
    2. Direct access returns 403 Forbidden.
    3. Complete Rooms 501, 502, and 503.
    4. Verify Room 504 unlocks on Ward map.
    5. Complete all 10 activities of Room 504 including hazard retries.
    6. Verify 'Respiratory Ready' badge award and Ward showcase.
    """
    with app.app_context():
        run_all_seeds()

    # 1. Start student session
    start_res = client.post("/session/start")
    assert start_res.status_code == 302

    # 2. Check Ward map: Room 504 is Locked initially
    ward_res1 = client.get("/ward")
    assert ward_res1.status_code == 200
    ward_html1 = ward_res1.get_data(as_text=True)
    assert "Room 504" in ward_html1
    assert "Respiratory Rescue" in ward_html1
    assert "Requires completion of" in ward_html1

    # 3. Direct GET to Room 504 before prerequisites are complete -> 403 Forbidden
    res_direct_locked = client.get("/missions/respiratory-rescue")
    assert res_direct_locked.status_code == 403
    assert "Room Locked" in res_direct_locked.get_data(as_text=True)

    # 4. Play and complete Room 501
    client.get("/missions/clear-the-airway")
    with app.app_context():
        run501 = db.session.execute(select(MissionRun).order_by(MissionRun.id.desc())).scalars().first()
    _complete_room_501(client, app, run501.id)

    # Still locked (502 and 503 remain)
    res_direct_locked2 = client.get("/missions/respiratory-rescue")
    assert res_direct_locked2.status_code == 403

    # 5. Play and complete Room 502
    client.get("/missions/support-the-breath")
    with app.app_context():
        run502 = db.session.execute(select(MissionRun).order_by(MissionRun.id.desc())).scalars().first()
    _complete_room_502(client, app, run502.id)

    # Still locked (503 remains)
    res_direct_locked3 = client.get("/missions/respiratory-rescue")
    assert res_direct_locked3.status_code == 403

    # 6. Play and complete Room 503
    client.get("/missions/open-the-airway")
    with app.app_context():
        run503 = db.session.execute(select(MissionRun).order_by(MissionRun.id.desc())).scalars().first()
    _complete_room_503(client, app, run503.id)

    # 7. Check Ward map: Room 504 is NOW UNLOCKED and Ready!
    ward_res2 = client.get("/ward")
    assert ward_res2.status_code == 200
    ward_html2 = ward_res2.get_data(as_text=True)
    assert "Start mission" in ward_html2
    assert "Integrated clinical simulation ready to play." in ward_html2

    # 8. Access Room 504 -> 200 OK!
    res_504 = client.get("/missions/respiratory-rescue")
    assert res_504.status_code == 200
    html_504 = res_504.get_data(as_text=True)
    assert "Mr. Prasert" in html_504
    assert "First Look" in html_504
    assert "Acute Respiratory Distress" in html_504

    with app.app_context():
        run504 = db.session.execute(select(MissionRun).order_by(MissionRun.id.desc())).scalars().first()
        assert run504 is not None
        run_id = run504.id

    # 9. Step 1: Intro (acknowledge)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res1 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"acknowledged": True}},
    )
    assert res1.status_code == 200
    assert res1.json["success"] is True

    # 10. Step 2: Clinical Cues (First Look)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res2 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": [
            "severe_hypoxemia_87", "tachypnea_and_retractions",
            "copious_secretions_weak_cough", "bilateral_wheezes_and_rhonchi"
        ]}},
    )
    assert res2.status_code == 200
    assert res2.json["success"] is True

    # 11. Step 3: Emergency Prioritization (Test Hazard: Suction without oxygen)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res3_hazard = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "immediate_deep_suction_without_oxygen"}},
    )
    assert res3_hazard.status_code == 200
    assert res3_hazard.json["success"] is False
    assert res3_hazard.json["result_type"] == "retry"
    assert "Hypoxemia Hazard" in res3_hazard.json["title"]

    # Retry with correct priority action
    res3 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "position_upright_and_escalate_oxygen_nrb"}},
    )
    assert res3.status_code == 200
    assert res3.json["success"] is True

    # 12. Step 4: Safety Check: Equipment Setup (Test Hazard: 2 L/min on NRB)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res4_hazard = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": [
            "pre_inflate_nrb_bag", "set_nrb_flow_to_2_lpm", "suction_calibrated_100_120"
        ]}},
    )
    assert res4_hazard.status_code == 200
    assert res4_hazard.json["success"] is False
    assert res4_hazard.json["result_type"] == "retry"
    assert "Suffocation Hazard" in res4_hazard.json["title"]

    # Retry with correct setup
    res4 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": [
            "pre_inflate_nrb_bag", "flow_10_to_15_lpm",
            "suction_calibrated_100_120", "sterile_suction_technique"
        ]}},
    )
    assert res4.status_code == 200
    assert res4.json["success"] is True

    # 13. Step 5: Sequence: Airway Clearance Procedure
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res5 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"ordered_keys": [
            "step_pre_oxygenate",
            "step_lubricate_catheter",
            "step_advance_without_suction",
            "step_intermittent_suction_withdraw",
            "step_reapply_oxygen_evaluate",
        ]}},
    )
    assert res5.status_code == 200
    assert res5.json["success"] is True

    # 14. Step 6: Decision: Oxygen-Driven Nebulization
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res6 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "nebulize_with_oxygen_source_6_8_lpm"}},
    )
    assert res6.status_code == 200
    assert res6.json["success"] is True

    # 15. Step 7: Acute Deterioration Event (Test Hazard: Sedation)
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res7_hazard = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "administer_iv_diazepam_sedative"}},
    )
    assert res7_hazard.status_code == 200
    assert res7_hazard.json["success"] is False
    assert res7_hazard.json["result_type"] == "retry"
    assert "Fatal Medication Error" in res7_hazard.json["title"]

    # Retry with correct airway check & reassurance
    res7 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "assess_airway_patency_dislodged_plug_and_calm"}},
    )
    assert res7.status_code == 200
    assert res7.json["success"] is True

    # 16. Step 8: Call for Help & SBAR Escalation
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res8 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"chosen_key": "sbar_structured_urgent_handover"}},
    )
    assert res8.status_code == 200
    assert res8.json["success"] is True

    # 17. Step 9: Post-Rescue Continuing Care
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res9 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"selected_keys": [
            "continuous_pulse_ox_and_telemetry", "maintain_upright_fowlers",
            "frequent_lung_auscultation", "psychological_reassurance_family"
        ]}},
    )
    assert res9.status_code == 200
    assert res9.json["success"] is True

    # 18. Step 10: Capstone Debrief & Shift Reflection -> Completes Mission!
    with app.app_context():
        run = db.session.get(MissionRun, run_id)
        act_id = run.current_activity_id

    res10 = client.post(
        f"/api/runs/{run_id}/activities/{act_id}/submit",
        json={"payload": {"reflection_text": "I learned to prioritize high-flow oxygen before suctioning, drive nebulizers with oxygen in acute hypoxemia, avoid sedatives in agitated hypoxic patients, and use structured SBAR handover to escalate safely."}},
    )
    assert res10.status_code == 200
    assert res10.json["success"] is True
    assert res10.json["is_mission_completed"] is True
    assert res10.json["badge_awarded"] is not None
    assert "Respiratory Ready" in res10.json["badge_awarded"]["name"]

    # 19. Verify Database Records
    with app.app_context():
        completed_run = db.session.get(MissionRun, run_id)
        assert completed_run.status == "completed"

        progress = db.session.execute(
            select(MissionProgress).join(
                MissionRun, MissionProgress.session_id == MissionRun.session_id
            ).where(
                MissionProgress.mission_id == completed_run.mission_id,
                MissionProgress.status == "completed",
            )
        ).scalars().first()
        assert progress is not None

        session_badges = db.session.execute(select(SessionBadge)).scalars().all()
        badge_slugs = []
        for sb in session_badges:
            b = db.session.get(Badge, sb.badge_id)
            badge_slugs.append(b.slug)

        # All 4 badges earned!
        assert "airway-explorer" in badge_slugs
        assert "oxygen-guardian" in badge_slugs
        assert "nebulizer-navigator" in badge_slugs
        assert "respiratory-ready" in badge_slugs

    # 20. Verify Ward Display: All 4 badges unlocked & earned
    ward_res3 = client.get("/ward")
    assert ward_res3.status_code == 200
    ward_html3 = ward_res3.get_data(as_text=True)
    assert "Respiratory Ready" in ward_html3
    assert ward_html3.count("Unlocked & Earned!") == 4
