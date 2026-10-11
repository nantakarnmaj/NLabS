"""Unit tests for reusable activity evaluation engine."""

from __future__ import annotations

from app.models.activity import Activity, ActivityOption, ProcedureStep, Feedback
from app.services.evaluation_engine import evaluate_activity


def test_evaluate_sequence_correct_and_inverted():
    """Sequence evaluator accepts correct order and provides targeted hint for inversions."""
    act = Activity(activity_type="sequence", title="Step Order", instruction="Order steps")
    act.procedure_steps = [
        ProcedureStep(step_key="step_1", step_text="Pre-oxygenate", correct_order=1, rationale="Must oxygenate first"),
        ProcedureStep(step_key="step_2", step_text="Don gloves", correct_order=2, rationale="Maintain sterility"),
        ProcedureStep(step_key="step_3", step_text="Insert catheter", correct_order=3, rationale="Advance gently"),
    ]
    act.feedback_rules = [
        Feedback(trigger_type="on_success", title="Success", message="Ordered correctly"),
        Feedback(trigger_type="on_mistake", title="Mistake", message="Incorrect sequence", hint="Check gloves timing"),
    ]

    # 1. Correct sequence
    res_correct = evaluate_activity(act, {"ordered_keys": ["step_1", "step_2", "step_3"]})
    assert res_correct["success"] is True
    assert res_correct["result_type"] == "success"

    # 2. Inverted sequence
    res_inverted = evaluate_activity(act, {"ordered_keys": ["step_2", "step_1", "step_3"]})
    assert res_inverted["success"] is False
    assert res_inverted["result_type"] == "retry"
    assert "Pre-oxygenate" in res_inverted["hint"] or "gloves" in res_inverted["hint"]


def test_evaluate_selection_correct_and_hazards():
    """Selection evaluator verifies required options and identifies safety hazards."""
    act = Activity(activity_type="equipment_select", title="Equipment", instruction="Select gear")
    act.options = [
        ActivityOption(option_key="catheter", label="Sterile Catheter", is_correct=True, display_order=1),
        ActivityOption(option_key="gloves", label="Sterile Gloves", is_correct=True, display_order=2),
        ActivityOption(option_key="high_pressure", label="High Vacuum 200 mmHg", is_correct=False, display_order=3),
    ]
    act.feedback_rules = [
        Feedback(trigger_type="on_success", title="Ready", message="All good"),
        Feedback(trigger_type="on_selection", trigger_key="high_pressure", feedback_type="critical", title="Hazard", message="Vacuum too high", hint="Use 100-120 mmHg"),
    ]

    # Correct selection
    res_ok = evaluate_activity(act, {"selected_keys": ["catheter", "gloves"]})
    assert res_ok["success"] is True

    # Hazardous selection
    res_hazard = evaluate_activity(act, {"selected_keys": ["catheter", "high_pressure"]})
    assert res_hazard["success"] is False
    assert res_hazard["result_type"] == "retry"
    assert res_hazard["title"] == "Hazard"
    assert "100-120" in res_hazard["hint"]


def test_evaluate_debrief():
    """Debrief evaluator accepts non-empty reflection text and sanitizes HTML."""
    act = Activity(activity_type="debrief", title="Debrief", instruction="Reflect")
    act.feedback_rules = [
        Feedback(trigger_type="on_success", title="Completed", message="Good reflection"),
    ]

    # Too short -> retry
    res_short = evaluate_activity(act, {"reflection_text": "ok"})
    assert res_short["success"] is False
    assert res_short["result_type"] == "retry"

    # Valid reflection
    res_valid = evaluate_activity(act, {"reflection_text": "I learned to always hyperoxygenate Somchai before catheter insertion."})
    assert res_valid["success"] is True
    assert res_valid["result_type"] == "success"


def test_evaluate_matching():
    """Matching evaluator checks paired mini-scenarios and targets incorrect associations."""
    act = Activity(
        activity_type="matching",
        title="Device Match Challenge",
        instruction="Pair cases with devices",
        content_json={
            "matches": [
                {
                    "prompt_key": "case_mild",
                    "prompt_label": "Mild Hypoxemia",
                    "correct_target_key": "nasal_cannula",
                    "rationale": "Cannula allows eating/talking and delivers low-flow oxygen.",
                    "hint": "Select low-flow device.",
                },
                {
                    "prompt_key": "case_copd",
                    "prompt_label": "COPD Exacerbation",
                    "correct_target_key": "venturi_mask",
                    "rationale": "Venturi mask delivers precise fixed FiO2.",
                    "hint": "Look for calibrated fixed FiO2.",
                },
            ]
        },
    )
    act.feedback_rules = [
        Feedback(trigger_type="on_success", title="Matches Correct", message="All devices correctly paired"),
        Feedback(trigger_type="on_selection", trigger_key="case_copd:nrb_mask", title="Risk of Hyperoxia", message="NRB delivers uncontrolled high FiO2 which may blunt hypoxic drive"),
    ]

    # 1. Incomplete pairing -> retry
    res_incomplete = evaluate_activity(act, {"pairs": {"case_mild": "nasal_cannula"}})
    assert res_incomplete["success"] is False
    assert res_incomplete["result_type"] == "retry"
    assert "Match All" in res_incomplete["title"]

    # 2. Incorrect pairing with specific feedback rule -> retry with rationale
    res_wrong = evaluate_activity(act, {"pairs": {"case_mild": "nasal_cannula", "case_copd": "nrb_mask"}})
    assert res_wrong["success"] is False
    assert res_wrong["result_type"] == "retry"
    assert res_wrong["title"] == "Risk of Hyperoxia"

    # 3. All correct pairings -> success
    res_correct = evaluate_activity(act, {"pairs": {"case_mild": "nasal_cannula", "case_copd": "venturi_mask"}})
    assert res_correct["success"] is True
    assert res_correct["result_type"] == "success"
    assert res_correct["title"] == "Matches Correct"
