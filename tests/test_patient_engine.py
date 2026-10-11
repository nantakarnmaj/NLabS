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
