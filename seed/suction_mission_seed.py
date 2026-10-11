"""Complete seed content for Room 501: Clear the Airway (Suctioning Mission).

Idempotent: inserts or updates scenario, 10 activities, options, procedure steps,
feedback rules, and badge without disturbing student progress.
"""

from __future__ import annotations

import logging
from sqlalchemy import select
from app.extensions import db
from app.models.mission import Mission
from app.models.scenario import Scenario
from app.models.activity import Activity, ActivityOption, ProcedureStep, Feedback
from app.models.badge import Badge

logger = logging.getLogger(__name__)


def seed_suction_mission() -> dict[str, int]:
    """Seed Room 501 scenario, activities, options, steps, feedback, and badge."""
    mission = db.session.execute(
        select(Mission).where((Mission.room_number == "501") | (Mission.slug == "clear-the-airway"))
    ).scalar_one_or_none()

    if not mission:
        logger.warning("Room 501 mission not found. Run seed_rooms() first.")
        return {"scenario": 0, "activities": 0}

    # Update Room 501 availability from 'preview' to 'playable'
    mission.availability = "playable"

    # 1. Create or update Scenario
    scenario = db.session.execute(
        select(Scenario).where(Scenario.mission_id == mission.id)
    ).scalar_one_or_none()

    initial_vitals = {
        "spo2": 91,
        "rr": 26,
        "hr": 96,
        "distress": 3,
        "secretions": "copious",
        "breath_sound": "coarse_rhonchi",
        "consciousness": "restless",
    }

    if not scenario:
        scenario = Scenario(
            mission_id=mission.id,
            title="การดูดเสมหะท่อช่วยหายใจสำหรับคุณสมชาย (Endotracheal Airway Clearance for Somchai)",
            patient_name="นายสมชาย (Mr. Somchai)",
            patient_age=68,
            patient_gender="ชาย",
            clinical_summary=(
                "นายสมชาย อายุ 68 ปี วันที่ 2 หลังผ่าตัดช่องท้อง ใส่ท่อช่วยหายใจเบอร์ 7.5 "
                "ไอสู้เครื่องช่วยหายใจและได้ยินเสียงเสมหะเดือดในทางเดินหายใจ "
                "จอมอนิเตอร์แสดงค่า SpO2 ลดลงเหลือ 91% หายใจ 26 ครั้ง/นาที ชีพจร 96 ครั้ง/นาที ฟังปอดได้ยิน coarse rhonchi"
            ),
            initial_state_json=initial_vitals,
            difficulty="intermediate",
            approval_status="approved",
            version=1,
            is_active=True,
        )
        db.session.add(scenario)
        db.session.flush()
        logger.info("Created Scenario for Room 501 (id=%s)", scenario.id)
    else:
        scenario.title = "การดูดเสมหะท่อช่วยหายใจสำหรับคุณสมชาย (Endotracheal Airway Clearance for Somchai)"
        scenario.patient_name = "นายสมชาย (Mr. Somchai)"
        scenario.patient_age = 68
        scenario.patient_gender = "ชาย"
        scenario.clinical_summary = (
            "นายสมชาย อายุ 68 ปี วันที่ 2 หลังผ่าตัดช่องท้อง ใส่ท่อช่วยหายใจเบอร์ 7.5 "
            "ไอสู้เครื่องช่วยหายใจและได้ยินเสียงเสมหะเดือดในทางเดินหายใจ "
            "จอมอนิเตอร์แสดงค่า SpO2 ลดลงเหลือ 91% หายใจ 26 ครั้ง/นาที ชีพจร 96 ครั้ง/นาที ฟังปอดได้ยิน coarse rhonchi"
        )
        scenario.initial_state_json = initial_vitals
        scenario.approval_status = "approved"

    # 2. Define the 10 Activities
    ACTIVITIES_DATA = [
        # Activity 1: Intro
        {
            "display_order": 1,
            "activity_type": "intro",
            "title": "พบคุณสมชาย (Meet Mr. Somchai) & ข้อมูลผู้ป่วย",
            "instruction": "ทบทวนข้อมูลผู้ป่วย ภาวะทางเดินหายใจประดิษฐ์ และสัญญาณชีพระดับฐานบนจอมอนิเตอร์ข้างเตียง",
            "content_json": {
                "patient_name": "นายสมชาย (Mr. Somchai)",
                "age": 68,
                "history": "วันที่ 2 หลังผ่าตัดช่องท้อง (Post-Op Laparotomy) ใช้เครื่องช่วยหายใจ",
                "airway": "ท่อช่วยหายใจทางปาก (Oral ETT) เบอร์ 7.5 มม. ลึก 22 ซม. ที่มุมปาก",
                "cues_preview": "ได้ยินเสียงเสมหะเดือดในวงจรเครื่องช่วยหายใจ หายใจเร็ว กระสับกระส่าย",
            },
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ทบทวนข้อมูลผู้ป่วยเรียบร้อย (Clinical Briefing Reviewed)",
                    "message": "คุณได้ทบทวนข้อมูลพื้นฐานของคุณสมชายเรียบร้อยแล้ว ดำเนินการต่อเพื่อประเมินสัญญาณและข้อบ่งชี้ทางคลินิก",
                    "clinical_rationale": "การประเมินอาการและสัญญาณชีพอย่างละเอียดช่วยสร้างข้อมูลพื้นฐานและยืนยันข้อบ่งชี้ก่อนทำหัตถการรุกล้ำ",
                }
            ],
        },
        # Activity 2: Clinical Cues
        {
            "display_order": 2,
            "activity_type": "clinical_cues",
            "title": "สัญญาณทางคลินิก: ประเมินข้อบ่งชี้การดูดเสมหะ (Clinical Cues)",
            "instruction": "เลือกข้อค้นพบจากการตรวจประเมินทางคลินิกทั้งหมดที่บ่งชี้ว่าจำเป็นต้องดูดเสมหะ หลีกเลี่ยงการทำเป็นกิจวัตรที่ไม่มีข้อบ่งชี้",
            "options": [
                {"option_key": "audible_gurgling", "label": "มองเห็นเสมหะบริเวณข้อต่อ ETT", "is_correct": True, "display_order": 1},
                {"option_key": "rhonchi", "label": "ฟังปอดได้ยินเสียง coarse rhonchi ทั้งสองข้าง", "is_correct": True, "display_order": 2},
                {"option_key": "desaturation", "label": "ค่าความอิ่มตัวของออกซิเจนลดลง (SpO2 ลดลงเหลือ 91%) ร่วมกับมีอาการกระสับกระส่าย", "is_correct": True, "display_order": 3},
                {"option_key": "scheduled_q2h", "label": "ดูดเสมหะตามรอบเวลาที่กำหนดทุก 2 ชั่วโมงเป็นกิจวัตรโดยไม่มีอาการบ่งชี้", "is_correct": False, "display_order": 4},
                {"option_key": "prevent_fever", "label": "ดูดเสมหะเป็นประจำเพื่อป้องกันไข้หลังผ่าตัด", "is_correct": False, "display_order": 5},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "การประเมินทางคลินิกถูกต้อง (Accurate Clinical Assessment)",
                    "message": "คุณระบุข้อบ่งชี้ทางคลินิกจากการประเมินทางเดินหายใจได้อย่างถูกต้อง แทนที่จะทำตามรอบเวลาเป็นกิจวัตร",
                    "clinical_rationale": "แนวปฏิบัติตามหลักฐานเชิงประจักษ์กำหนดให้ดูดเสมหะเมื่อมีข้อบ่งชี้ทางคลินิกเท่านั้น การดูดเสมหะตามรอบเวลาโดยไม่จำเป็นจะทำลายเยื่อบุหลอดลม ทำให้หลอดลมหดเกร็ง และเกิดภาวะขาดออกซิเจน",
                },
                {
                    "trigger_type": "on_selection",
                    "trigger_key": "scheduled_q2h",
                    "feedback_type": "caution",
                    "title": "อันตรายจากการดูดเสมหะตามรอบเวลา (Routine Suctioning Hazard)",
                    "message": "การดูดเสมหะตามตารางเวลาเป็นประจำล้าสมัยและก่ออันตราย ควรดูดเสมหะเมื่อมีอาการทางคลินิกบ่งชี้เท่านั้น",
                    "clinical_rationale": "การใส่สายดูดเสมหะโดยไม่จำเป็นจะครูดทำลายเยื่อบุหลอดลมและเพิ่มความเสี่ยงต่อการเกิดปอดอักเสบจากการใช้เครื่องช่วยหายใจ (VAP)",
                    "hint": "เลือกเฉพาะข้อค้นพบที่แสดงถึงการอุดกั้นของเสมหะในทางเดินหายใจหรือการแลกเปลี่ยนออกซิเจนลดลง",
                },
            ],
        },
        # Activity 3: Gear Up (Equipment Select)
        {
            "display_order": 3,
            "activity_type": "equipment_select",
            "title": "เตรียมอุปกรณ์ปลอดเชื้อและการตั้งค่าแรงดันดูด (Gear Up)",
            "instruction": "เลือกรายการอุปกรณ์ปลอดเชื้อ อุปกรณ์ป้องกันส่วนบุคคล (PPE) และการตั้งค่าแรงดันดูดสุญญากาศที่ปลอดภัยสำหรับผู้ใหญ่",
            "options": [
                {"option_key": "sterile_catheter", "label": "สายดูดเสมหะปลอดเชื้อ (ขนาด 12 Fr — เส้นผ่านศูนย์กลางภายนอกไม่เกินครึ่งหนึ่งของเส้นผ่านศูนย์กลางภายในท่อ ETT)", "is_correct": True, "display_order": 1},
                {"option_key": "sterile_gloves", "label": "ถุงมือปลอดเชื้อ (Sterile gloves) สำหรับเทคนิคการดูดเสมหะระบบเปิด", "is_correct": True, "display_order": 2},
                {"option_key": "vacuum_100_120", "label": "ปรับแรงดันเครื่องดูดเสมหะที่ 100–120 mmHg สำหรับผู้ใหญ่", "is_correct": True, "display_order": 3},
                {"option_key": "sterile_saline", "label": "ภาชนะใส่น้ำเกลือปลอดเชื้อ (Sterile normal saline) สำหรับล้างสายดูดเสมหะ", "is_correct": True, "display_order": 4},
                {"option_key": "face_shield", "label": "อุปกรณ์ป้องกันส่วนบุคคล (PPE): หน้ากากพร้อมกระบังหน้า (Face shield) หรือแว่นป้องกัน", "is_correct": True, "display_order": 5},
                {"option_key": "clean_gloves_only", "label": "ถุงมือสะอาดธรรมดาที่ไม่ปลอดเชื้อสำหรับการดูดเสมหะระบบเปิด", "is_correct": False, "display_order": 6},
                {"option_key": "vacuum_200", "label": "ตั้งแรงดันเครื่องดูดเสมหะสูงถึง 200 mmHg", "is_correct": False, "display_order": 7},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ตรวจสอบอุปกรณ์และความปลอดภัยเรียบร้อย (Equipment & Safety Verified)",
                    "message": "อุปกรณ์ปลอดเชื้อ อุปกรณ์ PPE และแรงดันสุญญากาศที่ปลอดภัย (100–120 mmHg) พร้อมใช้งานแล้ว",
                    "clinical_rationale": "การเลือกขนาดสายดูดเสมหะที่เหมาะสม (≤ 1/2 ของขนาด ETT) ป้องกันการอุดตันทางเดินหายใจอย่างสมบูรณ์ขณะดูดเสมหะ",
                },
                {
                    "trigger_type": "on_selection",
                    "trigger_key": "vacuum_200",
                    "feedback_type": "critical",
                    "title": "อันตรายจากแรงดันสุญญากาศสูงเกินไป (Dangerous Negative Pressure)",
                    "message": "แรงดันสุญญากาศ 200 mmHg สูงเกินไปและอันตรายมากสำหรับผู้ใหญ่",
                    "clinical_rationale": "แรงดันที่สูงเกินไปจะดูดดึงเยื่อบุหลอดลมเข้าไปในรูข้างสายดูด ทำให้เลือดออกและเกิดปอดแฟบ (atelectasis)",
                    "hint": "แรงดันดูดเสมหะในผู้ใหญ่ต้องควบคุมให้อยู่ระหว่าง 100–120 mmHg อย่างเคร่งครัด",
                },
            ],
        },
        # Activity 4: Safety Check
        {
            "display_order": 4,
            "activity_type": "safety_check",
            "title": "รายการตรวจสอบความปลอดภัยก่อนทำหัตถการ (Pre-Procedure Safety Checklist)",
            "instruction": "ยืนยันการปฏิบัติเพื่อความปลอดภัยที่จำเป็นก่อนดูดเสมหะเพื่อลดความเสี่ยงต่อภาวะพร่องออกซิเจน",
            "options": [
                {"option_key": "pre_oxygenate", "label": "ให้ออกซิเจนความเข้มข้นสูง (Hyperoxygenate 100% O2) อย่างน้อย 30–60 วินาทีก่อนทำหัตถการ", "is_correct": True, "display_order": 1},
                {"option_key": "semi_fowler", "label": "จัดผู้ป่วยนอนท่าศีรษะสูง Semi-Fowler's (30–45 องศา) หากไม่มีข้อห้าม", "is_correct": True, "display_order": 2},
                {"option_key": "monitor_vitals", "label": "ติดเครื่องวัดออกซิเจนปลายนิ้ว (Pulse Oximeter) ต่อเนื่องและเปิดเสียงเตือนภัย", "is_correct": True, "display_order": 3},
                {"option_key": "routine_saline_bolus", "label": "หยดน้ำเกลือปลอดเชื้อ 5 มล. เข้าท่อ ETT โดยตรงเป็นกิจวัตรเพื่อละลายเสมหะ", "is_correct": False, "display_order": 4},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ยืนยันความปลอดภัยก่อนดูดเสมหะเรียบร้อย (Pre-Suction Safety Confirmed)",
                    "message": "การให้ออกซิเจนล่วงหน้าและการจัดท่าช่วยเพิ่มความจุปอดสำรอง (FRC) และป้องกันภาวะออกซิเจนตก",
                    "clinical_rationale": "การให้ 100% O2 ก่อนดูดเสมหะเป็นวิธีที่มีประสิทธิภาพสูงสุดในการป้องกันภาวะขาดออกซิเจนจากการดูดเสมหะ",
                    "patient_effect_json": {"spo2_delta": +2},
                },
                {
                    "trigger_type": "on_selection",
                    "trigger_key": "routine_saline_bolus",
                    "feedback_type": "caution",
                    "title": "ไม่แนะนำให้หยดน้ำเกลือเข้าท่อช่วยหายใจเป็นกิจวัตร (Routine Saline Lavage Discouraged)",
                    "message": "แนวปฏิบัติปัจจุบันไม่แนะนำให้หยดน้ำเกลือลงในท่อช่วยหายใจเป็นกิจวัตร",
                    "clinical_rationale": "น้ำเกลือไม่ช่วยละลายเสมหะอย่างแท้จริง แต่จะชะล้างคราบจุลชีพ (biofilm) ลงสู่ปอดส่วนลึก เพิ่มความเสี่ยงปอดอักเสบ",
                    "hint": "เน้นการให้ออกซิเจนล่วงหน้าและการจัดท่าผู้ป่วย หลีกเลี่ยงการหยดน้ำเกลือลงท่อช่วยหายใจ",
                },
            ],
        },
        # Activity 5: Sequence (Put It in Order)
        {
            "display_order": 5,
            "activity_type": "sequence",
            "title": "จัดลำดับขั้นตอนการดูดเสมหะให้ถูกต้อง (Put It in Order)",
            "instruction": "เรียงลำดับขั้นตอนการดูดเสมหะจากขั้นแรกไปขั้นสุดท้าย โดยการลากวางหรือใช้ปุ่ม เลื่อนขึ้น / เลื่อนลง",
            "steps": [
                {"step_key": "step_preox", "step_text": "ให้ออกซิเจน 100% O2 แก่ผู้ป่วยล่วงหน้าเป็นเวลา 30–60 วินาที", "correct_order": 1, "rationale": "ต้องให้ออกซิเจนล่วงหน้าเสมอก่อนสอดสายดูดเสมหะ", "critical_step": True},
                {"step_key": "step_don_sterile", "step_text": "สวมถุงมือปลอดเชื้อและต่อสายดูดเสมหะเข้ากับท่อยางโดยใช้มือข้างที่ไม่ถนัด", "correct_order": 2, "rationale": "รักษามือข้างที่ถนัดให้ปลอดเชื้ออย่างเคร่งครัด", "critical_step": True},
                {"step_key": "step_insert_no_suction", "step_text": "ค่อยๆ สอดสายดูดเสมหะเข้าท่อ ETT โดยไม่เปิดแรงดันดูด จนกระทั่งรู้สึกถึงแรงต้านหรือผู้ป่วยไอ แล้วถอยสายออก 1 ซม.", "correct_order": 3, "rationale": "การดูดเสมหะขณะสอดสายจะฉีกขาดเนื้อเยื่อและทำให้ออกซิเจนลดฮวบ", "critical_step": True},
                {"step_key": "step_suction_withdraw", "step_text": "กดเปิดแรงดันดูดเป็นระยะ (Intermittent) พร้อมหมุนสายและค่อยๆ ดึงสายออก (ใช้เวลารวมไม่เกิน 10–15 วินาที)", "correct_order": 4, "rationale": "การดูดต่อเนื่องหรือนานเกินไปทำให้ปอดแฟบและออกซิเจนลดลงรุนแรง", "critical_step": True},
                {"step_key": "step_post_oxygenate", "step_text": "ต่อเครื่องช่วยหายใจ/แหล่งออกซิเจนกลับทันทีและให้ออกซิเจน 100% เพื่อให้ผู้ป่วยฟื้นตัวก่อนทำรอบถัดไป", "correct_order": 5, "rationale": "การให้ออกซิเจนชดเชยช่วยคืนค่าออกซิเจนในเลือดและทำให้หัวใจเต้นคงที่", "critical_step": True},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ลำดับขั้นตอนหัตถการถูกต้องสมบูรณ์ (Flawless Procedural Sequence)",
                    "message": "คุณจัดลำดับขั้นตอนการดูดเสมหะได้อย่างถูกต้องตามหลักคลินิก รักษาเทคนิคปลอดเชื้อและระดับออกซิเจนของผู้ป่วยได้ดีเยี่ยม",
                    "clinical_rationale": "การให้ออกซิเจนล่วงหน้า สอดสายโดยไม่ดูด ถอยสายออกเป็นจังหวะไม่เกิน 15 วินาที และให้ออกซิเจนชดเชย ช่วยขจัดเสมหะได้สูงสุดโดยลดภาวะขาดออกซิเจน",
                    "patient_effect_json": {"secretions_set": "moderate"},
                },
                {
                    "trigger_type": "on_mistake",
                    "title": "ลำดับขั้นตอนต้องปรับปรุง (Sequence Needs Adjustment)",
                    "message": "บางขั้นตอนไม่ถูกต้องตามลำดับหรืออาจส่งผลต่อความปลอดภัยของผู้ป่วย",
                    "clinical_rationale": "ข้อควรจำ: ให้ออกซิเจนล่วงหน้าเสมอก่อนสอดสาย และห้ามดูดเสมหะขณะสอดสายเด็ดขาด",
                    "hint": "ตรวจสอบว่าสวมถุงมือปลอดเชื้อและให้ออกซิเจนล่วงหน้าก่อนสอดสายดูดเสมหะหรือไม่",
                },
            ],
        },
        # Activity 6: Critical Decision
        {
            "display_order": 6,
            "activity_type": "decision",
            "title": "การตัดสินใจสำคัญ: จังหวะการเปิดแรงดันดูดเสมหะ (Critical Decision)",
            "instruction": "เมื่อสอดสายดูดเสมหะถึงระดับความลึกที่กำหนดแล้ว ควรเปิดแรงดันสุญญากาศดูดเสมหะเมื่อใดและอย่างไร?",
            "options": [
                {"option_key": "only_on_withdraw", "label": "เปิดแรงดันดูดเป็นระยะเฉพาะขณะค่อยๆ หมุนและดึงสายออกเท่านั้น (ใช้เวลารวม ≤ 10–15 วินาที)", "is_correct": True, "display_order": 1, "description": "การดูดเฉพาะตอนดึงสายออกช่วยปกป้องผนังหลอดลมจากการบาดเจ็บ"},
                {"option_key": "during_insertion", "label": "เปิดแรงดันดูดตลอดเวลาอย่างต่อเนื่องทั้งตอนดันสายเข้าและตอนดึงสายออก", "is_correct": False, "display_order": 2, "description": "การดูดขณะดันสายเข้าจะดูดเอาออกซิเจนออกจากปอดอย่างรวดเร็วและทำลายเยื่อบุหลอดลม"},
                {"option_key": "vigorous_pumping", "label": "กระตุกและกระทุ้งสายดูดเสมหะขึ้นลงอย่างรุนแรงหลายๆ ครั้งบริเวณ Carina", "is_correct": False, "display_order": 3, "description": "ทำให้เกิดแผลถลอกและการกระตุ้น Vagus nerve รุนแรง"},
            ],
            "feedback": [
                {
                    "trigger_key": "only_on_withdraw",
                    "feedback_type": "positive",
                    "title": "ปฏิบัติเทคนิคได้อย่างปลอดภัย (Safe Technique Executed)",
                    "message": "การดูดเสมหะเฉพาะตอนหมุนและดึงสายออกช่วยป้องกันการบาดเจ็บต่อเยื่อบุทางเดินหายใจ",
                    "clinical_rationale": "การหมุนสายเป็นระยะช่วยป้องกันไม่ให้รูข้างสายดูดดูดติดกับผนังหลอดลม",
                    "patient_effect_json": {"distress_delta": -1},
                },
                {
                    "trigger_key": "during_insertion",
                    "feedback_type": "critical",
                    "title": "อันตรายจากการบาดเจ็บต่อทางเดินหายใจ (Airway Trauma Hazard)",
                    "message": "การดูดเสมหะขณะสอดสายจะครูดทำลายเยื่อบุหลอดลมและดูดเอาออกซิเจนออกจากปอดอย่างรวดเร็ว",
                    "clinical_rationale": "ต้องสอดสายดูดเสมหะโดยเปิดรูระบายความดันไว้เสมอ (ไม่ดูด)",
                    "hint": "เปิดแรงดันดูดเสมหะเฉพาะตอนดึงสายออกเท่านั้น",
                },
                {
                    "trigger_key": "vigorous_pumping",
                    "feedback_type": "critical",
                    "title": "การบาดเจ็บต่อ Carina และการกระตุ้นประสาทวากัส (Carinal Trauma & Vagal Stimulation)",
                    "message": "การกระทุ้งสายบริเวณ Carina จะกระตุ้น Vagal reflex รุนแรงทำให้หัวใจเต้นช้ามากและเยื่อบุเป็นแผล",
                    "clinical_rationale": "เมื่อพบแรงต้านหรือผู้ป่วยไอ ให้ถอยสายออก 1 ซม. ก่อนเริ่มดูดเสมหะ",
                    "hint": "ค่อยๆ ดึงสายออกพร้อมหมุนเบาๆ ห้ามกระทุ้งขึ้นลงเด็ดขาด",
                },
            ],
        },
        # Activity 7: Troubleshooting (Monitor Challenge)
        {
            "display_order": 7,
            "activity_type": "troubleshooting",
            "title": "รับมือสถานการณ์ฉุกเฉินบนมอนิเตอร์: อาการทรุดลงเฉียบพลัน (Patient Monitor Challenge)",
            "instruction": "ขณะกำลังดึงสายดูดเสมหะออก สัญญาณเตือนบนมอนิเตอร์ดังขึ้น: SpO2 ลดลงฮวบเหลือ 84% และอัตราการเต้นของหัวใจลดลงเหลือ 48 ครั้ง/นาที (Severe Bradycardia) การปฏิบัติสำคัญอันดับแรกของคุณคืออะไร?",
            "options": [
                {"option_key": "abort_and_oxygenate", "label": "ยุติการดูดเสมหะทันที รีบถอนสายดูดเสมหะออกทั้งหมด และให้ออกซิเจนความเข้มข้นสูง 100% ทันที", "is_correct": True, "display_order": 1, "description": "หยุดสิ่งกระตุ้น Vagus nerve ทันทีและให้ออกซิเจนชดเชยอย่างเร่งด่วน"},
                {"option_key": "continue_faster", "label": "ดูดเสมหะต่อไปอย่างรวดเร็วอีก 10 วินาทีเพื่อให้เสมหะหมดเกลี้ยง", "is_correct": False, "display_order": 2, "description": "ข้อผิดพลาดร้ายแรง: ยืดเวลาภาวะขาดออกซิเจนรุนแรงและเสี่ยงต่อหัวใจหยุดเต้น"},
                {"option_key": "administer_atropine_first", "label": "คาสายดูดเสมหะไว้แล้ววิ่งไปหายา Atropine ทางหลอดเลือดดำก่อนถอดสาย", "is_correct": False, "display_order": 3, "description": "การปล่อยสายค้างไว้ทำให้การกระตุ้น Vagus nerve ดำเนินต่อไป"},
            ],
            "feedback": [
                {
                    "trigger_key": "abort_and_oxygenate",
                    "feedback_type": "positive",
                    "title": "การช่วยฟื้นตัวฉุกเฉินช่วยชีวิตสำเร็จ (Immediate Life-Saving Recovery)",
                    "message": "การหยุดดูดเสมหะทันทีและให้ออกซิเจน 100% ช่วยบรรเทาปฏิกิริยา Vagal reflex ชีพจรของคุณสมชายกลับมาเต้น 82 ครั้ง/นาที และ SpO2 เพิ่มขึ้นเป็น 95%",
                    "clinical_rationale": "การกระตุ้น Vagus nerve และภาวะขาดออกซิเจนรุนแรงต้องหยุดสิ่งกระตุ้นทันทีและให้ออกซิเจน 100%",
                    "patient_effect_json": {"spo2_delta": +11, "hr_delta": +34, "distress_delta": -1},
                },
                {
                    "trigger_key": "continue_faster",
                    "feedback_type": "critical",
                    "title": "อันตรายถึงขั้นหัวใจหยุดเต้น (Cardiac Arrest Danger)",
                    "message": "การฝืนดูดเสมหะต่อขณะที่หัวใจเต้นช้ามากและขาดออกซิเจนอาจทำให้หัวใจหยุดเต้น (Asystole)",
                    "clinical_rationale": "ความปลอดภัยและสัญญาณชีพของผู้ป่วยสำคัญกว่าการเคลียร์เสมหะเสมอ หากเกิดหัวใจเต้นช้าหรือออกซิเจนตกเฉียบพลัน ต้องหยุดดูดเสมหะทันที",
                    "hint": "เมื่อสัญญาณชีพบนมอนิเตอร์ทรุดลงเฉียบพลัน ให้หยุดดูดเสมหะทันทีและให้ออกซิเจน 100%",
                },
            ],
        },
        # Activity 8: Aftercare
        {
            "display_order": 8,
            "activity_type": "aftercare",
            "title": "การดูแลและปฏิบัติหลังเสร็จสิ้นการดูดเสมหะ (Aftercare)",
            "instruction": "เลือกการพยาบาลที่จำเป็นทั้งหมดหลังเสร็จสิ้นการดูดเสมหะและผู้ป่วยมีสัญญาณชีพคงที่แล้ว",
            "options": [
                {"option_key": "re_auscultate", "label": "ฟังเสียงหายใจที่ปอดทั้งสองข้างซ้ำเพื่อประเมินประสิทธิผลของการกำจัดเสมหะ", "is_correct": True, "display_order": 1},
                {"option_key": "flush_tubing", "label": "ดูดน้ำเกลือปลอดเชื้อล้างสายท่อยางดูดเสมหะจนสะอาด", "is_correct": True, "display_order": 2},
                {"option_key": "restore_fio2", "label": "ปรับลดความเข้มข้นของออกซิเจนบนเครื่องช่วยหายใจกลับสู่ค่าเดิมตามแผนการรักษาเมื่อสัญญาณชีพคงที่", "is_correct": True, "display_order": 3},
                {"option_key": "document_care", "label": "บันทึกทางการพยาบาล: สี ลักษณะ ปริมาณเสมหะ และการตอบสนองของผู้ป่วย", "is_correct": True, "display_order": 4},
                {"option_key": "leave_100_percent", "label": "เปิดออกซิเจน 100% FiO2 ค้างไว้ตลอดไป", "is_correct": False, "display_order": 5},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "การดูแลหลังหัตถการครอบคลุมสมบูรณ์ (Comprehensive Post-Procedure Care)",
                    "message": "การฟังปอดซ้ำ การปรับออกซิเจนคืนค่าเดิม และการบันทึกข้อมูลอย่างครบถ้วนช่วยให้การดูแลผู้ป่วยต่อเนื่องและปลอดภัย",
                    "clinical_rationale": "การปรับ FiO2 กลับสู่ค่าเดิมป้องกันภาวะเป็นพิษจากออกซิเจน (Oxygen Toxicity) ขณะที่ยืนยันว่าทางเดินหายใจโล่งขึ้น",
                    "patient_effect_json": {"secretions_set": "minimal", "distress_set": 0},
                },
                {
                    "trigger_type": "on_selection",
                    "trigger_key": "leave_100_percent",
                    "feedback_type": "caution",
                    "title": "อันตรายจากภาวะเป็นพิษจากออกซิเจน (Oxygen Toxicity Hazard)",
                    "message": "การให้ออกซิเจน 100% ต่อเนื่องเป็นเวลานานเสี่ยงต่อภาวะถุงลมปอดแฟบ (Absorption Atelectasis) และการทำลายเนื้อปอดจากอนุมูลอิสระ",
                    "clinical_rationale": "ต้องปรับลดออกซิเจนกลับสู่ค่าเดิมที่แพทย์สั่งเมื่อผู้ป่วยฟื้นตัวคงที่แล้ว",
                    "hint": "ตรวจสอบให้แน่ใจว่าได้ปรับระดับออกซิเจนกลับสู่ค่าเดิมตามแผนการรักษา",
                },
            ],
        },
        # Activity 9: Patient Outcome
        {
            "display_order": 9,
            "activity_type": "outcome",
            "title": "ผลลัพธ์การดูแลผู้ป่วยและการประเมินขั้นสุดท้าย (Patient Outcome)",
            "instruction": "ทบทวนผลการตอบสนองจำลองของผู้ป่วย เปรียบเทียบสัญญาณชีพหลังทำหัตถการกับข้อมูลตั้งต้นก่อนทำ",
            "content_json": {
                "before": {"spo2": 91, "rr": 26, "hr": 96, "breath_sound": "เสียงเสมหะเดือด Coarse Rhonchi", "secretions": "เสมหะมาก (Copious)"},
                "after": {"spo2": 97, "rr": 18, "hr": 78, "breath_sound": "เสียงปอดโล่งชัดเจนทั้งสองข้าง (Clear)", "secretions": "เสมหะเล็กน้อย/ใส (Minimal/Clear)"},
                "summary": "ภาวะอุดกั้นทางเดินหายใจคลี่คลาย เสียงปอดโล่ง การออกแรงหายใจกลับสู่ปกติ สัญญาณชีพคงที่ปลอดภัย",
            },
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ฟื้นฟูทางเดินหายใจให้โล่งสำเร็จ (Airway Patency Successfully Restored)",
                    "message": "ทางเดินหายใจของคุณสมชายโล่ง ลมเข้าปอดได้ดีทั้งสองข้าง และสัญญาณชีพกลับสู่เกณฑ์ปกติอย่างปลอดภัย",
                    "clinical_rationale": "ตัวบ่งชี้ความสำเร็จของการดูดเสมหะ ได้แก่ SpO2 เพิ่มขึ้น การออกแรงหายใจลดลง และไม่มีเสียง rhonchi",
                    "patient_effect_json": {
                        "spo2_set": 97,
                        "rr_set": 18,
                        "hr_set": 78,
                        "distress_set": 0,
                        "secretions_set": "none",
                        "breath_sound_set": "clear",
                    },
                }
            ],
        },
        # Activity 10: Debrief & Reflection
        {
            "display_order": 10,
            "activity_type": "debrief",
            "title": "สะท้อนคิดและสรุปบทเรียน (Shift Reflection & Debriefing)",
            "instruction": "สะท้อนคิดจากสถานการณ์นี้: หลักการความปลอดภัยที่สำคัญที่สุดที่คุณได้ฝึกฝนในการดูดเสมหะท่อช่วยหายใจคืออะไร?",
            "content_json": {
                "prompt": "แบ่งปันสิ่งที่คุณได้เรียนรู้เกี่ยวกับการให้ออกซิเจนล่วงหน้า การคุมแรงดันดูด หรือการรับมือเมื่อสัญญาณชีพบกพร่อง",
                "placeholder": "เช่น การให้ออกซิเจน 100% ก่อนใส่สาย และการหยุดดูดทันทีเมื่อพบหัวใจเต้นช้า...",
            },
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ได้รับเหรียญผู้พิชิตทางเดินหายใจ (Airway Explorer Badge Awarded!)",
                    "message": "การสะท้อนคิดทางคลินิกยอดเยี่ยมมาก! คุณได้ทำภารกิจห้อง 501: เคลียร์ทางเดินหายใจ สำเร็จเรียบร้อย และได้รับเหรียญ ผู้พิชิตทางเดินหายใจ (Airway Explorer)",
                    "clinical_rationale": "การฝึกฝนแบบสะท้อนคิดช่วยเสริมสร้างทักษะการคิดวิเคราะห์และสัญชาตญาณความปลอดภัยของผู้ป่วย",
                }
            ],
        },
    ]

    # Insert or update activities
    created_acts = 0
    for act_data in ACTIVITIES_DATA:
        order = act_data["display_order"]
        activity = db.session.execute(
            select(Activity).where(
                Activity.scenario_id == scenario.id,
                Activity.display_order == order,
            )
        ).scalar_one_or_none()

        if not activity:
            activity = Activity(
                scenario_id=scenario.id,
                activity_type=act_data["activity_type"],
                title=act_data["title"],
                instruction=act_data["instruction"],
                content_json=act_data.get("content_json", {}),
                display_order=order,
                is_required=True,
                is_active=True,
            )
            db.session.add(activity)
            db.session.flush()
            created_acts += 1
        else:
            activity.title = act_data["title"]
            activity.instruction = act_data["instruction"]
            activity.content_json = act_data.get("content_json", {})
            activity.activity_type = act_data["activity_type"]

        # Seed Options
        for opt_data in act_data.get("options", []):
            existing_opt = db.session.execute(
                select(ActivityOption).where(
                    ActivityOption.activity_id == activity.id,
                    ActivityOption.option_key == opt_data["option_key"],
                )
            ).scalar_one_or_none()
            if not existing_opt:
                db.session.add(ActivityOption(
                    activity_id=activity.id,
                    option_key=opt_data["option_key"],
                    label=opt_data["label"],
                    description=opt_data.get("description"),
                    is_correct=opt_data["is_correct"],
                    display_order=opt_data["display_order"],
                ))
            else:
                existing_opt.label = opt_data["label"]
                existing_opt.description = opt_data.get("description")
                existing_opt.is_correct = opt_data["is_correct"]
                existing_opt.display_order = opt_data["display_order"]

        # Seed Procedure Steps
        for step_data in act_data.get("steps", []):
            existing_step = db.session.execute(
                select(ProcedureStep).where(
                    ProcedureStep.activity_id == activity.id,
                    ProcedureStep.step_key == step_data["step_key"],
                )
            ).scalar_one_or_none()
            if not existing_step:
                db.session.add(ProcedureStep(
                    activity_id=activity.id,
                    step_key=step_data["step_key"],
                    step_text=step_data["step_text"],
                    correct_order=step_data["correct_order"],
                    rationale=step_data.get("rationale"),
                    critical_step=step_data.get("critical_step", False),
                ))
            else:
                existing_step.step_text = step_data["step_text"]
                existing_step.correct_order = step_data["correct_order"]
                existing_step.rationale = step_data.get("rationale")
                existing_step.critical_step = step_data.get("critical_step", False)

        # Seed Feedback Rules
        for fb_data in act_data.get("feedback", []):
            trigger_type = fb_data.get("trigger_type") or ("on_selection" if fb_data.get("trigger_key") else "on_success")
            trigger_key = fb_data.get("trigger_key")

            existing_fb = db.session.execute(
                select(Feedback).where(
                    Feedback.activity_id == activity.id,
                    Feedback.trigger_type == trigger_type,
                    Feedback.trigger_key == trigger_key,
                )
            ).scalar_one_or_none()
            if not existing_fb:
                db.session.add(Feedback(
                    activity_id=activity.id,
                    trigger_type=trigger_type,
                    trigger_key=trigger_key,
                    feedback_type=fb_data.get("feedback_type", "guidance"),
                    title=fb_data["title"],
                    message=fb_data["message"],
                    clinical_rationale=fb_data.get("clinical_rationale"),
                    hint=fb_data.get("hint"),
                    patient_effect_json=fb_data.get("patient_effect_json"),
                ))
            else:
                existing_fb.feedback_type = fb_data.get("feedback_type", "guidance")
                existing_fb.title = fb_data["title"]
                existing_fb.message = fb_data["message"]
                existing_fb.clinical_rationale = fb_data.get("clinical_rationale")
                existing_fb.hint = fb_data.get("hint")
                existing_fb.patient_effect_json = fb_data.get("patient_effect_json")

    # 3. Seed Airway Explorer Badge
    badge = db.session.execute(
        select(Badge).where(Badge.slug == "airway-explorer")
    ).scalar_one_or_none()

    if not badge:
        badge = Badge(
            slug="airway-explorer",
            name="ผู้พิชิตทางเดินหายใจ (Airway Explorer)",
            description="มีส่วนร่วมในการประเมินและดูดเสมหะท่อช่วยหายใจแบบปลอดเชื้อ จัดการความปลอดภัย และฟื้นฟูออกซิเจนฉุกเฉิน",
            icon="airway",
            mission_id=mission.id,
        )
        db.session.add(badge)
        logger.info("Created Badge 'ผู้พิชิตทางเดินหายใจ (Airway Explorer)'")
    else:
        badge.name = "ผู้พิชิตทางเดินหายใจ (Airway Explorer)"
        badge.description = "มีส่วนร่วมในการประเมินและดูดเสมหะท่อช่วยหายใจแบบปลอดเชื้อ จัดการความปลอดภัย และฟื้นฟูออกซิเจนฉุกเฉิน"
        badge.icon = "airway"
        badge.mission_id = mission.id

    db.session.commit()
    logger.info("Room 501 content seeding complete. %s activities configured.", len(ACTIVITIES_DATA))
    return {"scenario": scenario.id, "activities": len(ACTIVITIES_DATA)}
