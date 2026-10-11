"""Unit tests for deterministic patient simulation engine."""

from __future__ import annotations

from app.services.patient_engine import apply_patient_effects, normalize_state, clamp


def test_clamp():
    """Verify numeric clamping adheres to boundaries."""
    assert clamp(50, 70, 100) == 70
    assert clamp(110, 70, 100) == 100
    assert clamp(85, 70, 100) == 85


def test_normalize_state_defaults_and_clamping():
    """Verify normalize_state sets standard defaults and clamps values."""
    raw = {
        "spo2": 115,  # above max
        "rr": 5,      # below min
        "hr": 90,
        "secretions": "invalid_val",
    }
    normalized = normalize_state(raw)
    assert normalized["spo2"] == 100
    assert normalized["rr"] == 8
    assert normalized["hr"] == 90
    assert normalized["secretions"] in {"none", "minimal", "moderate", "copious"}


def test_apply_patient_effects_deltas_and_sets():
    """Verify relative deltas and absolute sets produce deterministic state transitions."""
    initial = {
        "spo2": 91,
        "rr": 26,
        "hr": 96,
        "distress": 3,
        "secretions": "copious",
        "breath_sound": "rhonchi",
    }

    # Apply delta
    effects = {
        "spo2_delta": -5,
        "hr_delta": +10,
        "distress_delta": +1,
        "secretions_set": "moderate",
    }
    new_state, events = apply_patient_effects(initial, effects)

    assert new_state["spo2"] == 86
    assert new_state["hr"] == 106
    assert new_state["distress"] == 4
    assert new_state["secretions"] == "moderate"
    assert len(events) == 4

    # Verify clamping during extreme delta
    extreme_effects = {"spo2_delta": -50}
    extreme_state, _ = apply_patient_effects(new_state, extreme_effects)
    assert extreme_state["spo2"] == 70  # clamped to physiological minimum


def test_compute_step_patient_state():
    """Verify deterministic per-step patient state replay for review and active play."""
    from app.services.patient_engine import compute_step_patient_state
    from unittest.mock import MagicMock

    scenario = MagicMock()
    scenario.initial_state_json = {
        "spo2": 91,
        "hr": 96,
        "rr": 26,
        "distress": 3,
        "breath_sound": "coarse_rhonchi",
        "secretions": "copious",
    }

    fb_act2 = MagicMock(
        trigger_type="on_success",
        patient_effect_json={"spo2_delta": +2, "distress_delta": -1}
    )
    fb_act3 = MagicMock(
        trigger_type="on_success",
        patient_effect_json={"spo2_set": 97, "distress_set": 0, "breath_sound_set": "clear"}
    )

    act1 = MagicMock(display_order=1, feedback_rules=[])
    act2 = MagicMock(display_order=2, feedback_rules=[fb_act2])
    act3 = MagicMock(display_order=3, feedback_rules=[fb_act3])
    activities = [act1, act2, act3]

    # Viewing step 1 (before act1 effects or step 2)
    s1 = compute_step_patient_state(scenario, activities, act1)
    assert s1["spo2"] == 91
    assert s1["distress"] == 3

    # Viewing step 2 (after act1 completed, before act2 effects)
    s2 = compute_step_patient_state(scenario, activities, act2)
    assert s2["spo2"] == 91

    # Viewing step 3 (after act1 and act2 effects applied)
    s3 = compute_step_patient_state(scenario, activities, act3)
    assert s3["spo2"] == 93
    assert s3["distress"] == 2

