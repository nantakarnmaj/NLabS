"""Ward service for presenting ward rooms, statuses, prerequisites, and badges."""

from __future__ import annotations

from sqlalchemy import select
from app.extensions import db
from app.models.mission import Mission, MissionPrerequisite
from app.models.progress import MissionProgress
from app.models.session import StudentSession

# Static badge definitions for ward showcase (participation badges)
BADGE_DEFINITIONS = [
    {
        "id": "badge-501",
        "room_number": "501",
        "name": "ผู้พิชิตทางเดินหายใจ (Airway Explorer)",
        "description": "มีส่วนร่วมในการประเมินและดูดเสมหะทางท่อหลอดลมคอแบบปลอดเชื้อ",
        "icon": "airway",
    },
    {
        "id": "badge-502",
        "room_number": "502",
        "name": "ผู้พิทักษ์ออกซิเจน (Oxygen Guardian)",
        "description": "มีส่วนร่วมในการเลือกอุปกรณ์ให้ออกซิเจนและปรับอัตราการไหลอย่างปลอดภัย",
        "icon": "oxygen",
    },
    {
        "id": "badge-503",
        "room_number": "503",
        "name": "ยอดนักพ่นยา (Nebulizer Navigator)",
        "description": "มีส่วนร่วมในการตรวจสอบยาขยายหลอดลมและดูแลชุดพ่นยา",
        "icon": "nebulizer",
    },
    {
        "id": "badge-504",
        "room_number": "504",
        "name": "พร้อมรับมือภาวะวิกฤต (Respiratory Ready)",
        "description": "บูรณาการทักษะการพยาบาลระบบหายใจช่วยชีวิตผู้ป่วยในภาวะวิกฤตฉุกเฉิน",
        "icon": "rescue",
    },
]


def get_ward_state(session: StudentSession | None = None) -> list[dict]:
    """Retrieve all active ward rooms with their computed state and prerequisite info.

    Returns:
        List of dictionaries containing room metadata and display status.
    """
    missions = db.session.execute(
        select(Mission).where(Mission.is_active.is_(True)).order_by(Mission.display_order.asc())
    ).scalars().all()

    # If database has not been seeded yet, auto-seed missions so the ward is never empty
    if not missions:
        try:
            from seed import run_all_seeds
            run_all_seeds()
            missions = db.session.execute(
                select(Mission).where(Mission.is_active.is_(True)).order_by(Mission.display_order.asc())
            ).scalars().all()
        except Exception:
            pass

    # If session is provided, find any completed missions for this session
    completed_mission_ids: set[int] = set()
    if session:
        completed = db.session.execute(
            select(MissionProgress.mission_id).where(
                MissionProgress.session_id == session.id,
                MissionProgress.status == "completed",
            )
        ).scalars().all()
        completed_mission_ids = set(completed)

    ward_rooms = []
    for mission in missions:
        # Check prerequisites
        prereqs = db.session.execute(
            select(MissionPrerequisite).where(MissionPrerequisite.mission_id == mission.id)
        ).scalars().all()

        prereq_rooms = []
        is_prereq_satisfied = True
        for p in prereqs:
            prereq_mission = db.session.get(Mission, p.prerequisite_mission_id)
            if prereq_mission:
                prereq_rooms.append(f"Room {prereq_mission.room_number}")
                if prereq_mission.id not in completed_mission_ids:
                    is_prereq_satisfied = False

        # In Checkpoint E:
        # Rooms 501, 502, 503: Playable / In Progress / Completed
        # Room 504: Playable if all prerequisites (501, 502, 503) are satisfied; otherwise Locked
        if mission.room_number in ("501", "502", "503") and mission.availability == "playable":
            prog = None
            if session:
                prog = db.session.execute(
                    select(MissionProgress).where(
                        MissionProgress.session_id == session.id,
                        MissionProgress.mission_id == mission.id,
                    )
                ).scalar_one_or_none()

            can_open = True
            action_url = f"/missions/{mission.slug}"

            if prog and prog.status == "completed":
                display_status = "completed"
                status_label = "สำเร็จแล้ว (Completed)"
                status_color = "emerald"
                action_label = "ทบทวน / เล่นซ้ำ (Review / Replay mission)"
                notice = "ภารกิจสำเร็จแล้ว! คุณสามารถทบทวนหรือเล่นซ้ำเพื่อฝึกฝนเพิ่มเติมได้ตลอดเวลา"
            elif prog and prog.status == "in_progress":
                display_status = "in_progress"
                status_label = "กำลังเรียนรู้ (In Progress)"
                status_color = "cyan"
                action_label = "เรียนรู้ต่อ (Resume)"
                notice = "กำลังทำภารกิจ สามารถเรียนรู้ต่อจากขั้นตอนล่าสุดของคุณได้"
            else:
                display_status = "ready"
                status_label = "พร้อมเรียนรู้ (Ready)"
                status_color = "emerald"
                action_label = "เริ่มทำภารกิจ (Start mission)"
                notice = "พร้อมสำหรับสถานการณ์จำลองคลินิก"
        elif mission.room_number == "504":
            if is_prereq_satisfied and mission.availability == "playable":
                prog = None
                if session:
                    prog = db.session.execute(
                        select(MissionProgress).where(
                            MissionProgress.session_id == session.id,
                            MissionProgress.mission_id == mission.id,
                        )
                    ).scalar_one_or_none()

                can_open = True
                action_url = f"/missions/{mission.slug}"

                if prog and prog.status == "completed":
                    display_status = "completed"
                    status_label = "สำเร็จแล้ว (Completed)"
                    status_color = "emerald"
                    action_label = "ทบทวน / เล่นซ้ำ (Review / Replay mission)"
                    notice = "ภารกิจสำเร็จแล้ว! คุณสามารถทบทวนหรือเล่นซ้ำเพื่อฝึกฝนเพิ่มเติมได้ตลอดเวลา"
                elif prog and prog.status == "in_progress":
                    display_status = "in_progress"
                    status_label = "กำลังเรียนรู้ (In Progress)"
                    status_color = "cyan"
                    action_label = "เรียนรู้ต่อ (Resume)"
                    notice = "กำลังทำภารกิจ สามารถเรียนรู้ต่อจากขั้นตอนล่าสุดของคุณได้"
                else:
                    display_status = "ready"
                    status_label = "พร้อมเรียนรู้ (Ready)"
                    status_color = "emerald"
                    action_label = "เริ่มทำภารกิจ (Start mission)"
                    notice = "พร้อมสำหรับสถานการณ์จำลองคลินิกฉุกเฉินบูรณาการ (Integrated clinical simulation ready to play.)"
            else:
                display_status = "locked"
                status_label = "ล็อกอยู่ (Locked)"
                status_color = "slate"
                action_label = None
                action_url = None
                can_open = False
                prereq_str = ", ".join(prereq_rooms) if prereq_rooms else "Rooms 501, 502, and 503"
                notice = f"ต้องทำภารกิจ {prereq_str} ให้สำเร็จก่อนเข้า (Requires completion of {prereq_str} before entry)"
        elif mission.room_number == "501" and mission.availability == "preview":
            can_open = True
            action_url = f"/missions/{mission.slug}"
            display_status = "ready"
            status_label = "พร้อมเรียนรู้ (Ready)"
            status_color = "emerald"
            action_label = "ดูตัวอย่างภารกิจ (View mission preview)"
            notice = "Mission preview — gameplay coming in Checkpoint B"
        elif mission.room_number in ("502", "503") and mission.availability == "coming_soon":
            display_status = "coming_soon"
            status_label = "เร็วๆ นี้ (Coming Soon)"
            status_color = "amber"
            action_label = None
            action_url = None
            can_open = False
            notice = "ห้องกำลังพัฒนา (Coming Soon — under development)"
        else:
            display_status = mission.availability
            status_label = mission.availability.replace("_", " ").title()
            status_color = "slate"
            action_label = None
            action_url = None
            can_open = False
            notice = ""

        ward_rooms.append({
            "mission": mission,
            "room_number": mission.room_number,
            "title": mission.title,
            "subtitle": mission.subtitle,
            "description": mission.description,
            "display_status": display_status,
            "status_label": status_label,
            "status_color": status_color,
            "action_label": action_label,
            "action_url": action_url,
            "can_open": can_open,
            "notice": notice,
            "prerequisites": prereq_rooms,
        })

    return ward_rooms


def get_badge_showcase(session: StudentSession | None = None) -> list[dict]:
    """Retrieve badge definitions for ward display, showing earned status for the current session."""
    awarded_badge_slugs: set[str] = set()
    if session:
        from app.models.badge import SessionBadge, Badge
        session_badges = db.session.execute(
            select(Badge.slug).join(SessionBadge, SessionBadge.badge_id == Badge.id).where(
                SessionBadge.session_id == session.id
            )
        ).scalars().all()
        awarded_badge_slugs = set(session_badges)

    result = []
    for badge in BADGE_DEFINITIONS:
        # Check mapping for participation badges
        is_unlocked = False
        if badge["id"] == "badge-501" and "airway-explorer" in awarded_badge_slugs:
            is_unlocked = True
        elif badge["id"] == "badge-502" and "oxygen-guardian" in awarded_badge_slugs:
            is_unlocked = True
        elif badge["id"] == "badge-503" and "nebulizer-navigator" in awarded_badge_slugs:
            is_unlocked = True
        elif badge["id"] == "badge-504" and "respiratory-ready" in awarded_badge_slugs:
            is_unlocked = True

        result.append({
            **badge,
            "is_unlocked": is_unlocked,
            "status_text": "Unlocked & Earned!" if is_unlocked else "Participate to discover",
        })

    return result
