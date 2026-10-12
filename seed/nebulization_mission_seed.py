"""Complete seed content for Room 503: Open the Airway (Nebulization Mission).

Idempotent: creates or updates scenario, 10 activities, options, procedure steps,
feedback rules, and the 'Nebulizer Navigator' badge.
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


def seed_nebulization_mission() -> dict[str, int]:
    """Seed Room 503 scenario, activities, options, steps, feedback, and badge."""
    mission = db.session.execute(
        select(Mission).where((Mission.room_number == "503") | (Mission.slug == "open-the-airway"))
    ).scalar_one_or_none()

    if not mission:
        logger.warning("Room 503 mission not found. Run seed_rooms() first.")
        return {"scenario": 0, "activities": 0}

    # Update Room 503 availability to playable
    mission.availability = "playable"

    # 1. Create or update Scenario
    scenario = db.session.execute(
        select(Scenario).where(Scenario.mission_id == mission.id)
    ).scalar_one_or_none()

    initial_vitals = {
        "spo2": 93,
        "rr": 24,
        "hr": 92,
        "distress": 2,
        "secretions": "minimal",
        "breath_sound": "expiratory_wheezing",
        "consciousness": "alert_anxious",
    }

    scenario_title = "การพ่นยาขยายหลอดลมสำหรับคุณมะลิ (Bronchodilator Nebulization for Ms. Mali)"
    patient_name = "นางมะลิ (Ms. Mali)"
    clinical_summary = (
        "นางมะลิ อายุ 55 ปี มาด้วยโรคหอบหืดกำเริบเฉียบพลัน (Acute Asthma Exacerbation) "
        "บ่นแน่นหน้าอก หายใจไม่อิ่ม และมีเสียงหวีดในหลอดลม "
        "มอนิเตอร์ข้างเตียงแสดง SpO2 93%, อัตราการหายใจ 24 ครั้ง/นาที, ชีพจร 92 ครั้ง/นาที "
        "ฟังปอดได้ยินเสียง expiratory wheezes ทั้งสองข้าง แพทย์สั่งพ่นยา Salbutamol 2.5 มก. stat"
    )

    if not scenario:
        scenario = Scenario(
            mission_id=mission.id,
            title=scenario_title,
            patient_name=patient_name,
            patient_age=55,
            patient_gender="หญิง",
            clinical_summary=clinical_summary,
            initial_state_json=initial_vitals,
            difficulty="intermediate",
            is_active=True,
        )
        db.session.add(scenario)
        db.session.flush()
        logger.info("Created Scenario for Room 503 id=%s", scenario.id)
    else:
        scenario.title = scenario_title
        scenario.patient_name = patient_name
        scenario.patient_age = 55
        scenario.patient_gender = "หญิง"
        scenario.clinical_summary = clinical_summary
        scenario.initial_state_json = initial_vitals
        scenario.is_active = True

    # 2. Activities Data (10 activities)
    ACTIVITIES_DATA = [
        # Activity 1: Intro / Meet Patient
        {
            "activity_type": "intro",
            "title": "พบคุณมะลิ (Meet Ms. Mali) & ข้อมูลผู้ป่วย",
            "instruction": "ทบทวนข้อมูลผู้ป่วย บริบททางคลินิก และสัญญาณชีพระดับฐานบนจอมอนิเตอร์ข้างเตียง",
            "content_json": {
                "patient_name": "นางมะลิ (Ms. Mali, 55 ปี)",
                "context": (
                    "นางมะลิมีประวัติเป็นโรคหอบหืด (Bronchial Asthma) มาด้วยอาการหายใจลำบากมากขึ้น "
                    "แน่นหน้าอก และได้ยินเสียงหายใจวี้ดชัดเจน แพทย์สั่งยาพ่น Salbutamol (Albuterol) 2.5 มก. / 2.5 มล. "
                    "ผ่านชุดพ่นยาแบบ Jet Nebulizer stat"
                ),
                "goal": "ตรวจสอบคำสั่งการใช้ยา ประกอบชุดพ่นยา แนะนำเทคนิคการหายใจที่ถูกต้อง แก้ไขปัญหาการพ่นยา และติดตามผลการตอบสนองต่อยาขยายหลอดลม",
            },
            "display_order": 1,
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ทบทวนข้อมูลผู้ป่วยเรียบร้อย (Clinical Briefing Reviewed)",
                    "message": "เริ่มการประเมินระบบหายใจเพื่อระบุสัญญาณทางคลินิกทั้งหมดของภาวะหลอดลมหดเกร็งเฉียบพลัน",
                    "clinical_rationale": "การตรวจพบภาวะหลอดลมหดเกร็งเฉียบพลันได้อย่างรวดเร็วช่วยให้บริหารยาขยายหลอดลมกลุ่ม SABA ได้ทันท่วงที",
                }
            ],
        },
        # Activity 2: Clinical Cues
        {
            "activity_type": "clinical_cues",
            "title": "ประเมินสัญญาณหลอดลมหดเกร็งเฉียบพลัน (Identify Cues of Acute Bronchospasm)",
            "instruction": "เลือกข้อค้นพบจากการตรวจประเมินทางคลินิกทั้งหมดที่บ่งชี้ถึงภาวะหลอดลมหดเกร็งเฉียบพลันและความจำเป็นต้องพ่นยาขยายหลอดลม",
            "content_json": {},
            "display_order": 2,
            "options": [
                {"option_key": "expiratory_wheezing", "label": "ฟังปอดได้ยินเสียงหวีดช่วงหายใจออกทั้งสองข้าง (Bilateral expiratory wheezing)", "is_correct": True},
                {"option_key": "high_fever_39c", "label": "มีไข้สูง 39.5°C", "is_correct": False},
                {"option_key": "chest_tightness", "label": "รู้สึกแน่นหน้าอก หายใจไม่อิ่ม และเหนื่อยหอบ", "is_correct": True},
                {"option_key": "bounding_peripheral_pulses", "label": "ชีพจรส่วนปลายเต้นแรงผิดปกติ (+4)", "is_correct": False},
                {"option_key": "tachypnea_rr24", "label": "หายใจเร็ว (อัตราการหายใจ 24 ครั้ง/นาที ร่วมกับช่วงหายใจออกยาวนานขึ้น)", "is_correct": True},
                {"option_key": "mild_hypoxemia_93", "label": "SpO₂ 93% ในอากาศห้อง บ่งชี้ถึงภาวะการระบายอากาศและการไหลเวียนเลือดไม่สมดุล (V/Q mismatch)", "is_correct": True},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ระบุสัญญาณหลอดลมหดเกร็งถูกต้อง (Accurate Bronchospasm Cue Recognition)",
                    "message": "คุณระบุสัญญาณสำคัญของหลอดลมหดเกร็งได้อย่างถูกต้อง: เสียงหวีดช่วงหายใจออก แน่นหน้าอก หายใจเร็ว และ SpO2 93%",
                    "clinical_rationale": "การหดเกร็งของกล้ามเนื้อเรียบหลอดลมส่วนล่างเพิ่มแรงต้านทานช่วงหายใจออก ทำให้เกิดเสียงหวีดสูง (Wheezing)",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "high_fever_39c",
                    "feedback_type": "guidance",
                    "title": "อาการที่ไม่ใช่อาการจำเพาะของหอบหืด (Atypical Asthma Finding)",
                    "message": "คุณมะลิไม่มีไข้ แม้การติดเชื้ออาจกระตุ้นหอบหืดได้ แต่ไข้สูงไม่ใช่สัญญาณโดยตรงของหลอดลมหดเกร็ง",
                    "hint": "เน้นการอุดกั้นของการไหลเวียนอากาศและเสียงผิดปกติจากการฟังปอด",
                },
            ],
        },
        # Activity 3: Medication Check (10 Rights)
        {
            "activity_type": "medication_check",
            "title": "ตรวจสอบคำสั่งการใช้ยาและความปลอดภัยตามหลัก 10 Rights (Medication Order & 10 Rights Verification)",
            "instruction": "ตรวจสอบคำสั่งแพทย์: 'Salbutamol 2.5 มก. / 2.5 มล. via nebulizer stat' และเลือกการตรวจสอบความปลอดภัยตามหลัก 10 Rights ในการบริหารยาที่ถูกต้องและจำเป็นทั้งหมด",
            "content_json": {
                "doctor_order": {
                    "patient_name": "นางมะลิ สุขใจ",
                    "age": "55 ปี",
                    "hn": "67-08421",
                    "ward_bed": "Ward 5 เตียง 503",
                    "diagnosis": "Acute Asthmatic Attack (หอบหืดกำเริบเฉียบพลัน)",
                    "rx_order": "Salbutamol (Ventolin) nebules 2.5 mg / 2.5 mL via pneumatic jet nebulizer stat",
                    "indication": "บรรเทาหลอดลมหดเกร็งเฉียบพลัน (Acute bronchospasm) และเสียง Expiratory wheezing",
                    "allergy": "ปฏิเสธประวัติแพ้ยาและสารเคมี (NKDA)",
                },
                "rights_count": 10,
                "banner_title": "หลัก 10 Rights ในการบริหารยาทางคลินิก (The 10 Rights of Medication Administration)",
            },
            "display_order": 3,
            "options": [
                {"option_key": "right_patient_mali", "label": "ตรวจสอบชื่อ-นามสกุล และดูป้ายข้อมือของคุณมะลิให้ตรงกับคำสั่งการรักษา", "is_correct": True},
                {"option_key": "right_drug_salbutamol", "label": "ยืนยันชื่อยา Salbutamol (Ventolin) ว่าเป็นยาขยายหลอดลมกลุ่มออกฤทธิ์เร็ว (SABA)", "is_correct": True},
                {"option_key": "right_dose_2_5mg", "label": "ตรวจสอบขนาดยา 2.5 มก. ในหลอดยูนิตโดสปลอดเชื้อขนาด 2.5 มล. ตามคำสั่งแพทย์", "is_correct": True},
                {"option_key": "dilute_with_distilled_water", "label": "เจือจางหลอดยาด้วยน้ำกลั่น 5 มล. ก่อนนำไปพ่น", "is_correct": False},
                {"option_key": "right_time_stat", "label": "ยืนยันเวลาการให้ยาทันที (Stat dose) ตามความเร่งด่วนของอาการหอบเหนื่อย", "is_correct": True},
                {"option_key": "right_reason_indication", "label": "ตรวจสอบข้อบ่งชี้ของยาสำหรับบรรเทาหลอดลมหดเกร็งเฉียบพลันและเสียง Wheezing", "is_correct": True},
                {"option_key": "administer_iv_push", "label": "เปลี่ยนวิถีทางยาเป็นการฉีดเข้าทางหลอดเลือดดำ (IV Push) โดยตรงเพื่อให้ออกฤทธิ์เร็วขึ้น", "is_correct": False},
                {"option_key": "right_route_inhalation", "label": "ยืนยันวิถีทางการให้ยาเป็นการสูดดมพ่นละอองผ่านเครื่องพ่นยา (Pneumatic Jet Nebulizer)", "is_correct": True},
                {"option_key": "check_expiry_and_clarity", "label": "ตรวจสอบวันหมดอายุบนหลอดยา สภาพหลอดยา และความใสไม่มีสีของสารละลาย", "is_correct": True},
                {"option_key": "right_assessment_evaluation", "label": "ซักประวัติแพ้ยา ประเมินเสียงปอดและชีพจรก่อนให้ และเตรียมประเมินผลการตอบสนองหลังพ่นยา", "is_correct": True},
                {"option_key": "right_education_patient", "label": "อธิบายขั้นตอนการสูดพ่นละอองยา เฝ้าระวังผลข้างเคียง (ใจสั่น มือสั่น) และเปิดโอกาสให้ผู้ป่วยซักถาม", "is_correct": True},
                {"option_key": "right_documentation", "label": "เตรียมบันทึกชื่อยา ขนาดยา วิถีทาง เวลา และการตอบสนองของผู้ป่วยในบันทึกทางการพยาบาลทันทีหลังพ่นยา", "is_correct": True},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ตรวจสอบหลัก 10 Rights ถูกต้องครบถ้วน (Medication 10 Rights Fully Verified)",
                    "message": "ยอดเยี่ยม! คุณได้ตรวจสอบความปลอดภัยตามหลัก 10 Rights ในการบริหารยาครบถ้วนทุกประการ: ตรวจสอบผู้ป่วย, ชื่อยา, ขนาด 2.5 มก., วิถีทางพ่นละออง, เวลา Stat, วันหมดอายุ/ความใส, ข้อบ่งชี้, การประเมินก่อน-หลังให้ยา, การให้ข้อมูลผู้ป่วย และการเตรียมบันทึกทางการพยาบาล",
                    "clinical_rationale": "การยึดมั่นในหลัก 10 Rights ช่วยป้องกันความคลาดเคลื่อนทางยา (Medication Error) ได้อย่างสมบูรณ์ และรับรองว่าผู้ป่วยจะได้รับยาขยายหลอดลมที่ปลอดภัยและมีประสิทธิภาพสูงสุด",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "dilute_with_distilled_water",
                    "feedback_type": "critical",
                    "title": "ข้อห้าม: การเจือจางยาพ่นด้วยน้ำกลั่น (Hazard: Inhalation of Hypotonic Sterile Water)",
                    "message": "ห้ามเจือจางยาพ่นด้วยน้ำกลั่นเด็ดขาด! การสูดพ่นละอองน้ำกลั่นซึ่งมีความดันออสโมลาริตีต่ำ (Hypotonic aerosol) จะระคายเคืองเยื่อบุทางเดินหายใจและกระตุ้นให้หลอดลมหดเกร็ง (Bronchospasm) รุนแรงขึ้น อีกทั้งหลอดยา Salbutamol Respule เป็นสารละลายไอโซโทนิก (Isotonic) 2.5 มล. พร้อมใช้ ไม่จำเป็นต้องเจือจางเพิ่ม",
                    "hint": "หลอดยา Respule แบบยูนิตโดสมีปริมาตรมาตรฐานพร้อมพ่นอยู่แล้ว หากจำเป็นต้องเจือจางยาอื่นจะใช้ 0.9% Normal Saline Solution (NSS) เท่านั้น ห้ามใช้น้ำกลั่น",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "administer_iv_push",
                    "feedback_type": "critical",
                    "title": "อันตรายจากการให้ยาผิดวิถีทาง (Wrong Route Hazard)",
                    "message": "ห้ามนำยาพ่น Salbutamol Respule มาฉีดเข้าหลอดเลือดดำ (IV)! สารละลายสำหรับพ่นไม่ได้เตรียมมาสำหรับการฉีด IV และคำสั่งแพทย์ระบุชัดเจนว่าให้สูดดมทางเครื่องพ่นยา (Nebulizer)",
                    "hint": "ตรวจสอบวิถีทางยา (Right Route) ให้ตรงกับคำสั่งการรักษาเสมอ",
                },
            ],
        },
        # Activity 4: Sequence (Circuit Assembly)
        {
            "activity_type": "sequence",
            "title": "จัดลำดับขั้นตอนการประกอบชุดพ่นยา (Nebulizer Circuit Assembly Sequence)",
            "instruction": "จัดลำดับขั้นตอนการประกอบและเตรียมชุดพ่นละอองยาให้ถูกต้องตามลำดับ",
            "content_json": {},
            "display_order": 4,
            "steps": [
                {
                    "step_key": "step_inspect_parts",
                    "step_text": "ตรวจความสะอาดของกระเปาะใส่ยา, ฝาเกลียวพร้อมเดือยกระจายละออง (Baffle) ด้านใน, ข้อต่อรูปตัว T และกระบอกสูดยา (Mouthpiece)",
                    "correct_order": 1,
                    "rationale": "มั่นใจว่าอุปกรณ์สะอาดสมบูรณ์และมีแกน Baffle อยู่ด้านในเพื่อสร้างละอองยาขนาดละเอียด",
                },
                {
                    "step_key": "step_instill_salbutamol",
                    "step_text": "บิดเปิดหลอดยา Salbutamol ปลอดเชื้อ และเทสารละลายยาทั้งหมด 2.5 มล. ลงในกระเปาะใส่ยา",
                    "correct_order": 2,
                    "rationale": "ใส่ยาลงในกระเปาะก่อนปิดฝาห้องผลิตละอองยา",
                },
                {
                    "step_key": "step_seal_cup",
                    "step_text": "หมุนปิดฝากระเปาะพ่นยาให้แน่นหนา โดยตั้งกระเปาะให้ตรงเสมอเพื่อไม่ให้ยารั่วหก",
                    "correct_order": 3,
                    "rationale": "ปิดผนึกห้องสร้างละอองยาและจัดหัวเจ็ทภายในให้อยู่ในแนวที่ถูกต้อง",
                },
                {
                    "step_key": "step_attach_mouthpiece",
                    "step_text": "ต่อกระบอกสูบทางปาก (Mouthpiece) และท่อรวงผึ้งสำรอง (Reservoir tubing) เข้ากับปลายด้านบนของข้อต่อรูปตัว T",
                    "correct_order": 4,
                    "rationale": "Mouthpiece ช่วยส่งละอองยาข้ามโพรงจมูกเข้าสู่ปอดโดยตรง ส่วนท่อ reservoir ช่วยกักเก็บละอองยาขณะหายใจออก",
                },
                {
                    "step_key": "step_connect_tubing_source",
                    "step_text": "ต่อสายนำก๊าซจากก้นกระเปาะพ่นยาเข้ากับช่องต่อของเกจวัดอัตราการไหล (Flowmeter)",
                    "correct_order": 5,
                    "rationale": "เชื่อมต่อวงจรก๊าซจากแหล่งกำเนิดแรงดันเข้าสู่ชุดพ่นยาของผู้ป่วยอย่างสมบูรณ์",
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ประกอบชุดพ่นยาถูกต้องสมบูรณ์ (Circuit Assembled Correctly)",
                    "message": "ชุดพ่นยาประกอบเสร็จเรียบร้อย ตั้งตรง มียาพร้อม และต่อสายนำก๊าซแน่นหนา",
                    "clinical_rationale": "การประกอบวงจรที่ถูกต้องป้องกันการรั่วซึมของละอองยาและช่วยให้อนุภาคละอองยามีขนาดตามหลักพลศาสตร์ที่เหมาะสม",
                }
            ],
        },
        # Activity 5: Safety Check (Positioning & Flow Rate)
        {
            "activity_type": "safety_check",
            "title": "การจัดท่าผู้ป่วยและการปรับอัตราการไหลของก๊าซ (Patient Positioning & Flow Calibration)",
            "instruction": "เลือกการตั้งค่าและการจัดท่าที่จำเป็นเพื่อเพิ่มประสิทธิภาพการรับละอองยาและการขยายตัวของปอด",
            "content_json": {},
            "display_order": 5,
            "options": [
                {"option_key": "high_fowlers_position", "label": "จัดคุณมะลินั่งในท่าศีรษะสูง High Fowler's (นั่งตัวตรง 60–90°)", "is_correct": True},
                {"option_key": "flow_rate_2_lpm", "label": "ตั้งอัตราการไหลเพียง 2 L/min เพื่อประหยัดออกซิเจน", "is_correct": False},
                {"option_key": "keep_cup_vertical", "label": "แนะนำให้ผู้ป่วยถือก้นกระเปาะพ่นยาให้ตั้งตรงตลอดระยะเวลาการพ่นยา", "is_correct": True},
                {"option_key": "supine_flat_bed", "label": "จัดผู้ป่วยนอนราบศีรษะราบ 0° ขณะพ่นยา", "is_correct": False},
                {"option_key": "flow_rate_6_to_8_lpm", "label": "ปรับอัตราการไหลของออกซิเจน/อากาศที่เกจ flowmeter ที่ 6–8 L/min เพื่อสร้างละอองฝอยละเอียด (1–5 µm)", "is_correct": True},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "สร้างพลศาสตร์ละอองยาที่เหมาะสมที่สุด (Optimal Aerosol Dynamics Established)",
                    "message": "คุณมะลินั่งตัวตรงสบาย และตั้งอัตราการไหลที่ 7 L/min ท่าทางนั่งตรงช่วยให้กะบังลมหย่อนตัวและปอดขยายตัวได้เต็มที่",
                    "clinical_rationale": "อัตราการไหล 6–8 L/min สร้างขนาดอนุภาคละอองยาที่ 1–5 ไมครอน ซึ่งเป็นขนาดที่เหมาะสมที่สุดในการลงสู่หลอดลมฝอยส่วนลึก",
                    "patient_effect_json": {"distress_delta": -1},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "flow_rate_2_lpm",
                    "feedback_type": "caution",
                    "title": "อัตราการไหลต่ำเกินไปจนไม่ได้ผล (Ineffective Flow Rate)",
                    "message": "อัตราการไหลต่ำกว่า 6 L/min จะสร้างอนุภาคละอองขนาดใหญ่ (>10 ไมครอน) ซึ่งจะตกค้างที่ช่องปากและคอหอยโดยไม่สามารถลงสู่หลอดลมส่วนล่างได้",
                    "hint": "Jet nebulizer ต้องใช้อัตราการไหล 6–8 L/min เพื่อสร้างละอองยาในระดับที่สูดเข้าปอดได้",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "supine_flat_bed",
                    "feedback_type": "caution",
                    "title": "ท่าทางไม่เหมาะสม (Suboptimal Positioning)",
                    "message": "ท่านอนราบทำให้ปริมาตรปอดลดลงถึง 30% และทำให้กระเปาะยาเอียงจนไม่สามารถสร้างละอองยาได้",
                    "hint": "จัดผู้ป่วยนั่งตัวตรงในท่า High Fowler's เสมอ",
                },
            ],
        },
        # Activity 6: Troubleshooting ("Why No Mist?")
        {
            "activity_type": "troubleshooting",
            "title": "แก้ปัญหาชุดพ่นยา: 'ทำไมละอองยาไม่ออก?' (Why No Mist?)",
            "instruction": "เปิดเกจวัดอัตราการไหลไปที่ 7 L/min แล้ว แต่ไม่มีละอองยาพ่นออกมาจาก Mouthpiece เลือกการตรวจสอบและแก้ไขปัญหาที่จำเป็น (เลือก 2 ข้อ)",
            "content_json": {},
            "display_order": 6,
            "options": [
                {
                    "option_key": "crank_to_15l",
                    "label": "เร่งเกจวัดอัตราการไหลขึ้นไปสูงสุด 15 L/min เพื่อให้ยาออกมากขึ้น",
                    "is_correct": False,
                },
                {
                    "option_key": "check_tubing_and_cup_orientation",
                    "label": "ตรวจการเชื่อมต่อของสายนำก๊าซที่เกจและก้นกระเปาะว่าหลวมหรือไม่ และตรวจว่ากระเปาะตั้งตรงหรือไม่",
                    "is_correct": True,
                },
                {
                    "option_key": "check_liquid_below_baffle",
                    "label": "ตรวจดูว่ายาพ่นอยู่ในตำแหน่งใต้แกน baffle หรือไม่",
                    "is_correct": True,
                },
                {
                    "option_key": "give_oral_tablet",
                    "label": "ทิ้งชุดพ่นยานี้แล้วเปลี่ยนไปให้ยารับประทาน Salbutamol ชนิดเม็ดแทน",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "แก้ไขปัญหาละอองยากลับมาพ่นได้ทันที (Mist Restored Promptly)",
                    "message": "ยอดเยี่ยมมาก! คุณตรวจข้อต่อสายนำก๊าซให้แน่นหนา พร้อมทั้งตรวจเช็กตำแหน่งแกน baffle และระดับยา ละอองฝอยยาก็พุ่งออกมาอย่างสม่ำเสมอทันที!",
                    "clinical_rationale": "ข้อต่อที่หลวมทำให้ก๊าซรั่วออก และตำแหน่งของยา/แกน baffle มีผลโดยตรงต่อการสร้างแรงดันสุญญากาศแบบ venturi ภายในกระเปาะยา",
                    "patient_effect_json": {"distress_delta": -1},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "crank_to_15l",
                    "feedback_type": "caution",
                    "title": "อันตรายจากการเพิ่มอัตราการไหลสูงเกินไป (Excessive Gas Flow Hazard)",
                    "message": "การเร่งเกจวัดอัตราการไหลขึ้นไป 15 L/min ไม่ได้แก้ปัญหาสายหลวมหรือกระเปาะเอียง และอัตราการไหลที่สูงเกิน 8 L/min จะทำให้ละอองยามีขนาดเล็กเกินไป พ่นยาหมดเร็วเกินควร และยาพุ่งกระทบผนังคอหอยมากกว่าลงสู่ปอด",
                    "hint": "อัตราการไหลที่เหมาะสมสำหรับ Jet Nebulizer คือ 6–8 L/min ให้ตรวจดูข้อต่อสายนำก๊าซและแกน baffle ก่อน",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "give_oral_tablet",
                    "feedback_type": "guidance",
                    "title": "การรักษาล่าช้า (Delayed Clinical Action)",
                    "message": "ยาขยายหลอดลมชนิดรับประทานต้องใช้เวลา 30–60 นาทีจึงจะเริ่มออกฤทธิ์และมีผลข้างเคียงทั่วร่างกายมาก ขณะที่ยาพ่นออกฤทธิ์ใน 3–5 นาทีและเป็นการรักษาหลักในภาวะเฉียบพลัน",
                    "hint": "แก้ไขปัญหาอุปกรณ์ก่อนตัดสินใจละทิ้งวิถีทางยาที่แพทย์สั่ง",
                },
            ],
        },
        # Activity 7: Decision (Nebulization End-point & Sputtering Management)
        {
            "activity_type": "decision",
            "title": "การสังเกตจุดสิ้นสุดของการพ่นยา (Recognizing End of Nebulization & Sputtering)",
            "instruction": "เมื่อพ่นยาไปได้ประมาณ 10–12 นาที เริ่มได้ยินเสียงฟู่ขาดๆ หายๆ (Sputtering) และละอองยาเริ่มไม่ออก การปฏิบัติทางการพยาบาลที่ถูกต้องคืออะไร?",
            "content_json": {},
            "display_order": 7,
            "options": [
                {
                    "option_key": "tap_cup_and_finish_mist",
                    "label": "เคาะข้างกระเปาะยาเบาๆ เพื่อให้ละอองยาที่เกาะผนังตกลงก้นกระเปาะ และพ่นต่อจนกระทั่งไม่มีละอองยาออกมาอีกจึงปิดเกจ",
                    "is_correct": True,
                },
                {
                    "option_key": "add_more_nss_immediately",
                    "label": "เปิดฝากระเปาะแล้วเติมน้ำเกลือ 0.9% NSS เพิ่มอีก 5 มล. ทันทีเพื่อให้พ่นยาต่อได้นานขึ้น",
                    "is_correct": False,
                },
                {
                    "option_key": "stop_immediately_on_first_sputter",
                    "label": "รีบปิดเกจวัดอัตราการไหลและยุติการพ่นยาทันทีที่ได้ยินเสียงฟู่ครั้งแรก โดยไม่ต้องตรวจดูปริมาณยาที่เหลือ",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "บริหารยาได้ครบถ้วนตามขนาดยา (Complete Medication Delivery)",
                    "message": "ถูกต้องมาก! การเคาะกระเปาะยาเบาๆ ช่วยให้ยาที่ติดค้างตามผนังไหลลงสู่ก้นกระเปาะเพื่อสร้างละอองยาจนหมด ทำให้คุณมะลิได้รับขนาดยาครบถ้วนตามแผนการรักษา",
                    "clinical_rationale": "เมื่อยาใกล้หมดจะมีเสียง sputtering เกิดขึ้น การเคาะกระเปาะช่วยลด Dead volume (ปริมาตรยาตกค้าง) และให้พ่นต่อจนไม่มีละอองยาออกมาอีก (ประมาณ 10–15 นาที)",
                    "patient_effect_json": {"spo2_set": 95, "rr_set": 20},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "add_more_nss_immediately",
                    "feedback_type": "caution",
                    "title": "การเจือจางยาเกินความจำเป็น (Inappropriate Fluid Overdilution)",
                    "message": "การเติม NSS เพิ่มหลังจากพ่นยาใกล้หมดไม่ได้ช่วยเพิ่มปริมาณตัวยาสำคัญ และทำให้ต้องใช้เวลาพ่นยานานเกินไปจนผู้ป่วยเหนื่อยล้าโดยไม่เกิดประโยชน์ทางคลินิก",
                    "hint": "พ่นยาเฉพาะขนาดและปริมาตรที่กำหนดไว้ในคำสั่งการรักษาจนยาหมด ไม่เติมสารน้ำซ้ำซ้อน",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "stop_immediately_on_first_sputter",
                    "feedback_type": "guidance",
                    "title": "ผู้ป่วยอาจได้รับยาไม่ครบขนาด (Underdose Risk)",
                    "message": "เสียงฟู่ครั้งแรกมักเกิดจากตัวยาเริ่มพร่อง แต่ยังมียาเกาะอยู่ตามผนังกระเปาะ การเคาะเบาๆ จะช่วยให้พ่นยาต่อได้อีก 1–2 นาทีจนยาหมดจริง",
                    "hint": "เคาะข้างกระเปาะยาเบาๆ เพื่อให้ยาตกลงก้นกระเปาะและพ่นต่อจนละอองยาหมดสนิท",
                },
            ],
        },
        # Activity 8: Troubleshooting / Decision (Adverse Effects Challenge)
        {
            "activity_type": "troubleshooting",
            "title": "เฝ้าระวังมอนิเตอร์: ตรวจจับอาการไม่พึงประสงค์จากยา (Adverse Effect Recognition)",
            "instruction": "หลังจากพ่นยาไปได้ 5 นาที สัญญาณเตือนบนมอนิเตอร์ดังขึ้น: ชีพจรเพิ่มขึ้นเป็น 114 ครั้ง/นาที และคุณมะลิบ่นมือสั่นเล็กน้อยและใจสั่น การปฏิบัติของคุณคืออะไร?",
            "content_json": {},
            "display_order": 8,
            "options": [
                {
                    "option_key": "reassure_and_monitor_expected_saba_effects",
                    "label": "อธิบายให้คุณมะลิคลายกังวลว่าอาการมือสั่นและใจสั่นเล็กน้อยเป็นผลข้างเคียงชั่วคราวที่พบได้ตามปกติของ Salbutamol และเฝ้าระวังสัญญาณชีพต่อเนื่อง",
                    "is_correct": True,
                },
                {
                    "option_key": "give_iv_beta_blocker",
                    "label": "หยุดพ่นยาทันทีและรีบฉีดยา Propranolol (Beta-blocker) ทางหลอดเลือดดำเพื่อลดอัตราการเต้นของหัวใจ",
                    "is_correct": False,
                },
                {
                    "option_key": "call_code_blue_arrest",
                    "label": "กดประกาศภาวะหัวใจหยุดเต้น (Code Blue) ทันที",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "การประเมินทางเภสัชวิทยาถูกต้องแม่นยำ (Accurate Pharmacological Assessment)",
                    "message": "คุณให้ข้อมูลอย่างใจเย็นทำให้คุณมะลิคลายกังวล และสามารถพ่นยาจนครบได้อย่างปลอดภัย อัตราการเต้นของหัวใจเริ่มลดลงเมื่ออาการหลอดลมหดเกร็งคลี่คลาย",
                    "clinical_rationale": "Salbutamol กระตุ้นตัวรับ Beta-2 ในหลอดลม แต่การดูดซึมเข้าสู่กระแสเลือดทำให้เกิดการกระตุ้น Beta-1 เล็กน้อยและหลอดเลือดส่วนปลายขยายตัว ส่งผลให้หัวใจเต้นเร็วและมือสั่น ซึ่งเป็นผลข้างเคียงชั่วคราวที่คาดหมายได้",
                    "patient_effect_json": {"hr_set": 102, "distress_set": 1},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "give_iv_beta_blocker",
                    "feedback_type": "critical",
                    "title": "ข้อห้ามใช้ยาที่เป็นอันตรายถึงชีวิต (Lethal Medication Contraindication)",
                    "message": "ห้ามให้ยา Non-selective beta-blocker แก่ผู้ป่วยโรคหอบหืดเด็ดขาด! เพราะการปิดกั้นตัวรับ Beta-2 จะกระตุ้นให้หลอดลมหดเกร็งอย่างรุนแรงและเป็นอันตรายถึงแก่ชีวิต",
                    "hint": "Beta-blocker เป็นข้อห้ามใช้เด็ดขาดในผู้ป่วยที่มีภาวะหลอดลมไวเกินหรือโรคหอบหืด",
                },
            ],
        },
        # Activity 9: Aftercare (Post-Care & Lung Auscultation)
        {
            "activity_type": "aftercare",
            "title": "การดูแลและฟังเสียงปอดหลังพ่นยา (Post-Nebulization Care & Auscultation)",
            "instruction": "เลือกการปฏิบัติการพยาบาลที่จำเป็นทั้งหมดหลังเสร็จสิ้นการพ่นยา",
            "content_json": {},
            "display_order": 9,
            "options": [
                {"option_key": "reauscultate_bilateral_lungs", "label": "ฟังเสียงหายใจในปอดทั้งสองข้างเพื่อประเมินการตอบสนองต่อยาขยายหลอดลม", "is_correct": True},
                {"option_key": "soak_cup_in_bleach", "label": "แช่กระเปาะพ่นยาในน้ำยาฟอกขาว (Bleach) เข้มข้นหลังใช้งาน", "is_correct": False},
                {"option_key": "rinse_mouth_spit", "label": "ให้ผู้ป่วยบ้วนปากด้วยน้ำสะอาดแล้วบ้วนทิ้งเพื่อลดการดูดซึมยาตกค้างในช่องปาก", "is_correct": True},
                {"option_key": "rinse_and_air_dry_cup", "label": "ถอดแยกชิ้นส่วนกระเปาะยา ล้างด้วยน้ำกลั่น/น้ำปลอดเชื้อ และคว่ำผึ่งลมบนผ้าสะอาด", "is_correct": True},
                {"option_key": "document_response", "label": "บันทึกสัญญาณชีพ เสียงปอดก่อนและหลังพ่นยา ขนาดยาที่ให้ และการตอบสนองของผู้ป่วย", "is_correct": True},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "การดูแลหลังหัตถการและการควบคุมการติดเชื้อยอดเยี่ยม (Excellent Post-Care & Infection Control)",
                    "message": "การฟังปอดซ้ำยืนยันว่าเสียงหวีดหายไป ลมเข้าปอดได้ดีทั้งสองข้าง และคุณมะลิได้รับการบ้วนปากสดชื่น",
                    "clinical_rationale": "การบ้วนปากช่วยล้างละอองยาตกค้างและป้องกันอาการคอแห้ง ส่วนการล้างผึ่งแห้งอุปกรณ์ช่วยป้องกันการเจริญเติบโตของแบคทีเรียในชุดพ่นยา",
                    "patient_effect_json": {
                        "spo2_set": 97,
                        "rr_set": 16,
                        "hr_set": 82,
                        "distress_set": 0,
                        "breath_sound": "clear_bilateral",
                    },
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "soak_cup_in_bleach",
                    "feedback_type": "caution",
                    "title": "อันตรายจากสารเคมีตกค้าง (Chemical Residue Hazard)",
                    "message": "น้ำยาฟอกขาวทิ้งสารเคมีตกค้างที่ระคายเคืองเยื่อบุหลอดลมอย่างรุนแรงเมื่อนำกระเปาะกลับมาใช้ใหม่ ให้ล้างด้วยน้ำปลอดเชื้อและผึ่งลมให้แห้ง",
                    "hint": "ปฏิบัติตามแนวทางการทำความสะอาดอุปกรณ์ด้วยน้ำปลอดเชื้อ/น้ำกลั่น",
                },
            ],
        },
        # Activity 10: Debrief (Shift Reflection)
        {
            "activity_type": "debrief",
            "title": "สะท้อนคิดและสรุปบทเรียน (Shift Reflection & Debriefing)",
            "instruction": "สะท้อนคิดจากสถานการณ์นี้: สิ่งสำคัญที่สุดที่คุณได้เรียนรู้เกี่ยวกับการบริหารยาพ่น การปรับอัตราก๊าซ และการสอนผู้ป่วยคืออะไร?",
            "content_json": {
                "prompt": "แบ่งปันสิ่งที่คุณได้เรียนรู้เกี่ยวกับการติดตั้งชุดพ่นยา อัตราการไหล 6–8 L/min การสอนเทคนิคการหายใจ และการเฝ้าระวังผลข้างเคียง",
            },
            "display_order": 10,
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ภารกิจห้อง 503 สำเร็จ — ได้รับเหรียญยอดนักพ่นยา (Nebulizer Navigator)!",
                    "message": "ยินดีด้วยที่คุณช่วยบรรเทาภาวะหลอดลมหดเกร็งของคุณมะลิได้สำเร็จ และเชี่ยวชาญหลักการพ่นยาขยายหลอดลมอย่างปลอดภัย",
                    "clinical_rationale": "เทคนิคการพ่นยาที่ถูกต้อง อัตราการไหลที่แม่นยำ การสอนผู้ป่วย และการตระหนักรู้ผลข้างเคียงเป็นทักษะสำคัญยิ่งของการพยาบาลระบบหายใจ",
                    "patient_effect_json": {
                        "spo2_set": 98,
                        "rr_set": 16,
                        "hr_set": 80,
                        "distress_set": 0,
                        "breath_sound": "clear_vesicular",
                        "consciousness": "comfortable_resting",
                    },
                }
            ],
        },
    ]

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
                is_required=True,
                is_active=True,
            )
            db.session.add(activity)
            db.session.flush()
        else:
            activity.activity_type = act_data["activity_type"]
            activity.title = act_data["title"]
            activity.instruction = act_data["instruction"]
            activity.content_json = act_data.get("content_json", {})
            activity.is_required = True
            activity.is_active = True

        # Options
        for opt_idx, opt_data in enumerate(act_data.get("options", [])):
            existing_opt = db.session.execute(
                select(ActivityOption).where(
                    ActivityOption.activity_id == activity.id,
                    ActivityOption.option_key == opt_data["option_key"],
                )
            ).scalar_one_or_none()
            if not existing_opt:
                db.session.add(ActivityOption(
                    activity_id=activity.id,
                    label=opt_data["label"],
                    option_key=opt_data["option_key"],
                    is_correct=opt_data["is_correct"],
                    display_order=opt_idx + 1,
                ))
            else:
                existing_opt.label = opt_data["label"]
                existing_opt.is_correct = opt_data["is_correct"]
                existing_opt.display_order = opt_idx + 1

        # Steps
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
                ))
            else:
                existing_step.step_text = step_data["step_text"]
                existing_step.correct_order = step_data["correct_order"]
                existing_step.rationale = step_data.get("rationale")

        # Feedback
        for fb_data in act_data.get("feedback_rules", []):
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

        # Clean up orphaned options not present in current seed data
        current_opt_keys = {opt["option_key"] for opt in act_data.get("options", [])}
        existing_all_opts = db.session.execute(
            select(ActivityOption).where(ActivityOption.activity_id == activity.id)
        ).scalars().all()
        for opt in existing_all_opts:
            if opt.option_key not in current_opt_keys:
                db.session.delete(opt)

        # Clean up orphaned feedback rules not present in current seed data
        current_fb_pairs = {
            (fb.get("trigger_type") or ("on_selection" if fb.get("trigger_key") else "on_success"), fb.get("trigger_key"))
            for fb in act_data.get("feedback_rules", [])
        }
        existing_all_fbs = db.session.execute(
            select(Feedback).where(Feedback.activity_id == activity.id)
        ).scalars().all()
        for fb in existing_all_fbs:
            if (fb.trigger_type, fb.trigger_key) not in current_fb_pairs:
                db.session.delete(fb)

    # 3. Seed Nebulizer Navigator Badge
    badge = db.session.execute(
        select(Badge).where(Badge.slug == "nebulizer-navigator")
    ).scalar_one_or_none()

    if not badge:
        badge = Badge(
            slug="nebulizer-navigator",
            name="ยอดนักพ่นยา (Nebulizer Navigator)",
            description="มีส่วนร่วมในการตรวจสอบยาขยายหลอดลม การประกอบชุดพ่นยา การสอนผู้ป่วย และการเฝ้าระวังผลข้างเคียง",
            icon="nebulizer",
            mission_id=mission.id,
        )
        db.session.add(badge)
        logger.info("Created Badge 'ยอดนักพ่นยา (Nebulizer Navigator)'")
    else:
        badge.name = "ยอดนักพ่นยา (Nebulizer Navigator)"
        badge.description = "มีส่วนร่วมในการตรวจสอบยาขยายหลอดลม การประกอบชุดพ่นยา การสอนผู้ป่วย และการเฝ้าระวังผลข้างเคียง"
        badge.icon = "nebulizer"
        badge.mission_id = mission.id

    db.session.commit()
    logger.info("Room 503 content seeding complete. %s activities configured.", len(ACTIVITIES_DATA))
    return {"scenario": scenario.id, "activities": len(ACTIVITIES_DATA)}
