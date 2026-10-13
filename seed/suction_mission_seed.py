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
            title="การดูดเสมหะทางท่อหลอดลมคอสำหรับคุณสมชาย (Tracheostomy Suctioning for Somchai)",
            patient_name="นายสมชาย (Mr. Somchai)",
            patient_age=68,
            patient_gender="ชาย",
            clinical_summary=(
                "นายสมชาย อายุ 68 ปี พักฟื้นหลังผ่าตัดช่องท้อง ได้รับการใส่ท่อหลอดลมคอ (Tracheostomy tube) "
                "ต่อชุดให้ออกซิเจน Tracheostomy collar (T-collar) ผู้ป่วยมีอาการเหนื่อย หายใจลำบาก หายใจได้ยินเสียงครืดคราด / "
                "ได้ยินเสียงเสมหะในหลอดลม จอมอนิเตอร์แสดงค่า SpO2 ลดลงเหลือ 91% หายใจ 26 ครั้ง/นาที ชีพจร 96 ครั้ง/นาที ฟังปอดได้ยิน rhonchi"
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
        scenario.title = "การดูดเสมหะทางท่อหลอดลมคอสำหรับคุณสมชาย (Tracheostomy Suctioning for Somchai)"
        scenario.patient_name = "นายสมชาย (Mr. Somchai)"
        scenario.patient_age = 68
        scenario.patient_gender = "ชาย"
        scenario.clinical_summary = (
            "นายสมชาย อายุ 68 ปี พักฟื้นหลังผ่าตัดช่องท้อง ได้รับการใส่ท่อหลอดลมคอ (Tracheostomy tube) "
            "ต่อชุดให้ออกซิเจน Tracheostomy collar (T-collar) ผู้ป่วยมีอาการเหนื่อย หายใจลำบาก หายใจได้ยินเสียงครืดคราด / "
            "ได้ยินเสียงเสมหะในหลอดลม จอมอนิเตอร์แสดงค่า SpO2 ลดลงเหลือ 91% หายใจ 26 ครั้ง/นาที ชีพจร 96 ครั้ง/นาที ฟังปอดได้ยิน rhonchi"
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
            "instruction": "ทักทายผู้ป่วย แนะนำตนเอง อธิบายวัตถุประสงค์ของการดูดเสมหะให้ผู้ป่วยทราบ และประเมินสัญญาณชีพ",
            "content_json": {
                "patient_name": "นายสมชาย (Mr. Somchai)",
                "age": 68,
                "history": "วันที่ 2 หลังผ่าตัดช่องท้อง (Post-Op Laparotomy) พักฟื้นหายใจเองผ่านท่อหลอดลมคอใส่ออกซิเจน Collar",
                "airway": "ท่อหลอดลมคอ (Tracheostomy tube) เบอร์ 7.5 มม. ต่อชุดให้ออกซิเจนแบบ Tracheostomy collar",
                "cues_preview": "ผู้ป่วยมีอาการเหนื่อย หายใจลำบาก หายใจได้ยินเสียงครืดคราด / ได้ยินเสียงเสมหะในหลอดลม กระสับกระส่าย",
            },
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ทบทวนข้อมูลและสื่อสารกับผู้ป่วยเรียบร้อย (Patient Communication & Briefing)",
                    "message": "คุณได้ทักทายผู้ป่วย แนะนำตนเอง และอธิบายวัตถุประสงค์ของการดูดเสมหะให้คุณสมชายทราบเรียบร้อยแล้ว ดำเนินการต่อเพื่อประเมินสัญญาณและข้อบ่งชี้ทางคลินิก",
                    "clinical_rationale": "การทักทาย แนะนำตนเอง และอธิบายวัตถุประสงค์ก่อนทำหัตถการช่วยลดความวิตกกังวลและสร้างความร่วมมือจากผู้ป่วยตามแบบประเมินทักษะทางการพยาบาล",
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
                {"option_key": "audible_gurgling", "label": "ผู้ป่วยมีอาการเหนื่อย หายใจลำบาก หายใจได้ยินเสียงครืดคราด / ได้ยินเสียงเสมหะในหลอดลม", "is_correct": True, "display_order": 1},
                {"option_key": "rhonchi", "label": "ฟังปอดได้ยินเสียงเสมหะ (Rhonchi) ทั้งสองข้าง และมองเห็นเสมหะบริเวณท่อหลอดลมคอ", "is_correct": True, "display_order": 2},
                {"option_key": "desaturation", "label": "ค่า Oxygen Saturation จาก Pulse Oximetry ลดลงเหลือ 91% ร่วมกับมีอาการกระสับกระส่าย", "is_correct": True, "display_order": 3},
                {"option_key": "scheduled_q2h", "label": "ดูดเสมหะตามรอบเวลาที่กำหนดทุก 2 ชั่วโมง โดยไม่มีอาการบ่งชี้", "is_correct": False, "display_order": 4},
                {"option_key": "prevent_fever", "label": "ดูดเสมหะเป็นประจำเพื่อป้องกันไข้หลังผ่าตัด", "is_correct": False, "display_order": 5},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "การประเมินทางคลินิกถูกต้อง (Accurate Clinical Assessment)",
                    "message": "คุณระบุข้อบ่งชี้ทางคลินิกจากการประเมินทางเดินหายใจได้อย่างถูกต้องตามแบบประเมินทักษะทางการพยาบาล",
                    "clinical_rationale": "ข้อบ่งชี้สำคัญ ได้แก่ ผู้ป่วยมีอาการเหนื่อย หายใจลำบาก หายใจได้ยินเสียงครืดคราด/ได้ยินเสียงเสมหะในหลอดลม และค่าความอิ่มตัวออกซิเจนลดลง",
                },
                {
                    "trigger_type": "on_selection",
                    "trigger_key": "scheduled_q2h",
                    "feedback_type": "caution",
                    "title": "อันตรายจากการดูดเสมหะตามรอบเวลา (Routine Suctioning Hazard)",
                    "message": "การดูดเสมหะตามตารางเวลาเป็นประจำล้าสมัยและก่ออันตราย ควรดูดเสมหะเมื่อมีอาการทางคลินิกบ่งชี้เท่านั้น",
                    "clinical_rationale": "การใส่สายดูดเสมหะโดยไม่จำเป็นจะครูดทำลายเยื่อบุหลอดลมและเพิ่มความเสี่ยงต่อการติดเชื้อทางเดินหายใจและปอดอักเสบ",
                    "hint": "เลือกเฉพาะข้อค้นพบที่แสดงถึงการอุดกั้นของเสมหะในทางเดินหายใจหรือการแลกเปลี่ยนออกซิเจนลดลง",
                },
            ],
        },
        # Activity 3: Gear Up (Equipment Select)
        {
            "display_order": 3,
            "activity_type": "equipment_select",
            "title": "เตรียมอุปกรณ์ปลอดเชื้อและการทดสอบเครื่องดูดเสมหะ (Gear Up & Suction Setup)",
            "instruction": "เลือกรายการอุปกรณ์ปลอดเชื้อ อุปกรณ์ป้องกันการแพร่กระจายเชื้อ และการตั้งค่าแรงดูดที่ถูกต้องตามแบบประเมิน",
            "options": [
                {
                    "option_key": "suction_set",
                    "label": "ชุดดูดเสมหะปลอดเชื้อ (Set suction) ประกอบด้วย สายดูดเสมหะปลอดเชื้อ (เบอร์ 12–14 Fr) และถุงมือปลอดเชื้อ (Sterile gloves)",
                    "is_correct": True,
                    "display_order": 1,
                },
                {"option_key": "vacuum_100_120", "label": "เปิดเครื่องดูดเสมหะและทดสอบแรงดูดของเครื่องดูดเสมหะ (ปรับตั้ง 100–120 mmHg ในผู้ใหญ่)", "is_correct": True, "display_order": 2},
                {"option_key": "sterile_saline", "label": "ภาชนะใส่น้ำสะอาดสำหรับดูดน้ำล้างสาย และสำลีชุบแอลกอฮอล์ 70% สำหรับเช็ดข้อต่อ", "is_correct": True, "display_order": 3},
                {"option_key": "face_shield", "label": "อุปกรณ์ป้องกันการแพร่กระจายเชื้อ: สวม Mask ถูกต้อง ล้างมือถูกวิธีไม่ใส่นาฬิกา และแว่นป้องกัน/Face shield", "is_correct": True, "display_order": 4},
                {"option_key": "clean_gloves_only", "label": "ถุงมือสะอาดธรรมดาที่ไม่ปลอดเชื้อสำหรับการดูดเสมหะทางท่อหลอดลมคอ", "is_correct": False, "display_order": 5},
                {"option_key": "vacuum_200", "label": "ตั้งแรงดูดของเครื่องดูดเสมหะสูงถึง 200 mmHg", "is_correct": False, "display_order": 6},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "เตรียมอุปกรณ์และทดสอบเครื่องเรียบร้อย (Equipment & Vacuum Ready)",
                    "message": "ชุดดูดเสมหะปลอดเชื้อ อุปกรณ์ป้องกันการแพร่กระจายเชื้อ และการทดสอบแรงดูด (100–120 mmHg) ถูกต้องครบถ้วนตามแบบประเมิน",
                    "clinical_rationale": "ต้องเตรียมอุปกรณ์ให้ครบถ้วน ทดสอบความพร้อมใช้ของเครื่องดูดเสมหะ และหยิบจับเครื่องใช้ปลอดเชื้ออย่างถูกวิธี",
                },
                {
                    "trigger_type": "on_selection",
                    "trigger_key": "vacuum_200",
                    "feedback_type": "critical",
                    "title": "อันตรายจากแรงดูดสูงเกินไป (Dangerous Negative Pressure)",
                    "message": "แรงดูด 200 mmHg สูงเกินไปและอันตรายมากสำหรับผู้ใหญ่",
                    "clinical_rationale": "แรงดูดที่สูงเกินไปจะดูดดึงเยื่อบุหลอดลมเข้าไปในรูข้างสายดูด ทำให้เลือดออกและเกิดปอดแฟบ (atelectasis)",
                    "hint": "แรงดูดของเครื่องดูดเสมหะในผู้ใหญ่ต้องควบคุมให้อยู่ระหว่าง 100–120 mmHg อย่างเคร่งครัด",
                },
            ],
        },
        # Activity 4: Safety Check
        {
            "display_order": 4,
            "activity_type": "safety_check",
            "title": "การเตรียมความพร้อมและความปลอดภัยก่อนดูดเสมหะ (Pre-Procedure Safety & Planning)",
            "instruction": "ยืนยันการจัดท่า การป้องกันการแพร่กระจายเชื้อ และการเตรียมผู้ป่วยก่อนทำหัตถการตามแบบประเมิน",
            "options": [
                {"option_key": "pre_oxygenate", "label": "ให้ออกซิเจนความเข้มข้นสูง (Hyperoxygenate 100% O2) 30–60 วินาทีก่อนทำหัตถการ", "is_correct": True, "display_order": 1},
                {"option_key": "semi_fowler", "label": "จัดท่าศีรษะสูง 30 องศา (รายงานด้วยวาจา)", "is_correct": True, "display_order": 2},
                {"option_key": "monitor_vitals", "label": "ล้างมือถูกวิธี ไม่ใส่นาฬิกา สวม Mask ถูกต้อง และประเมินค่า Oxygen Saturation จาก Pulse Oximeter", "is_correct": True, "display_order": 3},
                {"option_key": "routine_saline_bolus", "label": "หยดน้ำเกลือปลอดเชื้อ 5 มล. เข้าท่อหลอดลมคอก่อนดูดเสมหะเป็นประจำ", "is_correct": False, "display_order": 4},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "เตรียมความพร้อมถูกต้องตามแบบประเมิน (Preparation Standard Met)",
                    "message": "จัดท่าศีรษะสูง 30 องศา ล้างมือ สวม Mask และเตรียมความพร้อมด้านออกซิเจนถูกต้องครบถ้วน",
                    "clinical_rationale": "การจัดท่าศีรษะสูง 30 องศา ช่วยให้กระบังลมหย่อนตัว ปอดขยายได้ดี และการให้ออกซิเจนล่วงหน้าป้องกันภาวะออกซิเจนตกเฉียบพลัน",
                    "patient_effect_json": {"spo2_delta": +2},
                },
                {
                    "trigger_type": "on_selection",
                    "trigger_key": "routine_saline_bolus",
                    "feedback_type": "caution",
                    "title": "ไม่แนะนำให้หยดน้ำเกลือเข้าท่อหลอดลมคอเป็นกิจวัตร (Routine Saline Lavage Discouraged)",
                    "message": "แนวปฏิบัติปัจจุบันไม่แนะนำให้หยดน้ำเกลือลงในท่อหลอดลมคอเป็นกิจวัตร",
                    "clinical_rationale": "น้ำเกลือไม่ช่วยละลายเสมหะอย่างแท้จริง แต่จะชะล้างคราบจุลชีพ (biofilm) ลงสู่ปอดส่วนลึก เพิ่มความเสี่ยงปอดอักเสบ",
                    "hint": "เน้นการให้ออกซิเจนล่วงหน้าและการจัดท่าผู้ป่วย หลีกเลี่ยงการหยดน้ำเกลือลงท่อหลอดลมคอ",
                },
            ],
        },
        # Activity 5: Sequence (Put It in Order)
        {
            "display_order": 5,
            "activity_type": "sequence",
            "title": "จัดลำดับขั้นตอนการดูดเสมหะทางท่อหลอดลมคอ (Suctioning Procedure Sequence)",
            "instruction": "เรียงลำดับขั้นตอนการดูดเสมหะตามแบบประเมินทักษะทางการพยาบาล โดยยึดหลักปลอดเชื้ออย่างเคร่งครัด",
            "steps": [
                {"step_key": "step_preox", "step_text": "ให้ออกซิเจน 100% O2 ล่วงหน้า และเช็ดปลาย finger tip จนถึงต่ำกว่าข้อต่อ 1 นิ้วด้วยแอลกอฮอล์ 70%", "correct_order": 1, "rationale": "ต้องให้ออกซิเจนล่วงหน้าและเช็ดทำความสะอาดข้อต่อด้วยแอลกอฮอล์ 70% ก่อนต่อสาย", "critical_step": True},
                {"step_key": "step_don_sterile", "step_text": "สวมถุงมือปลอดเชื้อข้างที่ถนัดอย่างถูกวิธี หยิบสายดูดเสมหะปลอดเชื้อและต่อเข้ากับข้อต่อ ไม่เกิดการปนเปื้อน พร้อมเปิดเครื่องและทดสอบแรงดูด", "correct_order": 2, "rationale": "สวมถุงมือปลอดเชื้อข้างที่ถนัด หยิบจับสายปลอดเชื้อ และเปิดเครื่องด้วยมือข้างที่ไม่สวมถุงมือ สายไม่ปนเปื้อน", "critical_step": True},
                {"step_key": "step_insert_no_suction", "step_text": "สอดสายดูดเสมหะเข้าไปในท่อหลอดลมคออย่างรวดเร็วและนุ่มนวล ยังไม่ดูดเสมหะ (สอดสายลึกประมาณ 9–10 ซม. โดยจับสายที่ตำแหน่งประมาณ 12 ซม.)", "correct_order": 3, "rationale": "สอดสายอย่างรวดเร็วและนุ่มนวล ยังไม่ดูดเสมหะ และกะความลึก 9–10 ซม. เพื่อป้องกันการบาดเจ็บต่อ Carina", "critical_step": True},
                {"step_key": "step_suction_withdraw", "step_text": "ดูดเสมหะโดยหมุนสายไปมารอบท่อและค่อยดึงสายขึ้น (ระยะเวลาเริ่มสอดสายจนสายพ้นท่อเจาะคอ 10–15 วินาทีต่อรอบ)", "correct_order": 4, "rationale": "ดูดเสมหะโดยหมุนสายรอบท่อและค่อยดึงขึ้น ใช้เวลารวมไม่เกิน 10–15 วินาที เพื่อป้องกันภาวะขาดออกซิเจน", "critical_step": True},
                {"step_key": "step_post_oxygenate", "step_text": "ก่อนดูดซ้ำ เว้นระยะให้หายใจ 3–5 ครั้ง และให้ออกซิเจนชดเชย (ดูดไม่เกิน 2 ครั้งต่อรอบของการดูดเสมหะ)", "correct_order": 5, "rationale": "เว้นระยะให้ผู้ป่วยหายใจ 3–5 ครั้ง ให้ออกซิเจนชดเชย และดูดไม่เกิน 2 ครั้งต่อรอบของการดูดเสมหะ", "critical_step": True},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ลำดับขั้นตอนหัตถการถูกต้องสมบูรณ์ (Flawless Procedural Sequence)",
                    "message": "คุณจัดลำดับขั้นตอนการดูดเสมหะได้ถูกต้องตามเกณฑ์แบบประเมินทักษะทางการพยาบาลทุกประการ",
                    "clinical_rationale": "การเช็ด finger tip, สวมถุงมือปลอดเชื้อ, สอดสายลึก 9–10 ซม. โดยยังไม่ดูด, หมุนสายและดึงขึ้นภายใน 10–15 วินาที และเว้นระยะให้หายใจ 3–5 ครั้ง (ไม่เกิน 2 ครั้งต่อรอบ) เป็นหัวใจสำคัญของความปลอดภัย",
                    "patient_effect_json": {"secretions_set": "moderate"},
                },
                {
                    "trigger_type": "on_mistake",
                    "title": "ลำดับขั้นตอนต้องปรับปรุง (Sequence Needs Adjustment)",
                    "message": "บางขั้นตอนไม่ถูกต้องตามลำดับหรืออาจส่งผลต่อความปลอดภัยของผู้ป่วย",
                    "clinical_rationale": "ข้อควรจำ: เช็ดข้อต่อด้วยแอลกอฮอล์ สวมถุงมือปลอดเชื้อ สอดสายโดยยังไม่ดูด และเว้นระยะให้หายใจ 3–5 ครั้งก่อนดูดซ้ำ",
                    "hint": "ตรวจสอบว่าสวมถุงมือปลอดเชื้อและให้ออกซิเจนล่วงหน้าก่อนสอดสายดูดเสมหะหรือไม่",
                },
            ],
        },
        # Activity 6: Critical Decision
        {
            "display_order": 6,
            "activity_type": "decision",
            "title": "การตัดสินใจสำคัญ: จังหวะและเทคนิคการดูดเสมหะ (Critical Technique Decision)",
            "instruction": "เมื่อสอดสายดูดเสมหะลึกประมาณ 9–10 ซม. แล้ว ควรเปิดแรงดูดและควบคุมเวลาอย่างไรตามแบบประเมิน?",
            "options": [
                {"option_key": "only_on_withdraw", "label": "ดูดเสมหะโดยหมุนสายไปมารอบท่อและค่อยดึงสายขึ้น (ระยะเวลาเริ่มสอดสายจนสายพ้นท่อเจาะคอ 10–15 วินาที)", "is_correct": True, "display_order": 1, "description": "หมุนสายรอบท่อและค่อยดึงขึ้น ใช้เวลารวม 10–15 วินาทีตามเกณฑ์แบบประเมิน"},
                {"option_key": "during_insertion", "label": "เปิดแรงดูดทันทีตั้งแต่เริ่มสอดสายเข้าไปในท่อหลอดลมคอ", "is_correct": False, "display_order": 2, "description": "การดูดขณะสอดสายเข้าทำให้เยื่อบุหลอดลมฉีกขาดและดึงอากาศออกจากปอดอย่างรวดเร็ว"},
                {"option_key": "vigorous_pumping", "label": "เปิดแรงดูดแล้วดึงสายออกพร้อมควงสายและชักเข้าออกอย่างรวดเร็ว", "is_correct": False, "display_order": 3, "description": "ทำให้เกิดแผลถลอกและกระตุ้น Vagus nerve รุนแรง"},
            ],
            "feedback": [
                {
                    "trigger_key": "only_on_withdraw",
                    "feedback_type": "positive",
                    "title": "ปฏิบัติเทคนิคได้อย่างปลอดภัยตามแบบประเมิน (Safe Technique Executed)",
                    "message": "การดูดเสมหะโดยหมุนสายรอบท่อและค่อยดึงสายขึ้นภายใน 10–15 วินาที ถูกต้องตามแบบประเมินและช่วยป้องกันการบาดเจ็บต่อเยื่อบุทางเดินหายใจ",
                    "clinical_rationale": "การดูดเฉพาะตอนดึงสายขึ้นพร้อมหมุนสายรอบท่อ ช่วยกำจัดเสมหะรอบด้านและปกป้องเยื่อบุหลอดลมจากการบาดเจ็บ",
                    "patient_effect_json": {"distress_delta": -1},
                },
                {
                    "trigger_key": "during_insertion",
                    "feedback_type": "critical",
                    "title": "อันตรายจากการบาดเจ็บต่อทางเดินหายใจ (Airway Trauma Hazard)",
                    "message": "การดูดเสมหะขณะสอดสายจะครูดทำลายเยื่อบุหลอดลมและดูดเอาออกซิเจนออกจากปอดอย่างรวดเร็ว",
                    "clinical_rationale": "ข้อกำหนดตามแบบประเมิน: สอดสายอย่างรวดเร็วและนุ่มนวล ยังไม่ดูดเสมหะ",
                    "hint": "ต้องสอดสายโดยไม่เปิดแรงดูด และเปิดแรงดูดเฉพาะตอนดึงสายออกเท่านั้น",
                },
                {
                    "trigger_key": "vigorous_pumping",
                    "feedback_type": "critical",
                    "title": "อันตรายต่อเยื่อบุหลอดลมและการกระตุ้นวากัส (Airway Trauma & Vagal Stimulation)",
                    "message": "การควงสายอย่างรุนแรงขณะดูดเสมหะทำให้เยื่อบุหลอดลมเกิดแผลและกระตุ้น Vagus nerve",
                    "clinical_rationale": "ทำให้เกิดแผลถลอกและกระตุ้น Vagus nerve รุนแรง",
                    "hint": "ค่อยๆ หมุนสายรอบท่อและดึงสายขึ้นอย่างนุ่มนวล ห้ามชักเข้าออก",
                },
            ],
        },
        # Activity 7: Troubleshooting (Monitor Challenge)
        {
            "display_order": 7,
            "activity_type": "troubleshooting",
            "title": "รับมือสถานการณ์ฉุกเฉินบนมอนิเตอร์: อาการทรุดลงเฉียบพลัน (Patient Monitor Challenge)",
            "instruction": "ขณะกำลังดึงสายดูดเสมหะออก สัญญาณเตือนบนมอนิเตอร์ดังขึ้น: SpO2 ลดลงฮวบเหลือ 84% และอัตราการเต้นของหัวใจลดลงเหลือ 48 ครั้ง/นาที (Severe Bradycardia) การปฏิบัติสำคัญอันดับแรกของคุณคืออะไร?",
            "content_json": {
                "is_emergency": True,
                "theme_color": "red",
                "alarm_badge": "PATIENT MONITOR ALERT / สัญญาณชีพทรุดลงเฉียบพลัน",
                "alarm_code": "HR 48 BPM CRITICAL",
                "image_url": "images/patients/patient_somchai.jpg",
                "image_alt": "ภาพจำลองคุณสมชายเกิดภาวะหัวใจเต้นช้าและออกซิเจนตกขณะดูดเสมหะ",
                "image_overlay_text": "HR 48 bpm | SpO2 84%",
                "event_header": "สัญญาณเตือนวิกฤตบนมอนิเตอร์ (Critical Bedside Monitor Alarm)",
                "urgent_message": "ขณะกำลังดึงสายดูดเสมหะออก สัญญาณเตือนบนมอนิเตอร์ดังขึ้นเฉียบพลัน: SpO2 ลดลงฮวบเหลือ 84% และอัตราการเต้นของหัวใจลดลงเหลือ 48 ครั้ง/นาที (Severe Bradycardia)",
                "scenario_description": "ผู้ป่วยเริ่มซึมลงและริมฝีปากคล้ำจากปฏิกิริยา Vagal reflex ร่วมกับภาวะขาดออกซิเจนเฉียบพลัน ต้องการการตัดสินใจช่วยชีวิตทันท่วงที",
                "telemetry": {
                    "spo2": "84%",
                    "spo2_alert": True,
                    "spo2_trend": "Critical Desat",
                    "hr": "48",
                    "hr_alert": True,
                    "hr_trend": "Severe Bradycardia",
                    "rr": "26",
                    "rr_trend": "Tachypnea",
                    "rr_alert": True,
                    "patient_status": "หัวใจเต้นช้าวิกฤต / ซึมลง",
                    "status_sub": "Vagal Reaction",
                    "status_alert": True,
                },
                "challenge_question": "การปฏิบัติการพยาบาลที่สำคัญที่สุดเป็นอันดับแรกเพื่อช่วยชีวิตผู้ป่วยคืออะไร?",
            },
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
                    "patient_effect_json": {"spo2_set": 95, "hr_set": 82, "distress_delta": -1},
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
            "title": "การดูแลหลังดูดเสมหะและการประเมินผล (Aftercare, Evaluation & Documentation)",
            "instruction": "เลือกการพยาบาลหลังดูดเสมหะตามหลักป้องกันการแพร่กระจายเชื้อและการประเมินผลตามแบบประเมิน",
            "options": [
                {"option_key": "re_auscultate", "label": "การประเมินผล (รายงานด้วยวาจา): ประเมินว่าผู้ป่วยหายใจสะดวก ไม่กระสับกระส่าย เสียงเสมหะลดลง และฟังเสียงปอดซ้ำ", "is_correct": True, "display_order": 1},
                {"option_key": "flush_tubing", "label": "ดูดน้ำล้างสายไม่แพร่กระจายเชื้อ ปิดเครื่องดูดเสมหะและปลดสายดูดเสมหะออก เช็ดเหนือข้อต่อ 1 นิ้วลงมาที่ปลาย tip ด้วยแอลกอฮอล์ 70%", "is_correct": True, "display_order": 2},
                {"option_key": "restore_fio2", "label": "ถอดถุงมือและทิ้งสายดูดเสมหะถูกต้อง ล้างมือถูกวิธี ถอด Mask ทิ้งถูกวิธี และปรับอัตราการไหลของออกซิเจนคืนค่าเดิม", "is_correct": True, "display_order": 3},
                {"option_key": "document_care", "label": "การบันทึก (รายงานด้วยวาจา): บันทึกสภาวะของผู้ป่วยและลักษณะการหายใจ ลักษณะของเสมหะ (สี กลิ่น ปริมาณ) และค่า Oxygen Saturation จาก Pulse Oximetry", "is_correct": True, "display_order": 4},
                {"option_key": "leave_100_percent", "label": "เปิดออกซิเจน 100% FiO2 ค้างไว้ตลอดเวลา", "is_correct": False, "display_order": 5},
            ],
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "การดูแลหลังหัตถการครบถ้วนตามแบบประเมิน (Rubric Criteria Fully Met)",
                    "message": "ดูดน้ำล้างสาย เช็ดข้อต่อด้วยแอลกอฮอล์ 70% ทิ้งขยะและถอดอุปกรณ์ถูกต้อง พร้อมประเมินผลและบันทึกทางการพยาบาลครบถ้วน",
                    "clinical_rationale": "หลังดูดเสมหะต้องใช้หลักป้องกันการแพร่กระจายเชื้อ เช็ดข้อต่อ ล้างมือ ถอด Mask และรายงานการประเมินผลและการบันทึกด้วยวาจา",
                    "patient_effect_json": {
                        "breath_sound_set": "clear",
                        "secretions_set": "minimal",
                        "distress_set": 0,
                        "spo2_set": 97,
                        "hr_set": 78,
                        "rr_set": 18,
                    },
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
            "title": "ผลลัพธ์และการบันทึกทางการพยาบาล (Patient Outcome & Documentation)",
            "instruction": "ทบทวนการประเมินผลและการบันทึกทางการพยาบาล (รายงานด้วยวาจา) ตามเกณฑ์แบบประเมินทักษะ",
            "content_json": {
                "before": {"spo2": 91, "rr": 26, "hr": 96, "breath_sound": "เสียงเสมหะ Rhonchi", "secretions": "มีอาการเหนื่อย หายใจเสียงครืดคราด เสมหะมาก"},
                "after": {"spo2": 97, "rr": 18, "hr": 78, "breath_sound": "เสียงปอดโล่งชัดเจนทั้งสองข้าง (Clear)", "secretions": "หายใจสะดวก ไม่กระสับกระส่าย เสียงเสมหะลดลง"},
                "summary": "การประเมินผลและการบันทึกทางการพยาบาล (รายงานด้วยวาจา):\n1. สภาวะของผู้ป่วยและลักษณะการหายใจ: ผู้ป่วยรู้สึกตัวดี หายใจสะดวก ไม่กระสับกระส่าย อัตราการหายใจ 18 ครั้ง/นาที เสียงเสมหะลดลง ปอดโล่งทั้งสองข้าง\n2. ลักษณะของเสมหะ: เสมหะสีขาวขุ่น เหนียวเล็กน้อย ไม่มีกลิ่น ปริมาณปานกลาง\n3. ค่า Oxygen Saturation จาก Pulse Oximetry: เพิ่มขึ้นจาก 91% เป็น 97% หลังทำหัตถการ",
            },
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ประเมินผลและบันทึกทางการพยาบาลสมบูรณ์ (Evaluation & Documentation Complete)",
                    "message": "ทางเดินหายใจของคุณสมชายโล่ง ผู้ป่วยหายใจสะดวก ไม่กระสับกระส่าย เสียงเสมหะลดลง และบันทึกข้อมูลครบถ้วนตามเกณฑ์",
                    "clinical_rationale": "เกณฑ์การประเมินและการบันทึกครอบคลุม: สภาวะผู้ป่วย ลักษณะการหายใจ ลักษณะเสมหะ (สี กลิ่น ปริมาณ) และค่า oxygen saturation",
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
            "instruction": "สะท้อนคิดจากสถานการณ์นี้: หลักการความปลอดภัยที่สำคัญที่สุดที่คุณได้ฝึกฝนในการดูดเสมหะท่อหลอดลมคอตามแบบประเมินคืออะไร?",
            "content_json": {
                "prompt": "แบ่งปันสิ่งที่คุณได้เรียนรู้เกี่ยวกับการให้ออกซิเจนล่วงหน้า การยึดหลักปลอดเชื้อ การคุมแรงดูดและเวลาดูดเสมหะ หรือการบันทึกทางการพยาบาล",
                "placeholder": "เช่น การรักษาหลักปลอดเชื้อ การสอดสายลึก 9-10 ซม. โดยยังไม่ดูด และการจำกัดเวลา 10-15 วินาที...",
            },
            "feedback": [
                {
                    "trigger_type": "on_success",
                    "title": "ได้รับเหรียญผู้พิชิตทางเดินหายใจ (Airway Explorer Badge Awarded!)",
                    "message": "การสะท้อนคิดทางคลินิกยอดเยี่ยมมาก! คุณได้ทำภารกิจห้อง 501: เคลียร์ทางเดินหายใจ สำเร็จเรียบร้อยตามเกณฑ์แบบประเมิน และได้รับเหรียญ ผู้พิชิตทางเดินหายใจ (Airway Explorer)",
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
        configured_keys = {opt["option_key"] for opt in act_data.get("options", [])}
        for existing_opt in list(activity.options):
            if existing_opt.option_key not in configured_keys:
                db.session.delete(existing_opt)

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
            description="มีส่วนร่วมในการประเมินและดูดเสมหะทางท่อหลอดลมคอแบบปลอดเชื้อ จัดการความปลอดภัย และฟื้นฟูออกซิเจนฉุกเฉิน",
            icon="airway",
            mission_id=mission.id,
        )
        db.session.add(badge)
        logger.info("Created Badge 'ผู้พิชิตทางเดินหายใจ (Airway Explorer)'")
    else:
        badge.name = "ผู้พิชิตทางเดินหายใจ (Airway Explorer)"
        badge.description = "มีส่วนร่วมในการประเมินและดูดเสมหะทางท่อหลอดลมคอแบบปลอดเชื้อ จัดการความปลอดภัย และฟื้นฟูออกซิเจนฉุกเฉิน"
        badge.icon = "airway"
        badge.mission_id = mission.id

    db.session.commit()
    logger.info("Room 501 content seeding complete. %s activities configured.", len(ACTIVITIES_DATA))
    return {"scenario": scenario.id, "activities": len(ACTIVITIES_DATA)}
