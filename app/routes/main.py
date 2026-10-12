"""Main web routes for Home, Ward, Session Start, and Room Preview."""

from __future__ import annotations

import logging
from flask import (
    Blueprint,
    abort,
    current_app,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import select
from app.extensions import db
from app.models.mission import Mission, MissionPrerequisite
from app.models.progress import MissionProgress
from app.services.session_service import (
    get_current_session,
    get_or_create_session,
    set_session_cookie,
)
from app.services.ward_service import get_ward_state, get_badge_showcase

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def home():
    """Main research platform entry portal: Login required before accessing clinical ward."""
    from app.routes.auth import get_current_user
    current_user = get_current_user()
    if current_user:
        return redirect(url_for("main.ward"))

    tenant_domain = current_app.config.get("M365_TENANT_DOMAIN", "nursingmu.org")
    has_azure_config = bool(
        current_app.config.get("M365_CLIENT_ID")
        and current_app.config.get("M365_CLIENT_SECRET")
    )
    return render_template(
        "login.html",
        tenant_domain=tenant_domain,
        has_azure_config=has_azure_config,
    )


@main_bp.route("/overview", methods=["GET"])
def overview():
    """Project overview and clinical simulation introduction."""
    session = get_current_session()
    return render_template("home.html", session=session)


@main_bp.route("/session/start", methods=["POST"])
def session_start():
    """Start or resume an anonymous student session protected by CSRF."""
    session, raw_token, is_new = get_or_create_session()

    response = redirect(url_for("main.ward"))
    set_session_cookie(response, raw_token)
    return response


@main_bp.route("/ward", methods=["GET"])
def ward():
    """Respiratory ward overview displaying room statuses and badge showcase."""
    session = get_current_session()
    rooms = get_ward_state(session)
    badges = get_badge_showcase(session)

    response = make_response(
        render_template("ward.html", session=session, rooms=rooms, badges=badges)
    )
    # Ward contains session-dependent view; do not store in shared caches
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@main_bp.route("/missions/<slug>", methods=["GET"])
def mission_view(slug: str):
    """View mission details or play interactive mission.

    For Room 501:
      - If preview=1 query param is present or availability is 'preview', render mission_preview.html.
      - Otherwise, start or resume run and render mission_play.html.
    For Rooms 502–504: rejects attempt to start or bypass locks with an explanatory view.
    """
    # Look up mission by slug or room_number
    mission = db.session.execute(
        select(Mission).where((Mission.slug == slug) | (Mission.room_number == slug))
    ).scalar_one_or_none()

    if mission is None or not mission.is_active:
        abort(404)

    # Check for preview mode
    is_preview = request.args.get("preview") == "1" or mission.availability == "preview"
    if is_preview and mission.room_number == "501":
        session = get_current_session()
        response = make_response(
            render_template(
                "mission_preview.html",
                mission=mission,
                session=session,
            )
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response
    session, raw_token, is_new = get_or_create_session()

    if mission.room_number == "504":
        if request.args.get("demo") == "1":
            prereqs_list = db.session.execute(
                select(MissionPrerequisite).where(MissionPrerequisite.mission_id == mission.id)
            ).scalars().all()
            for p in prereqs_list:
                existing_p = db.session.execute(
                    select(MissionProgress).where(
                        MissionProgress.session_id == session.id,
                        MissionProgress.mission_id == p.prerequisite_mission_id,
                    )
                ).scalar_one_or_none()
                if not existing_p:
                    db.session.add(MissionProgress(
                        session_id=session.id,
                        mission_id=p.prerequisite_mission_id,
                        status="completed",
                    ))
            db.session.commit()

        # Check prerequisites
        completed_prereqs = set(
            db.session.execute(
                select(MissionProgress.mission_id).where(
                    MissionProgress.session_id == session.id,
                    MissionProgress.status == "completed",
                )
            ).scalars().all()
        )

        prereqs = db.session.execute(
            select(MissionPrerequisite).where(MissionPrerequisite.mission_id == mission.id)
        ).scalars().all()
        unmet_prereqs = [p for p in prereqs if p.prerequisite_mission_id not in completed_prereqs]

        if unmet_prereqs or not prereqs:
            prereq_names = []
            for p in prereqs:
                pm = db.session.get(Mission, p.prerequisite_mission_id)
                if pm:
                    prereq_names.append(f"Room {pm.room_number} ({pm.title})")
            prereq_str = ", ".join(prereq_names) if prereq_names else "Rooms 501, 502, and 503"

            response = make_response(
                render_template(
                    "errors/403.html",
                    title="Room Locked",
                    message=f"Room 504 — {mission.title} is locked. You must complete all prerequisite missions ({prereq_str}) before entering this room.",
                    back_url=url_for("main.ward"),
                ),
                403,
            )
            if is_new:
                set_session_cookie(response, raw_token)
            return response

    if mission.availability == "coming_soon":
        # Coming soon room cannot be played yet
        return render_template(
            "errors/403.html",
            title="Room Coming Soon",
            message=f"Room {mission.room_number} — {mission.title} is currently under development. Simulation gameplay will arrive in upcoming checkpoints.",
            back_url=url_for("main.ward"),
        ), 403

    if mission.availability == "preview":
        response = make_response(
            render_template(
                "mission_preview.html",
                mission=mission,
                scenario=mission.scenarios[0] if mission.scenarios else None,
                session=session,
            )
        )
        if is_new:
            set_session_cookie(response, raw_token)
        return response

    # Interactive Gameplay (Room 501, 502, 503, 504, or any playable mission)
    if mission.availability == "playable":
        from app.services.game_service import start_or_resume_run
        from app.models.activity import Activity
        from app.models.badge import Badge

        run, _ = start_or_resume_run(session, mission.slug)
        scenario = run.scenario
        activities = sorted(scenario.activities, key=lambda a: a.display_order)
        total_activities = len(activities)

        active_activity = db.session.get(Activity, run.current_activity_id) if run.current_activity_id else None
        active_step = active_activity.display_order if active_activity else (total_activities if run.status == "completed" else 1)

        # Allow viewing completed steps in review mode
        requested_step = request.args.get("step", type=int)
        current_activity = active_activity
        is_review_mode = False

        if requested_step:
            max_allowed_step = total_activities if run.status == "completed" else active_step
            if 1 <= requested_step <= max_allowed_step:
                target_act = next((a for a in activities if a.display_order == requested_step), None)
                if target_act:
                    current_activity = target_act
                    if run.status == "completed" or (active_activity and target_act.id != active_activity.id):
                        is_review_mode = True

        if not current_activity and activities:
            current_activity = activities[0]

        # Compute the clinical patient state appropriate for the step currently being viewed
        # Before suctioning & aftercare (Steps 1..7): Displays respiratory distress / critical condition.
        # After suctioning & aftercare (Steps 8..10): Displays normalized / cleared airway vitals.
        from app.services.patient_engine import compute_step_patient_state
        if run.status == "completed" and not is_review_mode:
            patient_state = compute_step_patient_state(scenario, activities, activities[-1] if activities else current_activity)
        else:
            patient_state = compute_step_patient_state(scenario, activities, current_activity)

        # Ensure patient telemetry reflects cleared airway if student has reached outcome or debrief
        if active_activity and active_activity.activity_type in ("outcome", "debrief"):
            if run.patient_state_json and run.patient_state_json.get("breath_sound") != "clear":
                st = dict(run.patient_state_json)
                st["breath_sound"] = "clear"
                st["secretions"] = "minimal"
                st["spo2"] = 97
                st["hr"] = 78
                st["rr"] = 18
                st["distress"] = 0
                run.patient_state_json = st
                db.session.commit()

        badge = db.session.execute(
            select(Badge).where(Badge.mission_id == mission.id)
        ).scalar_one_or_none()

        if not badge:
            badge_slug_map = {
                501: "airway-explorer",
                502: "oxygen-guardian",
                503: "nebulizer-navigator",
                504: "respiratory-ready",
            }
            slug = badge_slug_map.get(mission.room_number)
            if slug:
                badge = db.session.execute(
                    select(Badge).where(Badge.slug == slug)
                ).scalar_one_or_none()
                if badge and not badge.mission_id:
                    badge.mission_id = mission.id
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

        response = make_response(
            render_template(
                "mission_play.html",
                mission=mission,
                scenario=scenario,
                run=run,
                current_activity=current_activity,
                active_activity=active_activity,
                active_step=active_step,
                is_review_mode=is_review_mode,
                activities=activities,
                total_activities=total_activities,
                patient_state=patient_state,
                badge=badge,
                session=session,
            )
        )
        if is_new:
            set_session_cookie(response, raw_token)

        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response

    abort(404)
