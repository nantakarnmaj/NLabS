"""Deterministic patient simulation engine for respiratory nursing scenarios.

Applies validated, bounded clinical state transitions based on approved content rules.
Does not use generative AI for state transitions.
"""

from __future__ import annotations

import copy
import logging

logger = logging.getLogger(__name__)

# Physiological clamping boundaries
BOUNDS: dict[str, tuple[int | float, int | float]] = {
    "spo2": (70, 100),
    "rr": (8, 50),
    "hr": (40, 190),
    "distress": (0, 5),
}

ALLOWED_ENUMS: dict[str, set[str]] = {
    "secretions": {"none", "minimal", "moderate", "copious"},
    "breath_sound": {"clear", "rhonchi", "stridor", "wheezing", "diminished", "coarse_rhonchi"},
    "consciousness": {"alert", "lethargic", "restless", "obtunded", "confused"},
}


def clamp(val: int | float, low: int | float, high: int | float) -> int | float:
    """Clamp a numeric value between low and high bounds."""
    return max(low, min(high, val))


def normalize_state(raw_state: dict) -> dict:
    """Validate and normalize a patient state dictionary."""
    state = copy.deepcopy(raw_state or {})

    # Defaults if missing
    state.setdefault("spo2", 95)
    state.setdefault("rr", 18)
    state.setdefault("hr", 80)
    state.setdefault("distress", 1)
    state.setdefault("secretions", "minimal")
    state.setdefault("breath_sound", "clear")
    state.setdefault("consciousness", "alert")

    # Clamp numeric values
    for var, (low, high) in BOUNDS.items():
        if var in state and isinstance(state[var], (int, float)):
            state[var] = clamp(state[var], low, high)

    # Validate enums
    for var, allowed in ALLOWED_ENUMS.items():
        if var in state and state[var] not in allowed:
            state[var] = next(iter(allowed))

    return state


def apply_patient_effects(current_state: dict, effect_spec: dict | None) -> tuple[dict, list[str]]:
    """Apply approved effect operations to the patient state deterministically.

    Args:
        current_state: Existing normalized patient vitals and state.
        effect_spec: Mapping of delta and set operations (e.g. {"spo2_delta": -5, "secretions_set": "minimal"}).

    Returns:
        tuple of (new_normalized_state, list_of_event_descriptions)
    """
    new_state = normalize_state(current_state)
    events: list[str] = []

    if not effect_spec or not isinstance(effect_spec, dict):
        return new_state, events

    # 1. Process relative delta changes
    for key, delta in effect_spec.items():
        if key.endswith("_delta") and isinstance(delta, (int, float)):
            var = key[:-6]
            if var in BOUNDS:
                old_val = new_state.get(var, 0)
                low, high = BOUNDS[var]
                new_val = clamp(old_val + delta, low, high)
                new_state[var] = new_val
                direction = "increased" if delta > 0 else "decreased"
                events.append(f"{var.upper()} {direction} from {old_val} to {new_val}")

    # 2. Process absolute set changes
    for key, val in effect_spec.items():
        if key.endswith("_set"):
            var = key[:-4]
            if var in BOUNDS and isinstance(val, (int, float)):
                low, high = BOUNDS[var]
                clamped_val = clamp(val, low, high)
                new_state[var] = clamped_val
                events.append(f"{var.upper()} set to {clamped_val}")
            elif var in ALLOWED_ENUMS and isinstance(val, str) and val in ALLOWED_ENUMS[var]:
                old_val = new_state.get(var)
                new_state[var] = val
                events.append(f"{var.replace('_', ' ').title()} changed from {old_val} to {val}")

    return new_state, events


def compute_step_patient_state(scenario, activities, viewing_activity) -> dict:
    """Compute the clinical patient state corresponding to the activity being viewed.

    Before suctioning & aftercare (Steps 1..7):
      Patient displays respiratory distress/obstruction (coarse rhonchi, copious secretions, SpO2 91-95%).
    After suctioning & aftercare (Steps 8..10):
      Patient displays restored airway patency (clear breath sounds, minimal secretions, SpO2 97%, HR 78, RR 18).
    """
    state = copy.deepcopy(scenario.initial_state_json or {}) if scenario else {}
    if not activities or not viewing_activity:
        return normalize_state(state)

    target_order = viewing_activity.display_order
    sorted_activities = sorted(activities, key=lambda a: a.display_order)

    for a in sorted_activities:
        if a.display_order < target_order:
            effect = None
            for fb in a.feedback_rules:
                if fb.trigger_type == "on_success" and fb.patient_effect_json:
                    effect = fb.patient_effect_json
                    break
                elif fb.trigger_key and fb.feedback_type == "positive" and fb.patient_effect_json:
                    effect = fb.patient_effect_json
                    break
            if effect:
                state, _ = apply_patient_effects(state, effect)

    return normalize_state(state)
