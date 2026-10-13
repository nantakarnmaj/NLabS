"""Seed data for Room 504: Respiratory Rescue (Integrated Emergency Scenario).

Patient: Mr. Prasert (นายประเสริฐ), 70-year-old male with COPD & pneumonia presenting
with acute severe respiratory distress, hypoxemia SpO2 87%, copious secretions with weak cough,
and bilateral bronchospasm. Integrates skills from suctioning, oxygen therapy, and nebulization.
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


def seed_rescue_mission() -> dict[str, int]:
    """Idempotently seed scenario, 10 activities, feedback rules, and badge for Room 504."""
    mission = db.session.execute(
        select(Mission).where((Mission.room_number == "504") | (Mission.slug == "respiratory-rescue"))
    ).scalar_one_or_none()

    if not mission:
        logger.error("Mission Room 504 not found; run seed_rooms first")
        return {"activities": 0}

    # Mark mission availability as playable (access will be guarded by prerequisite checks)
    mission.availability = "playable"

    # 1. Create or update Scenario
    scenario = db.session.execute(
        select(Scenario).where(Scenario.mission_id == mission.id)
    ).scalar_one_or_none()

    initial_vitals = {
        "spo2": 87,
        "rr": 30,
        "hr": 108,
        "distress": 3,
        "secretions": "copious_thick",
        "breath_sound": "bilateral_wheezes_and_rhonchi",
        "consciousness": "anxious_exhausted",
    }

    scenario_title = "การกู้ชีพฉุกเฉินระบบหายใจแบบบูรณาการสำหรับคุณประเสริฐ (Integrated Respiratory Rescue for Mr. Prasert)"
    patient_name = "นายประเสริฐ (Mr. Prasert)"
    clinical_summary = (
        "นายประเสริฐ อายุ 70 ปี โรคประจำตัวถุงลมโป่งพอง (COPD) และมีปอดอักเสบแทรกซ้อน (Pneumonia) "
        "มีภาวะหายใจลำบากวิกฤตเฉียบพลัน ริมฝีปากเขียวคล้ำ หายใจใช้กล้ามเนื้อเสริม มีเสียงเสมหะเดือดในหลอดลม ไออ่อนแรง "
        "และฟังปอดได้ยินเสียงหวีดทั้งสองข้าง มอนิเตอร์แสดง SpO2 87% ในอากาศห้อง, อัตราหายใจ 30 ครั้ง/นาที, ชีพจร 108 ครั้ง/นาที"
    )

    if not scenario:
        scenario = Scenario(
            mission_id=mission.id,
            title=scenario_title,
            patient_name=patient_name,
            patient_age=70,
            patient_gender="ชาย",
            clinical_summary=clinical_summary,
            initial_state_json=initial_vitals,
            difficulty="advanced",
            is_active=True,
        )
        db.session.add(scenario)
        db.session.flush()
        logger.info("Created Scenario for Room 504 id=%s", scenario.id)
    else:
        scenario.title = scenario_title
        scenario.patient_name = patient_name
        scenario.patient_age = 70
        scenario.patient_gender = "ชาย"
        scenario.clinical_summary = clinical_summary
        scenario.initial_state_json = initial_vitals
        scenario.is_active = True

    # 2. 10 Formative Activities
    ACTIVITIES_DATA = [
        # Activity 1: Intro / Emergency Briefing
        {
            "activity_type": "intro",
            "title": "สถานการณ์ฉุกเฉิน",
            "instruction": "ตรวจดูสัญญาณชีพบอร์ดมอนิเตอร์ข้างเตียง อาการทางคลินิก และสัญญาณเตือนภาวะการหายใจล้มเหลวเฉียบพลันของคุณประเสริฐ",
            "content_json": {
                "patient_name": "นายประเสริฐ (Mr. Prasert, 70 ปี)",
                "context": (
                    "คุณประเสริฐเป็นโรค COPD ระยะลุกลามและปอดอักเสบแทรกซ้อน นั่งโน้มตัวไปข้างหน้าในท่า Tripod ริมฝีปากเขียวคล้ำ "
                    "หายใจมีรอยบุ๋มซี่โครง ได้ยินเสียงเสมหะเดือดและเสียงหวีดชัดเจน ไอเบาแรงและหมดแรง มอนิเตอร์: SpO2 87% ในอากาศห้อง, "
                    "หายใจ 30 ครั้ง/นาที, ชีพจร 108 ครั้ง/นาที"
                ),
                "goal": "สังเคราะห์การประเมิน จัดลำดับการกู้ชีพเบื้องต้น ให้ออกซิเจนและดูดเสมหะอย่างปลอดภัย พ่นยาขยายหลอดลม จัดการอาการทรุดลงเฉียบพลัน และสื่อสารส่งต่อด้วย SBAR",
            },
            "display_order": 1,
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "เริ่มต้นการประเมินภาวะฉุกเฉิน (Emergency Assessment Initiated)",
                    "message": "เริ่มการประเมินอาการหลายมิติเพื่อระบุสัญญาณทางคลินิกทั้งหมดที่เป็นอันตรายถึงแก่ชีวิต",
                    "clinical_rationale": "การระบุภาวะพร่องออกซิเจน ทางเดินหายใจอุดกั้น และหลอดลมหดเกร็งอย่างรวดเร็วและเป็นระบบช่วยชี้แนะการจัดลำดับการกู้ชีพที่ถูกต้อง",
                }
            ],
        },
        # Activity 2: Multidimensional Cue Recognition
        {
            "activity_type": "clinical_cues",
            "title": "ประเมินสัญญาณวิกฤตและความล้มเหลวทางการหายใจ (Critical Cue Recognition)",
            "instruction": "เลือกข้อค้นพบจากการตรวจประเมินสำคัญทั้งหมดที่บ่งชี้ว่าผู้ป่วยอยู่ในภาวะการหายใจล้มเหลวเฉียบพลันที่ต้องการการช่วยเหลือทันที",
            "content_json": {},
            "display_order": 2,
            "options": [
                {"option_key": "severe_hypoxemia_87", "label": "ภาวะพร่องออกซิเจนรุนแรง (SpO₂ Room air 87% ร่วมกับริมฝีปากเขียวคล้ำ)", "is_correct": True},
                {"option_key": "tachypnea_and_retractions", "label": "หายใจเร็วมาก (30 ครั้ง/นาที) หายใจใช้กล้ามเนื้อช่วย และนั่งในท่า Tripod", "is_correct": True},
                {"option_key": "copious_secretions_weak_cough", "label": "เสมหะเหนียวข้นปริมาณมากในลำคอ ร่วมกับแรงไออ่อนแรงและเหนื่อยล้า", "is_correct": True},
                {"option_key": "bilateral_wheezes_and_rhonchi", "label": "ฟังปอดได้ยินทั้งเสียงหวีด Wheezes และเสียง Rhonchi ทั้งสองข้าง", "is_correct": True},
                {"option_key": "clear_vesicular_breath_sounds", "label": "เสียงหายใจปกติ ทั่วทั้งสองข้างของปอด", "is_correct": False},
                {"option_key": "adequate_spontaneous_clearance", "label": "ผู้ป่วยสามารถไอขับเสมหะออกได้เองอย่างมีประสิทธิภาพและสุขสบาย", "is_correct": False},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ระบุสัญญาณอันตรายครบถ้วน (Comprehensive Cues Identified)",
                    "message": "คุณระบุภาวะพร่องออกซิเจนรุนแรง (87%) การล้าของกล้ามเนื้อหายใจ เสมหะคั่งค้าง และหลอดลมหดเกร็งพร้อมกันได้อย่างแม่นยำ",
                    "clinical_rationale": "คุณประเสริฐเผชิญภาวะวิกฤตซ้ำซ้อน 3 ประการ: V/Q mismatch รุนแรง, การอุดกั้นทางกายภาพของเสมหะ, และการหดเกร็งของหลอดลมส่วนล่าง",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "clear_vesicular_breath_sounds",
                    "feedback_type": "caution",
                    "title": "การฟังปอดไม่ถูกต้อง (Incorrect Auscultation Finding)",
                    "message": "คุณประเสริฐมีเสียงเสมหะเดือดและเสียงหวีดชัดเจน ไม่ใช่เสียง vesicular ที่เป็นเสียงหายใจของปอดปกติ",
                    "hint": "เน้นเสียงผิดปกติที่เกิดจากเสมหะคั่งค้างและหลอดลมที่ตีบแคบ",
                },
            ],
        },
        # Activity 3: Emergency Prioritization (First Move)
        {
            "activity_type": "decision",
            "title": "การจัดลำดับความสำคัญฉุกเฉิน: การปฏิบัติแรกทางการพยาบาล (Emergency Prioritization)",
            "instruction": "คุณประเสริฐรู้สึกตัวดี มีภาวะพร่องออกซิเจนรุนแรง (SpO₂ 87%) และหายใจเหนื่อยหอบอย่างหนัก การปฏิบัติการพยาบาลที่ต้องทำเป็นลำดับแรกคืออะไร?",
            "content_json": {},
            "display_order": 3,
            "options": [
                {
                    "option_key": "position_upright_and_escalate_oxygen_nrb",
                    "label": "จัดผู้ป่วยนั่งตัวตรงท่า High Fowler's (60–90°) และให้ออกซิเจนความเข้มข้นสูงทันทีผ่าน Non-Rebreather Mask (10–15 L/min) พร้อมเตรียมเครื่องดูดเสมหะ",
                    "is_correct": True,
                },
                {
                    "option_key": "immediate_deep_suction_without_oxygen",
                    "label": "รีบสอดสายดูดเสมหะลงลึกในหลอดลมทันทีโดยยังไม่ให้ออกซิเจนเสริม",
                    "is_correct": False,
                },
                {
                    "option_key": "place_supine_flat",
                    "label": "จัดผู้ป่วยนอนราบศีรษะแบน 0° เพื่อให้กล้ามเนื้อหายใจได้พักผ่อน",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "การจัดลำดับความสำคัญยอดเยี่ยม: ให้ออกซิเจนและจัดท่านั่งก่อน (Optimal Priority)",
                    "message": "การจัดท่านั่งศีรษะสูงช่วยลดแรงกดของช่องท้องต่อกะบังลม และการใส่ Non-Rebreather Mask ช่วยแก้ไขภาวะพร่องออกซิเจนที่เป็นอันตรายถึงแก่ชีวิตได้ทันที",
                    "clinical_rationale": "การดูดเสมหะในผู้ป่วยที่ขาดออกซิเจนรุนแรงโดยไม่ให้ออกซิเจนล่วงหน้าจะกระตุ้น Vagal bradycardia หรือหัวใจหยุดเต้นได้ ต้องให้ออกซิเจนและจัดท่าก่อนเสมอ",
                    "patient_effect_json": {"distress_delta": -1, "spo2_delta": 3},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "immediate_deep_suction_without_oxygen",
                    "feedback_type": "critical",
                    "title": "อันตรายจากภาวะพร่องออกซิเจนรุนแรง: การดูดเสมหะโดยไม่ให้ออกซิเจนก่อน (Hypoxemia Hazard: Suctioning Without Oxygenation)",
                    "message": "ห้ามดูดเสมหะลึกในผู้ป่วยที่มี SpO₂ 87% โดยไม่ให้ออกซิเจนล่วงหน้าเด็ดขาด! การดูดจะดึงอากาศและออกซิเจนออกจากถุงลม ทำให้ SpO₂ ตกต่ำกว่า 75% และหัวใจหยุดเต้นได้",
                    "hint": "ต้องให้ออกซิเจนล่วงหน้าและจัดท่านั่งตัวตรงเสมอก่อนสอดสายดูดเสมหะ",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "place_supine_flat",
                    "feedback_type": "critical",
                    "title": "ท่านอนอันตราย: ภาวะหายใจไม่ออกในท่านอนราบ (Dangerous Posture: Orthopnea Hazard)",
                    "message": "ท่านอนราบทำให้การออกแรงหายใจแย่ลงอย่างหนัก ปริมาตรปอดลดลงถึง 30% และเพิ่มความเสี่ยงสำลักเสมหะ",
                    "hint": "ผู้ป่วยที่มีอาการหายใจลำบากเฉียบพลันต้องอยู่ในท่านั่งศีรษะสูง High Fowler's เสมอ",
                },
            ],
        },
        # Activity 4: Safety Check: High-Flow Oxygen & Suction Setup
        {
            "activity_type": "safety_check",
            "title": "การปรับเทียบและเตรียมอุปกรณ์ฉุกเฉิน (Emergency Equipment Calibration & Setup)",
            "instruction": "เลือกการตั้งค่าและตรวจสอบความปลอดภัยที่จำเป็นทั้งหมดก่อนเริ่มดูดเสมหะและให้ออกซิเจนความเข้มข้นสูง",
            "content_json": {},
            "display_order": 4,
            "options": [
                {"option_key": "pre_inflate_nrb_bag", "label": "เปิดออกซิเจนให้ถุงสำรอง (Reservoir bag) ของ Non-Rebreather พองตัวเต็มที่ก่อนครอบลงบนใบหน้าคุณประเสริฐ", "is_correct": True},
                {"option_key": "flow_10_to_15_lpm", "label": "ตั้งอัตราการไหลที่เกจออกซิเจน 10–15 L/min เพื่อให้ถุงสำรองคงสภาพพองตัวอย่างน้อย 1/3 ถึง 1/2 ตลอดช่วงหายใจเข้า", "is_correct": True},
                {"option_key": "suction_calibrated_100_120", "label": "พับสายดูดเสมหะเพื่อทดสอบและปรับตั้งแรงดันดูดสุญญากาศให้อยู่ในช่วง 100–120 mmHg อย่างเคร่งครัด", "is_correct": True},
                {"option_key": "sterile_suction_technique", "label": "รักษาเทคนิคปลอดเชื้ออย่างเคร่งครัดโดยใช้สายดูดเสมหะและถุงมือปลอดเชื้อ", "is_correct": True},
                {"option_key": "set_nrb_flow_to_2_lpm", "label": "ตั้งอัตราการไหลของ Non-Rebreather Mask เพียง 2 L/min เพื่อป้องกันภาวะเป็นพิษจากออกซิเจน", "is_correct": False},
                {"option_key": "suction_vacuum_250_mmhg", "label": "ปรับแรงดันดูดสุญญากาศไปที่สูงสุด 250 mmHg เพื่อให้เสมหะเหนียวออกเร็วขึ้น", "is_correct": False},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ปรับตั้งอุปกรณ์ถูกต้องสมบูรณ์ (Equipment Properly Configured)",
                    "message": "ถุงสำรอง NRB พองตัวดีที่ 12 L/min (SpO2 ขยับขึ้นเป็น 91%) และตั้งแรงดันดูดเสมหะปลอดภัยที่ 110 mmHg พร้อมอุปกรณ์ปลอดเชื้อ",
                    "clinical_rationale": "อัตราการไหลสูงช่วยให้ออกซิเจนเข้มข้นเพียงพอโดยถุงไม่แฟบ และแรงดันดูด 100–120 mmHg ป้องกันการฉีกขาดของเยื่อบุหลอดลม",
                    "patient_effect_json": {"spo2_set": 91, "distress_set": 2},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "set_nrb_flow_to_2_lpm",
                    "feedback_type": "critical",
                    "title": "อันตรายจากการขาดอากาศ: ถุงสำรองแฟบ (Suffocation Hazard: Deflated Reservoir Bag)",
                    "message": "การเปิดอัตราการไหลเพียง 2 L/min บนหน้ากาก NRB จะทำให้ถุงสำรองแฟบสนิทขณะหายใจเข้า ผู้ป่วยจะสูดดมก๊าซ CO2 ซ้ำและขาดอากาศหายใจ",
                    "hint": "หน้ากากแบบ Non-Rebreather ต้องใช้อัตราการไหล 10–15 L/min เสมอเพื่อให้ถุงพองตัว",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "suction_vacuum_250_mmhg",
                    "feedback_type": "critical",
                    "title": "อันตรายจากแรงดันสุญญากาศเกินขนาด (Barotrauma Hazard: Excessive Vacuum Pressure)",
                    "message": "แรงดันดูดที่เกิน 120 mmHg จะฉีกขาดเยื่อบุทางเดินหายใจ ทำให้ถุงลมปอดแฟบ (Atelectasis) และเลือดออกในปอด",
                    "hint": "เกณฑ์ความปลอดภัยของแรงดันดูดในผู้ใหญ่คือ 100–120 mmHg",
                },
            ],
        },
        # Activity 5: Airway Clearance Procedure Sequence
        {
            "activity_type": "sequence",
            "title": "ขั้นตอนการดูดเสมหะภายใต้แนวทางดูแลภาวะพร่องออกซิเจน (Airway Suctioning Procedure)",
            "instruction": "จัดลำดับขั้นตอนการดูดเสมหะเพื่อเคลียร์ทางเดินหายใจของคุณประเสริฐอย่างปลอดภัยตามลำดับเวลา",
            "content_json": {},
            "display_order": 5,
            "steps": [
                {
                    "step_key": "step_pre_oxygenate",
                    "step_text": "ให้ออกซิเจนความเข้มข้นสูง 100% O2 ผ่านหน้ากาก NRB อย่างน้อย 30–60 วินาทีก่อนสอดสายดูดเสมหะ",
                    "correct_order": 1,
                    "rationale": "สะสมออกซิเจนสำรองในร่างกายเพื่อป้องกันภาวะออกซิเจนตกระหว่างดูดเสมหะ",
                },
                {
                    "step_key": "step_lubricate_catheter",
                    "step_text": "สวมถุงมือปลอดเชื้อและหล่อลื่นปลายสายดูดเสมหะปลอดเชื้อด้วยสารหล่อลื่นสูตรน้ำหรือน้ำเกลือปลอดเชื้อ",
                    "correct_order": 2,
                    "rationale": "ลดแรงเสียดทานและการครูดทำลายเยื่อบุขณะสอดสาย",
                },
                {
                    "step_key": "step_advance_without_suction",
                    "step_text": "ค่อยๆ สอดสายดูดเสมหะเข้าไปโดยเปิดรูควบคุมแรงดันไว้สนิท (ไม่เปิดแรงดันดูด)",
                    "correct_order": 3,
                    "rationale": "ป้องกันการดูดทำลายเยื่อบุทางเดินหายใจขณะสอดสายเข้า",
                },
                {
                    "step_key": "step_intermittent_suction_withdraw",
                    "step_text": "กดเปิดแรงดันดูดเป็นระยะ หมุนสายเบาๆ และค่อยๆ ดึงสายออกโดยใช้เวลารวมไม่เกิน 10–15 วินาที",
                    "correct_order": 4,
                    "rationale": "ดูดเสมหะได้รอบทิศทางโดยจำกัดระยะเวลาการดึงก๊าซออกจากปอด",
                },
                {
                    "step_key": "step_reapply_oxygen_evaluate",
                    "step_text": "ครอบหน้ากากออกซิเจนกลับคืนทันที แนะนำให้หายใจลึกๆ และประเมินความโล่งของทางเดินหายใจและระดับ SpO₂",
                    "correct_order": 5,
                    "rationale": "คืนการให้ออกซิเจนความเข้มข้นสูงทันทีและยืนยันประสิทธิผลของการกำจัดเสมหะ",
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "เคลียร์ทางเดินหายใจอย่างปลอดภัยสำเร็จ (Airway Cleared Safely)",
                    "message": "เสมหะเหนียวข้นปริมาณมากถูกดูดออกสำเร็จ! เสียงเสมหะเดือดในหลอดลมลดลงอย่างชัดเจน และการหายใจโล่งขึ้น",
                    "clinical_rationale": "การให้ออกซิเจนล่วงหน้าและการจำกัดเวลาดูดไม่เกิน 15 วินาทีช่วยป้องกันภาวะแทรกซ้อนจากการขาดออกซิเจนได้อย่างมีประสิทธิภาพ",
                    "patient_effect_json": {
                        "secretions": "minimal",
                        "breath_sound": "bilateral_expiratory_wheezes",
                        "spo2_set": 92,
                    },
                }
            ],
        },
        # Activity 6: Secondary Intervention: Oxygen-Driven Nebulization
        {
            "activity_type": "decision",
            "title": "การจัดการภาวะหลอดลมหดเกร็งต่อเนื่องด้วยการพ่นยา (Managing Persistent Bronchospasm)",
            "instruction": "เสมหะถูกกำจัดแล้ว แต่ฟังปอดยังได้ยินเสียงหวีดทั้งสองข้างและ SpO₂ อยู่ที่ 92% แพทย์สั่งพ่นยา Salbutamol + Ipratropium (Combivent) stat คุณควรบริหารยาพ่นนี้อย่างไร?",
            "content_json": {},
            "display_order": 6,
            "options": [
                {
                    "option_key": "nebulize_with_oxygen_source_6_8_lpm",
                    "label": "ต่อชุดพ่นยากับท่อออกซิเจนทางการแพทย์ปรับอัตราการไหล 6–8 L/min โดยใช้หน้ากากพ่นยา (Aerosol mask)",
                    "is_correct": True,
                },
                {
                    "option_key": "remove_oxygen_use_air_compressor",
                    "label": "ถอดออกซิเจนออกทั้งหมดแล้วใช้ปั๊มลมธรรมดา (Air compressor) ในอากาศห้องมาขับเคลื่อนชุดพ่นยา",
                    "is_correct": False,
                },
                {
                    "option_key": "delay_nebulizer_for_2_hours",
                    "label": "ชะลอการพ่นยาออกไปอีก 2 ชั่วโมงเพื่อให้คุณประเสริฐได้พักผ่อนหลังจากการดูดเสมหะ",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "เริ่มการพ่นยาโดยใช้ออกซิเจนเป็นก๊าซขับเคลื่อน (Aerosol Therapy Initiated on Oxygen)",
                    "message": "เริ่มพ่นยาโดยใช้ออกซิเจนทางการแพทย์ที่ 7 L/min ละอองฝอยยากำลังส่งยาขยายหลอดลมพร้อมกับรักษาระดับออกซิเจนอย่างต่อเนื่อง",
                    "clinical_rationale": "ในผู้ป่วย COPD ที่มีภาวะพร่องออกซิเจน การใช้ออกซิเจนขับเคลื่อนชุดพ่นยาช่วยรักษาทั้งหลอดลมหดเกร็งและป้องกันออกซิเจนตกไปพร้อมกัน",
                    "patient_effect_json": {"distress_set": 1},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "remove_oxygen_use_air_compressor",
                    "feedback_type": "critical",
                    "title": "อันตรายจากภาวะขาดออกซิเจนกำเริบ: การหยุดออกซิเจน (Acute Hypoxemia Hazard)",
                    "message": "การถอดออกซิเจนออกจากผู้ป่วยโรคปอดรุนแรงเพื่อใช้เครื่องอัดอากาศห้องจะทำให้เกิดภาวะพร่องออกซิเจนกำเริบรุนแรงทันที",
                    "hint": "ในภาวะหายใจลำบากเฉียบพลัน ให้ใช้ออกซิเจนทางการแพทย์ 6–8 L/min ในการขับเคลื่อนชุดพ่นยา",
                },
            ],
        },
        # Activity 7: Acute Deterioration Event (Patient Safety Alert)
        {
            "activity_type": "troubleshooting",
            "title": "เตือนภัยความปลอดภัยผู้ป่วย: อาการทรุดลงเฉียบพลันบนมอนิเตอร์ (Patient Safety Alert: Acute Monitor Deterioration)",
            "instruction": "พ่นยาไปได้ 3 นาที สัญญาณเตือนบนมอนิเตอร์ดังขึ้น: SpO₂ ร่วงลงเหลือ 85%, ชีพจรพุ่งขึ้น 122 ครั้ง/นาที และคุณประเสริฐกระสับกระส่ายดึงหน้ากากออก การปฏิบัติทันทีของคุณคืออะไร?",
            "content_json": {
                "is_emergency": True,
                "theme_color": "red",
                "alarm_badge": "CRITICAL RESCUE ALARM / อาการทรุดลงเฉียบพลัน",
                "alarm_code": "🚨 ALARM: SPO2 CRITICAL LOW (< 88%) & TACHYCARDIA",
                "image_filename": "prasert_deterioration_alarm.jpg",
                "image_alt": "คุณประเสริฐ กระสับกระส่าย ดึงหน้ากากออก และมอนิเตอร์แจ้งเตือน SpO2 85% HR 122 bpm",
                "image_overlay_text": "SpO₂ 85% | HR 122 bpm",
                "event_header": "ภาวะวิกฤตเฉียบพลันข้างเตียง (Acute Bedside Deterioration)",
                "urgent_message": "พ่นยาไปได้ 3 นาที สัญญาณเตือนบนมอนิเตอร์ดังขึ้นฉุกเฉิน: ค่า O2 saturation (SpO2) ร่วงลงเหลือ <span class='text-red-600 font-black text-xl sm:text-2xl px-2 py-0.5 rounded-md bg-red-50 border border-red-300 underline decoration-red-500'>85%</span> ชีพจรพุ่งขึ้นเป็น <span class='text-amber-600 font-black text-xl px-1.5 py-0.5 rounded-md bg-amber-50 border border-amber-300'>122 ครั้ง/นาที</span> และคุณประเสริฐเริ่มมีอาการกระสับกระส่าย มือพยายามเอื้อมดึงหน้ากากออก!",
                "scenario_description": "คุณประเสริฐหายใจหอบลึก ตาเบิกกว้างด้วยความกลัว สมองเริ่มขาดออกซิเจน (Air hunger) และเสมหะที่เหนียวข้นอาจหลุดมาขวางกั้นทางเดินหายใจ",
                "challenge_question": "ในฐานะพยาบาลผู้รับผิดชอบ การปฏิบัติการพยาบาลที่ถูกต้องและต้องทำทันทีเป็น \"ลำดับแรก (Immediate Action)\" คืออะไร?",
                "telemetry": {
                    "spo2": "85%",
                    "spo2_trend": "ร่วงลงจาก 90%",
                    "spo2_alert": True,
                    "hr": "122 bpm",
                    "hr_trend": "Severe Tachycardia",
                    "hr_alert": True,
                    "rr": "32 /min",
                    "rr_trend": "Tachypnea",
                    "rr_alert": True,
                    "patient_status": "กระสับกระส่าย / ดึงหน้ากาก",
                    "status_sub": "วิกฤตเฉียบพลัน",
                    "status_alert": True,
                },
            },
            "display_order": 7,
            "options": [
                {
                    "option_key": "assess_airway_patency_dislodged_plug_and_calm",
                    "label": "ตรวจดูการต่อสายหน้ากากทันที ตรวจดูก้อนเสมหะอุดตัน (Mucus plug) ที่ถูกละอองยาทำให้หลุดมาขวางลำคอ รีบดูดเคลียร์ช่องปาก และพูดปลอบโยนผู้ป่วยอย่างสงบ",
                    "is_correct": True,
                },
                {
                    "option_key": "administer_iv_diazepam_sedative",
                    "label": "ฉีดยาระงับประสาท Diazepam ทางหลอดเลือดดำเพื่อลดความกระสับกระส่ายให้ผู้ป่วยยอมใส่หน้ากาก",
                    "is_correct": False,
                },
                {
                    "option_key": "apply_wrist_restraints",
                    "label": "ใช้ผูกยึดข้อมือ (Restraints) กับขอบเตียงเพื่อไม่ให้ผู้ป่วยเอื้อมมือมาดึงหน้ากาก",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "กำจัดสิ่งอุดกั้นและกู้คืนความปลอดภัยสำเร็จ (Obstruction Cleared & Safety Restored)",
                    "message": "คุณพบก้อนเสมหะเหนียวข้นหลุดมาอุดกั้นบริเวณคอหอยส่วนปาก เมื่อดูดเสมหะออกและครอบหน้ากากให้กระชับ SpO2 พุ่งกลับขึ้นมาเป็น 90% ทันที!",
                    "clinical_rationale": "อาการกระสับกระส่ายในภาวะขาดออกซิเจนรุนแรงเป็นสัญญาณของสมองขาดออกซิเจน (Air hunger) การแก้ไขสาเหตุที่ทางเดินหายใจจะทำให้อาการสงบลง ห้ามให้ยาระงับประสาทเด็ดขาด",
                    "patient_effect_json": {"spo2_set": 90, "hr_set": 105, "distress_set": 2},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "administer_iv_diazepam_sedative",
                    "feedback_type": "critical",
                    "title": "ข้อผิดพลาดทางยาอันตรายถึงชีวิต: การให้ยาระงับประสาทในภาวะขาดออกซิเจน (Fatal Medication Error: Sedation in Hypoxia)",
                    "message": "ห้ามให้ยาระงับประสาทแก่ผู้ป่วยที่มีภาวะขาดออกซิเจนเด็ดขาด! เพราะจะกดศูนย์หายใจ ยับยั้งกล้ามเนื้อช่วยหายใจ และทำให้หยุดหายใจเสียชีวิตในทันที",
                    "hint": "ความกระสับกระส่ายเกิดจากสมองขาดออกซิเจน ต้องรักษาที่สาเหตุคือเคลียร์ทางเดินหายใจและให้ออกซิเจน",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "apply_wrist_restraints",
                    "feedback_type": "caution",
                    "title": "การปฏิบัติที่ไม่เหมาะสม: การผูกมัดผู้ป่วย (Inappropriate Escalation: Physical Restraints)",
                    "message": "การผูกมัดยิ่งกระตุ้นให้ผู้ป่วยตื่นตระหนกและเพิ่มความต้องการออกซิเจนของหัวใจโดยไม่ช่วยแก้ปัญหาการอุดกั้นทางเดินหายใจ",
                    "hint": "ตรวจหาและกำจัดการอุดกั้นทางกายภาพในทางเดินหายใจ",
                },
            ],
        },
        # Activity 8: Call for Help & SBAR Escalation
        {
            "activity_type": "decision",
            "title": "การขอความช่วยเหลือและการรายงานส่งต่อผู้ป่วยด้วย SBAR (Call for Help & SBAR Escalation)",
            "instruction": "เมื่อตระหนักว่าคุณประเสริฐมีพลังงานสำรองต่ำและกล้ามเนื้อหายใจเริ่มล้า คุณจึงเรียกทีมตอบสนองเร็ว (Rapid Response Team - RRT) การรายงานแบบ SBAR ข้อใดเป็นการส่งต่อทางคลินิกที่มีโครงสร้างและตรงจุดวิกฤตที่สุด?",
            "content_json": {},
            "display_order": 8,
            "options": [
                {
                    "option_key": "sbar_structured_urgent_handover",
                    "label": "S: คุณประเสริฐ ห้อง 504 มีอาการหายใจล้มเหลวและเหนื่อยล้าอย่างหนัก; B: อายุ 70 ปี โรค COPD ร่วมกับปอดอักเสบ; A: SpO₂ 90% ด้วยออกซิเจนเข้มข้นสูง หายใจ 30 ครั้ง/นาที หัวใจเต้นเร็ว เพิ่งเคลียร์ก้อนเสมหะอุดตันแต่เริ่มหมดแรง; R: ขอให้แพทย์มาประเมินข้างเตียงด่วนเพื่อพิจารณาใช้เครื่องช่วยหายใจแรงดันบวกชนิดไม่รุกล้ำ (BiPAP) หรือเตรียมใส่ท่อช่วยหายใจ",
                    "is_correct": True,
                },
                {
                    "option_key": "sbar_vague_unprioritized",
                    "label": "S: ผู้ป่วยในหอ 5 รู้สึกไม่ค่อยดี; B: มีโรคปอดเรื้อรังเดิม; A: สัญญาณชีพดูแปลกๆ เล็กน้อย; R: ถ้าตรวจคนไข้วอร์ดเสร็จช่วยแวะมาดูหน่อยนะคะ",
                    "is_correct": False,
                },
                {
                    "option_key": "leave_bedside_to_look_for_intern",
                    "label": "ทิ้งคุณประเสริฐไว้ในห้องตามลำพังแล้วเดินลงไปที่โรงอาหารเพื่อตามหาแพทย์เวรด้วยตนเอง",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "การสื่อสารส่งต่อทางคลินิกแบบ SBAR ดีเยี่ยม (Exemplary SBAR Clinical Escalation)",
                    "message": "การส่งต่อแบบ SBAR ที่ชัดเจนและตรงประเด็นช่วยระดมทีมกู้ชีพได้ทันที แพทย์และนักบำบัดระบบหายใจมาถึงข้างเตียงพร้อมเครื่อง BiPAP",
                    "clinical_rationale": "การสื่อสารที่มีโครงสร้าง (Situation, Background, Assessment, Recommendation) ช่วยให้ทีมเข้าใจสถานการณ์ตรงกันและเร่งรัดการรักษาขั้นสูงได้อย่างทันท่วงที",
                    "patient_effect_json": {"distress_set": 1},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "leave_bedside_to_look_for_intern",
                    "feedback_type": "critical",
                    "title": "อันตรายจากการละทิ้งผู้ป่วยวิกฤต (Patient Abandonment Hazard)",
                    "message": "ห้ามทิ้งผู้ป่วยที่มีอาการวิกฤตไม่คงที่ไว้ตามลำพังเด็ดขาด! ให้ใช้กริ่งฉุกเฉินข้างเตียงหรือส่งเสียงขอความช่วยเหลือจากเพื่อนร่วมงาน",
                    "hint": "อยู่ข้างเตียงผู้ป่วยเพื่อดูแลทางเดินหายใจและออกซิเจนตลอดเวลาขณะเรียกขอความช่วยเหลือ",
                },
            ],
        },
        # Activity 9: Post-Rescue Stabilization & Comprehensive Monitoring
        {
            "activity_type": "aftercare",
            "title": "การทำให้คงที่หลังกู้ชีพและการดูแลต่อเนื่อง (Post-Rescue Stabilization & Continuing Care)",
            "instruction": "เมื่อเริ่มใช้ BiPAP และพ่นยาเสร็จสิ้น อาการหายใจของคุณประเสริฐดีขึ้นและ SpO₂ แตะ 95% เลือกการพยาบาลต่อเนื่องที่สำคัญทั้งหมด",
            "content_json": {},
            "display_order": 9,
            "options": [
                {"option_key": "continuous_pulse_ox_and_telemetry", "label": "ติดเครื่องวัดออกซิเจนปลายนิ้วและคลื่นไฟฟ้าหัวใจต่อเนื่อง พร้อมตรวจนับอัตราการหายใจอย่างใกล้ชิด", "is_correct": True},
                {"option_key": "maintain_upright_fowlers", "label": "จัดท่านั่งศีรษะสูง High Fowler's ต่อไป และตรวจดูขอบหน้ากาก BiPAP ว่าแนบสนิทไม่มีลมรั่ว", "is_correct": True},
                {"option_key": "frequent_lung_auscultation", "label": "ฟังเสียงปอดทั้งสองข้างทุก 30–60 นาทีเพื่อประเมินความโล่งของทางเดินหายใจและลมเข้าปอด", "is_correct": True},
                {"option_key": "psychological_reassurance_family", "label": "พูดคุยปลอบโยนให้กำลังใจคุณประเสริฐอย่างต่อเนื่อง และอธิบายแผนการรักษาให้ครอบครัวเข้าใจ", "is_correct": True},
                {"option_key": "discontinue_all_monitoring", "label": "ถอดเครื่องมอนิเตอร์ออกทั้งหมดเพราะ SpO₂ แตะ 95% แล้วและพ้นวิกฤตแล้ว", "is_correct": False},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "การดูแลต่อเนื่องหลังกู้ชีพครอบคลุมสมบูรณ์ (Comprehensive Post-Rescue Care Established)",
                    "message": "คุณประเสริฐมีสัญญาณชีพคงที่แล้ว: SpO2 95%, อัตราหายใจ 18 ครั้ง/นาที, ชีพจร 82 ครั้ง/นาที ลมเข้าปอดทั้งสองข้างได้ดีและเสียงหวีดลดลงมาก",
                    "clinical_rationale": "ผู้ป่วยระบบหายใจที่มีความเสี่ยงสูงจำเป็นต้องได้รับการเฝ้าระวังอย่างใกล้ชิดเพราะอาจเกิดกล้ามเนื้อหายใจล้าซ้ำหรือเสมหะกลับมาอุดตันได้อีก",
                    "patient_effect_json": {
                        "spo2_set": 95,
                        "rr_set": 18,
                        "hr_set": 82,
                        "distress_set": 0,
                        "breath_sound": "bilateral_clear_improved",
                        "consciousness": "calm_resting",
                    },
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "discontinue_all_monitoring",
                    "feedback_type": "caution",
                    "title": "อันตรายจากการลดระดับการเฝ้าระวังก่อนเวลาอันควร (Premature De-escalation Hazard)",
                    "message": "ผู้ป่วยที่เพิ่งฟื้นตัวจากภาวะเกือบหยุดหายใจต้องได้รับการเฝ้าระวังผ่านมอนิเตอร์อย่างใกล้ชิด เพราะอาจเกิดการอุดกั้นซ้ำหรือกล้ามเนื้อล้าได้รวดเร็ว",
                    "hint": "คงการเฝ้าระวังผ่านมอนิเตอร์และประเมินสัญญาณชีพซ้ำเป็นระยะอย่างสม่ำเสมอ",
                },
            ],
        },
        # Activity 10: Capstone Debrief & Clinical Reflection
        {
            "activity_type": "debrief",
            "title": "สะท้อนคิดทางคลินิกและสรุปบทเรียนขั้นสูงสุด (Capstone Clinical Reflection & Debriefing)",
            "instruction": "สะท้อนคิดจากสถานการณ์กู้ชีพฉุกเฉินบูรณาการนี้: สังเคราะห์การตัดสินใจทางคลินิกของคุณเกี่ยวกับการจัดลำดับความสำคัญ การตรวจจับอาการทรุดลงเฉียบพลัน และการสื่อสารอย่างมีประสิทธิภาพ",
            "content_json": {
                "prompt": (
                    "ทบทวนการปฏิบัติการพยาบาลของคุณในการดูแลคุณประเสริฐ:\n"
                    "1. เกิดอะไรขึ้นในสถานการณ์ฉุกเฉิน และการจัดลำดับความสำคัญของคุณส่งผลต่อความปลอดภัยของผู้ป่วยอย่างไร?\n"
                    "2. เหตุใดการให้ออกซิเจนก่อนดูดเสมหะจึงมีความสำคัญยิ่งทางคลินิก?\n"
                    "3. สัญญาณเตือนทางคลินิกใดที่คุณจะเฝ้าระวังต่อไปขณะที่ผู้ป่วยฟื้นตัวด้วย BiPAP?"
                ),
            },
            "display_order": 10,
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ภารกิจสำเร็จสมบูรณ์ — ได้รับเหรียญพร้อมรับมือภาวะวิกฤต (Respiratory Ready)!",
                    "message": "ยินดีด้วยอย่างยิ่ง! คุณผ่านสถานการณ์วิกฤตระบบหายใจที่ซับซ้อนของคุณประเสริฐได้สำเร็จ และแสดงให้เห็นถึงความเชี่ยวชาญแบบบูรณาการในทักษะการพยาบาลระบบหายใจ",
                    "clinical_rationale": "ความเป็นเลิศทางคลินิกในภาวะฉุกเฉินระบบหายใจเกิดจากการประเมินสัญญาณได้เร็ว การกู้ชีพที่จัดลำดับอย่างถูกต้อง การทำหัตถการอย่างปลอดภัย และการสื่อสาร SBAR ที่มีประสิทธิภาพ",
                    "patient_effect_json": {
                        "spo2_set": 96,
                        "rr_set": 16,
                        "hr_set": 78,
                        "distress_set": 0,
                        "breath_sound": "clear_bilateral",
                        "consciousness": "comfortable_resting",
                    },
                }
            ],
        },
    ]

    # 3. Seed activities, options, procedure steps, and feedback rules
    seeded_activities_count = 0

    for act_data in ACTIVITIES_DATA:
        activity = db.session.execute(
            select(Activity).where(
                Activity.scenario_id == scenario.id,
                Activity.display_order == act_data["display_order"],
            )
        ).scalar_one_or_none()

        if not activity:
            activity = Activity(
                scenario_id=scenario.id,
                activity_type=act_data["activity_type"],
                title=act_data["title"],
                instruction=act_data["instruction"],
                content_json=act_data.get("content_json", {}),
                display_order=act_data["display_order"],
                is_active=True,
            )
            db.session.add(activity)
            db.session.flush()
            logger.info("Created Activity Room 504 order=%s (%s)", activity.display_order, activity.title)
        else:
            activity.title = act_data["title"]
            activity.instruction = act_data["instruction"]
            activity.content_json = act_data.get("content_json", {})
            activity.activity_type = act_data["activity_type"]

        # Options
        for opt_data in act_data.get("options", []):
            opt = db.session.execute(
                select(ActivityOption).where(
                    ActivityOption.activity_id == activity.id,
                    ActivityOption.option_key == opt_data["option_key"],
                )
            ).scalar_one_or_none()

            if not opt:
                opt = ActivityOption(
                    activity_id=activity.id,
                    option_key=opt_data["option_key"],
                    label=opt_data["label"],
                    description=opt_data.get("description"),
                    is_correct=opt_data["is_correct"],
                )
                db.session.add(opt)
            else:
                opt.label = opt_data["label"]
                opt.description = opt_data.get("description")
                opt.is_correct = opt_data["is_correct"]

        # Steps
        for step_data in act_data.get("steps", []):
            step = db.session.execute(
                select(ProcedureStep).where(
                    ProcedureStep.activity_id == activity.id,
                    ProcedureStep.step_key == step_data["step_key"],
                )
            ).scalar_one_or_none()

            if not step:
                step = ProcedureStep(
                    activity_id=activity.id,
                    step_key=step_data["step_key"],
                    step_text=step_data["step_text"],
                    correct_order=step_data["correct_order"],
                    rationale=step_data.get("rationale"),
                )
                db.session.add(step)
            else:
                step.step_text = step_data["step_text"]
                step.correct_order = step_data["correct_order"]
                step.rationale = step_data.get("rationale")

        # Feedback rules
        for rule_data in act_data.get("feedback_rules", []):
            rule = db.session.execute(
                select(Feedback).where(
                    Feedback.activity_id == activity.id,
                    Feedback.trigger_type == rule_data["trigger_type"],
                    Feedback.trigger_key == rule_data.get("trigger_key"),
                )
            ).scalar_one_or_none()

            if not rule:
                rule = Feedback(
                    activity_id=activity.id,
                    trigger_type=rule_data["trigger_type"],
                    trigger_key=rule_data.get("trigger_key"),
                    feedback_type=rule_data.get("feedback_type", "guidance"),
                    title=rule_data["title"],
                    message=rule_data["message"],
                    clinical_rationale=rule_data.get("clinical_rationale"),
                    hint=rule_data.get("hint"),
                    patient_effect_json=rule_data.get("patient_effect_json"),
                )
                db.session.add(rule)
            else:
                rule.title = rule_data["title"]
                rule.message = rule_data["message"]
                rule.clinical_rationale = rule_data.get("clinical_rationale")
                rule.hint = rule_data.get("hint")
                rule.patient_effect_json = rule_data.get("patient_effect_json")

        seeded_activities_count += 1

    # 4. Create badge: respiratory-ready
    badge = db.session.execute(
        select(Badge).where(Badge.slug == "respiratory-ready")
    ).scalar_one_or_none()

    if not badge:
        badge = Badge(
            mission_id=mission.id,
            slug="respiratory-ready",
            name="พร้อมรับมือภาวะวิกฤต (Respiratory Ready)",
            description="บูรณาการทักษะการตัดสินใจทางคลินิก การจัดลำดับความสำคัญ และการส่งต่อผู้ป่วย SBAR ในสถานการณ์กู้ชีพฉุกเฉินระบบหายใจ",
            icon="rescue",
        )
        db.session.add(badge)
        logger.info("Created Badge 'พร้อมรับมือภาวะวิกฤต (Respiratory Ready)' for Room 504")
    else:
        badge.mission_id = mission.id
        badge.name = "พร้อมรับมือภาวะวิกฤต (Respiratory Ready)"
        badge.description = "บูรณาการทักษะการตัดสินใจทางคลินิก การจัดลำดับความสำคัญ และการส่งต่อผู้ป่วย SBAR ในสถานการณ์กู้ชีพฉุกเฉินระบบหายใจ"
        badge.icon = "rescue"

    db.session.commit()
    logger.info("Seeded Room 504 with %s activities and badge successfully.", seeded_activities_count)
    return {"activities": seeded_activities_count}
