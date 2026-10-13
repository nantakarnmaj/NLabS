"""Seed definitions for the four respiratory ward rooms and prerequisites.

Idempotent: inserts missing definitions without overwriting existing customizations or learner data.
"""

from __future__ import annotations

import logging
from sqlalchemy import select
from app.extensions import db
from app.models.mission import Mission, MissionPrerequisite

logger = logging.getLogger(__name__)

INITIAL_ROOMS = [
    {
        "room_number": "501",
        "slug": "clear-the-airway",
        "title": "เคลียร์ทางเดินหายใจ (Clear the Airway)",
        "subtitle": "ภารกิจการดูดเสมหะ (Suctioning Mission)",
        "description": "ทบทวนการประเมิน, การเตรียมสายและเทคนิคปลอดเชื้อ, การควบคุมแรงดูด และการเฝ้าระวังความปลอดภัยขณะดูดเสมหะท่อเจาะคอ",
        "icon": "airway",
        "availability": "preview",
        "display_order": 1,
        "is_active": True,
    },
    {
        "room_number": "502",
        "slug": "support-the-breath",
        "title": "ประคับประคองการหายใจ (Support the Breath)",
        "subtitle": "ภารกิจการให้ออกซิเจนบำบัด (Oxygen Therapy Mission)",
        "description": "จับคู่อาการทางคลินิกกับอุปกรณ์ให้ออกซิเจนที่เหมาะสม อัตราการไหล และข้อควรระวังความปลอดภัยสำหรับผู้ป่วยที่มีภาวะพร่องออกซิเจน",
        "icon": "oxygen",
        "availability": "coming_soon",
        "display_order": 2,
        "is_active": True,
    },
    {
        "room_number": "503",
        "slug": "open-the-airway",
        "title": "ขยายทางเดินหายใจ (Open the Airway)",
        "subtitle": "ภารกิจการพ่นยาขยายหลอดลม (Nebulization Mission)",
        "description": "ตรวจสอบสิทธิ 6 ประการของยา, ประกอบชุดพ่นยา, ปรับอัตราก๊าซ 6–8 L/min, สอนเทคนิคการสูดยา และเฝ้าระวังอาการข้างเคียง",
        "icon": "nebulizer",
        "availability": "coming_soon",
        "display_order": 3,
        "is_active": True,
    },
    {
        "room_number": "504",
        "slug": "respiratory-rescue",
        "title": "กู้ชีพฉุกเฉินระบบหายใจ (Respiratory Rescue)",
        "subtitle": "ภารกิจบูรณาการภาวะวิกฤต (Integrated Emergency Mission)",
        "description": "รับมือและกู้ชีพผู้ป่วยวิกฤตที่มีภาวะทรุดลงเฉียบพลัน จัดลำดับความสำคัญ ดูดเสมหะ พ่นยา และรายงานแพทย์ด้วย SBAR",
        "icon": "rescue",
        "availability": "locked",
        "display_order": 4,
        "is_active": True,
    },
]

# Prerequisites for Room 504: requires 501, 502, 503
PREREQUISITES_SPEC = [
    ("504", "501"),
    ("504", "502"),
    ("504", "503"),
]


def seed_rooms() -> dict[str, int]:
    """Idempotently seed the 4 ward rooms and their prerequisites.

    Returns summary counts of created entities.
    """
    created_missions = 0
    created_prereqs = 0

    # 1. Seed or retrieve missions
    missions_by_room: dict[str, Mission] = {}

    for room_data in INITIAL_ROOMS:
        room_num = room_data["room_number"]
        existing = db.session.execute(
            select(Mission).where(
                (Mission.room_number == room_num) | (Mission.slug == room_data["slug"])
            )
        ).scalar_one_or_none()

        if existing is None:
            mission = Mission(**room_data)
            db.session.add(mission)
            db.session.flush()  # assign id
            missions_by_room[room_num] = mission
            created_missions += 1
            logger.info("Created missing mission Room %s (%s)", room_num, mission.slug)
        else:
            existing.title = room_data["title"]
            existing.subtitle = room_data["subtitle"]
            if not existing.description or "Customized" not in existing.description:
                existing.description = room_data["description"]
            missions_by_room[room_num] = existing
            logger.debug("Updated mission Room %s titles/descriptions to Thai", room_num)

    # 2. Seed prerequisites
    for target_room, req_room in PREREQUISITES_SPEC:
        target_mission = missions_by_room.get(target_room)
        req_mission = missions_by_room.get(req_room)

        if not target_mission or not req_mission:
            logger.warning(
                "Cannot link prerequisite: Room %s or Room %s not found", target_room, req_room
            )
            continue

        existing_prereq = db.session.execute(
            select(MissionPrerequisite).where(
                MissionPrerequisite.mission_id == target_mission.id,
                MissionPrerequisite.prerequisite_mission_id == req_mission.id,
            )
        ).scalar_one_or_none()

        if existing_prereq is None:
            prereq = MissionPrerequisite(
                mission_id=target_mission.id,
                prerequisite_mission_id=req_mission.id,
            )
            db.session.add(prereq)
            created_prereqs += 1
            logger.info(
                "Added prerequisite: Room %s requires Room %s", target_room, req_room
            )

    db.session.commit()
    return {"created_missions": created_missions, "created_prereqs": created_prereqs}
