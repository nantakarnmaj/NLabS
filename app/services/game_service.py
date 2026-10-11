"""Game service orchestrating mission runs, activity submissions, and badge awards."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from app.extensions import db
from app.models.mission import Mission
from app.models.scenario import Scenario
from app.models.activity import Activity
from app.models.run import MissionRun, ActivityProgress, ActivityAttempt
from app.models.progress import MissionProgress
from app.models.badge import Badge, SessionBadge
from app.models.session import StudentSession
from app.services.patient_engine import apply_patient_effects
from app.services.evaluation_engine import evaluate_activity

logger = logging.getLogger(__name__)


def start_or_resume_run(session: StudentSession, mission_slug: str) -> tuple[MissionRun, bool]:
    """Start a new mission run or resume an active one for the given student session."""
    mission = db.session.execute(
        select(Mission).where((Mission.slug == mission_slug) | (Mission.room_number == mission_slug))
    ).scalar_one_or_none()

    if not mission:
        raise ValueError(f"Mission '{mission_slug}' not found")

    scenario = db.session.execute(
        select(Scenario).where(Scenario.mission_id == mission.id, Scenario.is_active.is_(True))
    ).scalar_one_or_none()

    if not scenario:
        raise ValueError(f"No active scenario found for mission '{mission_slug}'")

    # Enforce mission prerequisites
    from app.models.mission import MissionPrerequisite
    prereqs = db.session.execute(
        select(MissionPrerequisite).where(MissionPrerequisite.mission_id == mission.id)
    ).scalars().all()

    if prereqs:
        completed_ids = set(
            db.session.execute(
                select(MissionProgress.mission_id).where(
                    MissionProgress.session_id == session.id,
                    MissionProgress.status == "completed",
                )
            ).scalars().all()
        )
        for p in prereqs:
            if p.prerequisite_mission_id not in completed_ids:
                raise PermissionError(f"Prerequisite mission {p.prerequisite_mission_id} not completed for session {session.id}")

    # Check for existing in_progress run
    existing_run = db.session.execute(
        select(MissionRun).where(
            MissionRun.session_id == session.id,
            MissionRun.mission_id == mission.id,
            MissionRun.status == "in_progress",
        ).order_by(MissionRun.id.desc())
    ).scalars().first()

    if existing_run:
        return existing_run, False

    # Check for existing completed run (preserve completion showcase unless explicit replay)
    completed_run = db.session.execute(
        select(MissionRun).where(
            MissionRun.session_id == session.id,
            MissionRun.mission_id == mission.id,
            MissionRun.status == "completed",
        ).order_by(MissionRun.id.desc())
    ).scalars().first()

    if completed_run:
        return completed_run, False

    # Find first activity
    first_activity = db.session.execute(
        select(Activity).where(
            Activity.scenario_id == scenario.id,
            Activity.is_active.is_(True),
        ).order_by(Activity.display_order.asc())
    ).scalars().first()

    now = datetime.now(timezone.utc)
    new_run = MissionRun(
        session_id=session.id,
        mission_id=mission.id,
        scenario_id=scenario.id,
        status="in_progress",
        current_activity_id=first_activity.id if first_activity else None,
        patient_state_json=scenario.initial_state_json,
        state_revision=1,
        started_at=now,
    )
    db.session.add(new_run)

    # Ensure lasting MissionProgress record exists
    progress = db.session.execute(
        select(MissionProgress).where(
            MissionProgress.session_id == session.id,
            MissionProgress.mission_id == mission.id,
        )
    ).scalar_one_or_none()

    if not progress:
        progress = MissionProgress(
            session_id=session.id,
            mission_id=mission.id,
            status="in_progress",
            started_at=now,
        )
        db.session.add(progress)
    elif progress.status == "not_started":
        progress.status = "in_progress"
        progress.started_at = now

    db.session.commit()
    logger.info("Started new mission run %s for session %s", new_run.id, session.id)
    return new_run, True


def start_new_replay(session: StudentSession, mission_slug: str) -> MissionRun:
    """Start a fresh replay run, leaving earlier attempts, badges, and completion intact."""
    mission = db.session.execute(
        select(Mission).where((Mission.slug == mission_slug) | (Mission.room_number == mission_slug))
    ).scalar_one_or_none()

    if not mission:
        raise ValueError(f"Mission '{mission_slug}' not found")

    scenario = db.session.execute(
        select(Scenario).where(Scenario.mission_id == mission.id, Scenario.is_active.is_(True))
    ).scalar_one_or_none()

    if not scenario:
        raise ValueError(f"No active scenario found for mission '{mission_slug}'")

    # Enforce mission prerequisites
    from app.models.mission import MissionPrerequisite
    prereqs = db.session.execute(
        select(MissionPrerequisite).where(MissionPrerequisite.mission_id == mission.id)
    ).scalars().all()

    if prereqs:
        completed_ids = set(
            db.session.execute(
                select(MissionProgress.mission_id).where(
                    MissionProgress.session_id == session.id,
                    MissionProgress.status == "completed",
                )
            ).scalars().all()
        )
        for p in prereqs:
            if p.prerequisite_mission_id not in completed_ids:
                raise PermissionError(f"Prerequisite mission {p.prerequisite_mission_id} not completed for session {session.id}")

    # Mark any prior in_progress run as abandoned
    prior_runs = db.session.execute(
        select(MissionRun).where(
            MissionRun.session_id == session.id,
            MissionRun.mission_id == mission.id,
            MissionRun.status == "in_progress",
        )
    ).scalars().all()
    for r in prior_runs:
        r.status = "abandoned"

    first_activity = db.session.execute(
        select(Activity).where(
            Activity.scenario_id == scenario.id,
            Activity.is_active.is_(True),
        ).order_by(Activity.display_order.asc())
    ).scalars().first()

    now = datetime.now(timezone.utc)
    replay_run = MissionRun(
        session_id=session.id,
        mission_id=mission.id,
        scenario_id=scenario.id,
        status="in_progress",
        current_activity_id=first_activity.id if first_activity else None,
        patient_state_json=scenario.initial_state_json,
        state_revision=1,
        started_at=now,
    )
    db.session.add(replay_run)
    db.session.commit()
    return replay_run


def submit_activity(
    run_id: int,
    activity_id: int,
    payload: dict[str, Any],
    idempotency_key: str | None = None,
    expected_revision: int | None = None,
) -> dict[str, Any]:
    """Atomically evaluate activity, update patient state, advance run progress, and award badges.

    Guarantees all state changes occur in a single database transaction.
    """
    try:
        run = db.session.get(MissionRun, run_id)
        if not run:
            return {"error": {"code": "run_not_found", "message": "Mission run not found."}}

        if run.status != "in_progress":
            return {"error": {"code": "run_completed", "message": "This mission run has already ended."}}

        # Check idempotency key
        if idempotency_key:
            existing_attempt = db.session.execute(
                select(ActivityAttempt).where(
                    ActivityAttempt.mission_run_id == run.id,
                    ActivityAttempt.activity_id == activity_id,
                    ActivityAttempt.idempotency_key == idempotency_key,
                )
            ).scalar_one_or_none()

            if existing_attempt:
                logger.info("Idempotent submission detected for key %s", idempotency_key)
                return {
                    "is_idempotent": True,
                    "result_type": existing_attempt.result_type,
                    "patient_state": run.patient_state_json,
                    "revision": run.state_revision,
                    "current_activity_id": run.current_activity_id,
                    "is_mission_completed": run.status == "completed",
                }

        # Check state revision for stale tab conflict
        if expected_revision is not None and expected_revision != run.state_revision:
            return {
                "error": {
                    "code": "stale_state",
                    "message": "Your browser view is out of date. Reload to continue.",
                    "current_revision": run.state_revision,
                }
            }

        activity = db.session.get(Activity, activity_id)
        if not activity or activity.scenario_id != run.scenario_id:
            return {"error": {"code": "invalid_activity", "message": "Activity does not belong to this scenario."}}

        if run.current_activity_id != activity.id:
            return {
                "error": {
                    "code": "out_of_order",
                    "message": "Please complete previous activities first.",
                    "current_activity_id": run.current_activity_id,
                }
            }

        # Evaluate student submission
        eval_result = evaluate_activity(activity, payload)

        # Count prior attempts for this activity in this run
        prior_attempts = db.session.scalar(
            select(db.func.count(ActivityAttempt.id)).where(
                ActivityAttempt.mission_run_id == run.id,
                ActivityAttempt.activity_id == activity.id,
            )
        ) or 0
        attempt_number = prior_attempts + 1

        # Record attempt
        attempt = ActivityAttempt(
            mission_run_id=run.id,
            activity_id=activity.id,
            attempt_number=attempt_number,
            response_json=payload,
            result_type=eval_result["result_type"],
            idempotency_key=idempotency_key,
        )
        db.session.add(attempt)

        # Apply patient effect if defined
        patient_events: list[str] = []
        if eval_result.get("patient_effect"):
            new_state, events = apply_patient_effects(run.patient_state_json, eval_result["patient_effect"])
            run.patient_state_json = new_state
            patient_events = events

        # Advance state revision
        run.state_revision += 1
        now = datetime.now(timezone.utc)

        is_mission_completed = False
        badge_awarded = None

        if eval_result["success"]:
            # Record activity progress
            existing_prog = db.session.execute(
                select(ActivityProgress).where(
                    ActivityProgress.mission_run_id == run.id,
                    ActivityProgress.activity_id == activity.id,
                )
            ).scalar_one_or_none()

            if not existing_prog:
                prog = ActivityProgress(
                    mission_run_id=run.id,
                    activity_id=activity.id,
                    is_completed=True,
                    completion_evidence_json=eval_result.get("evidence", {}),
                    completed_at=now,
                )
                db.session.add(prog)

            # Find next activity
            next_activity = db.session.execute(
                select(Activity).where(
                    Activity.scenario_id == run.scenario_id,
                    Activity.is_active.is_(True),
                    Activity.display_order > activity.display_order,
                ).order_by(Activity.display_order.asc())
            ).scalars().first()

            if next_activity:
                run.current_activity_id = next_activity.id
            else:
                # Mission completed!
                run.current_activity_id = None
                run.status = "completed"
                run.completed_at = now
                is_mission_completed = True

                # Update lasting MissionProgress
                mission_prog = db.session.execute(
                    select(MissionProgress).where(
                        MissionProgress.session_id == run.session_id,
                        MissionProgress.mission_id == run.mission_id,
                    )
                ).scalar_one_or_none()

                if mission_prog:
                    mission_prog.status = "completed"
                    mission_prog.completed_at = now

                # Award badge if defined for this mission
                badge = db.session.execute(
                    select(Badge).where(Badge.mission_id == run.mission_id)
                ).scalar_one_or_none()

                if badge:
                    badge_file_map = {
                        "oxygen": "oxygen-guardian.svg",
                        "airway": "airway-explorer.svg",
                        "nebulizer": "nebulizer-navigator.svg",
                        "rescue": "respiratory-ready.svg",
                    }
                    badge_img_name = badge_file_map.get(badge.icon, "airway-explorer.svg")
                    badge_info = {
                        "name": badge.name,
                        "description": badge.description,
                        "icon": badge.icon,
                        "image_url": f"/static/images/badges/{badge_img_name}",
                    }

                    existing_session_badge = db.session.execute(
                        select(SessionBadge).where(
                            SessionBadge.session_id == run.session_id,
                            SessionBadge.badge_id == badge.id,
                        )
                    ).scalar_one_or_none()

                    if not existing_session_badge:
                        awarded_badge = SessionBadge(
                            session_id=run.session_id,
                            badge_id=badge.id,
                            mission_run_id=run.id,
                            awarded_at=now,
                        )
                        db.session.add(awarded_badge)
                    badge_awarded = badge_info

        db.session.commit()

        return {
            "success": eval_result["success"],
            "result_type": eval_result["result_type"],
            "title": eval_result["title"],
            "message": eval_result["message"],
            "clinical_rationale": eval_result["clinical_rationale"],
            "hint": eval_result.get("hint"),
            "patient_state": run.patient_state_json,
            "patient_events": patient_events,
            "revision": run.state_revision,
            "current_activity_id": run.current_activity_id,
            "is_mission_completed": is_mission_completed,
            "badge_awarded": badge_awarded,
        }

    except Exception as exc:
        db.session.rollback()
        logger.exception("Error processing activity submission: %s", exc)
        return {
            "error": {
                "code": "internal_error",
                "message": "An error occurred while evaluating your response. Please try again.",
            }
        }
