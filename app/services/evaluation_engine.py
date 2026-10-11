"""Reusable evaluation engine for clinical nursing activities.

Evaluates student responses against database-configured rules and generates targeted,
formative feedback with physiological patient effects.
"""

from __future__ import annotations

import html
import logging
from typing import Any
from app.models.activity import Activity, ActivityOption, ProcedureStep, Feedback

logger = logging.getLogger(__name__)


def evaluate_activity(activity: Activity, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch evaluation to appropriate evaluator based on activity type.

    Returns:
        dict: {
            "success": bool,
            "result_type": str ('success', 'retry', 'guidance'),
            "title": str,
            "message": str,
            "clinical_rationale": str,
            "hint": str | None,
            "patient_effect": dict | None,
            "evidence": dict,
        }
    """
    act_type = activity.activity_type

    if act_type in ("intro", "outcome"):
        return evaluate_acknowledgment(activity, response_payload)
    elif act_type in ("clinical_cues", "equipment_select", "medication_check", "safety_check", "aftercare"):
        return evaluate_selection(activity, response_payload)
    elif act_type == "sequence":
        return evaluate_sequence(activity, response_payload)
    elif act_type in ("decision", "troubleshooting"):
        return evaluate_decision(activity, response_payload)
    elif act_type == "matching":
        return evaluate_matching(activity, response_payload)
    elif act_type == "debrief":
        return evaluate_debrief(activity, response_payload)
    else:
        logger.warning("Unknown activity type: %s, falling back to acknowledgment", act_type)
        return evaluate_acknowledgment(activity, response_payload)


def evaluate_acknowledgment(activity: Activity, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Acknowledge informational screens."""
    feedback = next((f for f in activity.feedback_rules if f.trigger_type == "on_success"), None)
    title = feedback.title if feedback else "Acknowledged"
    message = feedback.message if feedback else "Proceeding to the next step."
    rationale = feedback.clinical_rationale if feedback else ""
    effect = feedback.patient_effect_json if feedback else None

    return {
        "success": True,
        "result_type": "success",
        "title": title,
        "message": message,
        "clinical_rationale": rationale,
        "hint": None,
        "patient_effect": effect,
        "evidence": {"acknowledged": True},
    }


def evaluate_selection(activity: Activity, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate multi-select options (cues, equipment, safety, aftercare)."""
    selected_keys = set(response_payload.get("selected_keys", []))
    correct_options = {opt.option_key: opt for opt in activity.options if opt.is_correct}
    incorrect_options = {opt.option_key: opt for opt in activity.options if not opt.is_correct}

    correct_selected = selected_keys.intersection(correct_options.keys())
    incorrect_selected = selected_keys.intersection(incorrect_options.keys())
    missing_correct = set(correct_options.keys()) - selected_keys

    # Success if all correct selected and no incorrect selected
    is_success = (len(incorrect_selected) == 0) and (len(missing_correct) == 0)

    # Find matching feedback rules
    feedback_rules = {f.trigger_key: f for f in activity.feedback_rules if f.trigger_key}

    if is_success:
        fb = next((f for f in activity.feedback_rules if f.trigger_type == "on_success"), None)
        title = fb.title if fb else "Excellent Clinical Decision"
        message = fb.message if fb else "You correctly identified all required elements."
        rationale = fb.clinical_rationale if fb else "All selected items align with patient safety protocols."
        effect = fb.patient_effect_json if fb else None
        return {
            "success": True,
            "result_type": "success",
            "title": title,
            "message": message,
            "clinical_rationale": rationale,
            "hint": None,
            "patient_effect": effect,
            "evidence": {"selected_keys": list(selected_keys)},
        }
    else:
        # Check if an incorrect choice triggered a specific caution/critical feedback
        specific_fb = None
        for inc_key in incorrect_selected:
            if inc_key in feedback_rules:
                specific_fb = feedback_rules[inc_key]
                break

        if specific_fb:
            title = specific_fb.title
            message = specific_fb.message
            rationale = specific_fb.clinical_rationale
            hint = specific_fb.hint
            effect = specific_fb.patient_effect_json
        else:
            default_err = next((f for f in activity.feedback_rules if f.trigger_type == "on_mistake"), None)
            title = default_err.title if default_err else "Review Selection"
            message = default_err.message if default_err else "Some choices were missing or inappropriate for this clinical situation."
            rationale = default_err.clinical_rationale if default_err else "Carefully re-read the patient's presentation and safety parameters."
            hint = default_err.hint if default_err else "Focus on airway protection and sterile barriers."
            effect = default_err.patient_effect_json if default_err else None

        return {
            "success": False,
            "result_type": "retry",
            "title": title,
            "message": message,
            "clinical_rationale": rationale,
            "hint": hint,
            "patient_effect": effect,
            "evidence": {"selected_keys": list(selected_keys)},
        }


def evaluate_sequence(activity: Activity, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate procedural sequence with targeted hints rather than full spoilers."""
    submitted_keys: list[str] = response_payload.get("ordered_keys", [])
    steps = sorted(activity.procedure_steps, key=lambda s: s.correct_order)
    expected_keys = [s.step_key for s in steps]

    if submitted_keys == expected_keys:
        fb = next((f for f in activity.feedback_rules if f.trigger_type == "on_success"), None)
        title = fb.title if fb else "Procedure Correctly Sequenced"
        message = fb.message if fb else "Each step was sequenced in optimal clinical order."
        rationale = fb.clinical_rationale if fb else "Following this sequence minimizes hypoxia and mucosal injury."
        effect = fb.patient_effect_json if fb else None

        return {
            "success": True,
            "result_type": "success",
            "title": title,
            "message": message,
            "clinical_rationale": rationale,
            "hint": None,
            "patient_effect": effect,
            "evidence": {"ordered_keys": submitted_keys},
        }

    # Find the earliest out-of-order step to give a targeted hint
    first_inverted_step = None
    step_dict = {s.step_key: s for s in steps}
    for i, submitted_key in enumerate(submitted_keys):
        expected_key = expected_keys[i] if i < len(expected_keys) else None
        if submitted_key != expected_key:
            first_inverted_step = step_dict.get(submitted_key)
            break

    # Look for feedback triggered on mistake or specific inverted step
    fb = next((f for f in activity.feedback_rules if f.trigger_type == "on_mistake"), None)
    title = fb.title if fb else "Sequence Needs Adjustment"
    message = fb.message if fb else "The sequence contains steps in an unsafe or sub-optimal order."
    rationale = fb.clinical_rationale if fb else "Ensure pre-oxygenation and sterile discipline occur before inserting the catheter."

    if first_inverted_step and first_inverted_step.rationale:
        hint = f"Hint regarding '{first_inverted_step.step_text}': {first_inverted_step.rationale}"
    elif fb and fb.hint:
        hint = fb.hint
    else:
        hint = "Remember: Always hyper-oxygenate before introducing the catheter into the artificial airway."

    effect = fb.patient_effect_json if fb else None

    return {
        "success": False,
        "result_type": "retry",
        "title": title,
        "message": message,
        "clinical_rationale": rationale,
        "hint": hint,
        "patient_effect": effect,
        "evidence": {"ordered_keys": submitted_keys},
    }


def evaluate_decision(activity: Activity, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a single decision or acute troubleshooting response."""
    chosen_key = response_payload.get("chosen_key")
    selected_option = next((opt for opt in activity.options if opt.option_key == chosen_key), None)

    if not selected_option:
        return {
            "success": False,
            "result_type": "retry",
            "title": "Selection Required",
            "message": "Please choose an action to proceed.",
            "clinical_rationale": "",
            "hint": "Assess the patient monitor and decide your immediate action.",
            "patient_effect": None,
            "evidence": {},
        }

    feedback_rules = {f.trigger_key: f for f in activity.feedback_rules if f.trigger_key}
    fb = feedback_rules.get(chosen_key)

    if selected_option.is_correct:
        title = fb.title if fb else "Correct Action Taken"
        message = fb.message if fb else "You made the appropriate clinical intervention."
        rationale = fb.clinical_rationale if fb else selected_option.description
        effect = fb.patient_effect_json if fb else None
        return {
            "success": True,
            "result_type": "success",
            "title": title,
            "message": message,
            "clinical_rationale": rationale,
            "hint": None,
            "patient_effect": effect,
            "evidence": {"chosen_key": chosen_key},
        }
    else:
        title = fb.title if fb else "Unsafe or Suboptimal Action"
        message = fb.message if fb else "This action does not address the acute safety threat."
        rationale = fb.clinical_rationale if fb else selected_option.description
        hint = fb.hint if fb else "Prioritize immediate oxygenation and airway clearance."
        effect = fb.patient_effect_json if fb else {"spo2_delta": -4}
        return {
            "success": False,
            "result_type": "retry",
            "title": title,
            "message": message,
            "clinical_rationale": rationale,
            "hint": hint,
            "patient_effect": effect,
            "evidence": {"chosen_key": chosen_key},
        }


def evaluate_debrief(activity: Activity, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Formative debriefing reflection. Accepts bounded text without numeric grading."""
    raw_text = str(response_payload.get("reflection_text", "")).strip()
    clean_text = html.escape(raw_text)[:1500]  # bounded sanitized length

    if len(clean_text) < 5:
        return {
            "success": False,
            "result_type": "retry",
            "title": "Reflection Required",
            "message": "Please share at least one key takeaway regarding patient safety before completing the mission.",
            "clinical_rationale": "Reflective practice solidifies procedural memory and safety awareness.",
            "hint": "What step felt most critical to preventing patient harm?",
            "patient_effect": None,
            "evidence": {},
        }

    fb = next((f for f in activity.feedback_rules if f.trigger_type == "on_success"), None)
    title = fb.title if fb else "Mission Complete — Well Done!"
    message = fb.message if fb else "Thank you for reflecting on clinical airway safety."
    rationale = fb.clinical_rationale if fb else "Continuous reflection is a foundational trait of safe clinical nurses."
    effect = fb.patient_effect_json if fb else None

    return {
        "success": True,
        "result_type": "success",
        "title": title,
        "message": message,
        "clinical_rationale": rationale,
        "hint": None,
        "patient_effect": effect,
        "evidence": {"reflection_text": clean_text},
    }


def evaluate_matching(activity: Activity, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate matching mini-scenarios to clinical devices (e.g. Oxygen Device Match Challenge)."""
    content = activity.content_json or {}
    match_items = content.get("matches", [])
    pairs: dict[str, str] = response_payload.get("pairs", {})

    if not isinstance(pairs, dict):
        pairs = {}

    # Check if all scenarios have been matched
    expected_prompt_keys = [m["prompt_key"] for m in match_items]
    unanswered = [k for k in expected_prompt_keys if not pairs.get(k)]

    if unanswered:
        return {
            "success": False,
            "result_type": "retry",
            "title": "Match All Patient Scenarios",
            "message": "Please pair each clinical patient scenario with an appropriate oxygen delivery device.",
            "clinical_rationale": "Different clinical scenarios require specific FiO2 concentrations and flow rates.",
            "hint": "Consider the patient's acute severity, comfort, and risk of CO2 retention.",
            "patient_effect": None,
            "evidence": {"submitted_pairs": pairs},
        }

    # Evaluate each match
    mismatches = []
    for m in match_items:
        pkey = m["prompt_key"]
        chosen = pairs.get(pkey)
        correct = m.get("correct_target_key")
        if chosen != correct:
            mismatches.append({
                "prompt_key": pkey,
                "prompt_label": m.get("prompt_label", pkey),
                "chosen": chosen,
                "correct": correct,
                "rationale": m.get("rationale", ""),
                "hint": m.get("hint", ""),
            })

    if mismatches:
        first_mismatch = mismatches[0]
        # Check if there is specific feedback rule for this mismatch
        fb_rule = next(
            (f for f in activity.feedback_rules if f.trigger_type == "on_selection" and f.trigger_key == f"{first_mismatch['prompt_key']}:{first_mismatch['chosen']}"),
            None
        )
        if not fb_rule:
            fb_rule = next(
                (f for f in activity.feedback_rules if f.trigger_key == first_mismatch["prompt_key"] or f.trigger_key == first_mismatch["chosen"]),
                None
            )

        title = fb_rule.title if fb_rule else "Review Device Pairing"
        message = fb_rule.message if fb_rule else f"Notice the clinical needs of {first_mismatch['prompt_label']}. {first_mismatch['rationale']}"
        rationale = fb_rule.clinical_rationale if fb_rule else first_mismatch["rationale"]
        hint = fb_rule.hint if fb_rule else first_mismatch["hint"] or "Recall the FiO2 concentration and control provided by each device."
        effect = fb_rule.patient_effect_json if fb_rule else None

        return {
            "success": False,
            "result_type": "retry",
            "title": title,
            "message": message,
            "clinical_rationale": rationale,
            "hint": hint,
            "patient_effect": effect,
            "evidence": {"submitted_pairs": pairs, "mismatch_count": len(mismatches)},
        }

    # All correct!
    success_fb = next((f for f in activity.feedback_rules if f.trigger_type == "on_success"), None)
    title = success_fb.title if success_fb else "All Devices Correctly Matched!"
    message = success_fb.message if success_fb else "Excellent clinical reasoning. You correctly selected each oxygen delivery system based on clinical urgency, FiO2 precision, and patient comfort."
    rationale = success_fb.clinical_rationale if success_fb else "Selecting the proper device ensures target oxygenation while minimizing risks of hyperoxia or hypoventilation."
    effect = success_fb.patient_effect_json if success_fb else None

    return {
        "success": True,
        "result_type": "success",
        "title": title,
        "message": message,
        "clinical_rationale": rationale,
        "hint": None,
        "patient_effect": effect,
        "evidence": {"submitted_pairs": pairs, "all_matched": True},
    }
