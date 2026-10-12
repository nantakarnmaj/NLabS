"""Complete seed content for Room 502: Support the Breath (Oxygen Therapy Mission).

Idempotent: creates or updates scenario, 10 activities, options, procedure steps,
feedback rules, and the 'Oxygen Guardian' badge.
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


def seed_oxygen_mission() -> dict[str, int]:
    """Seed Room 502 scenario, activities, options, steps, feedback, and badge."""
    mission = db.session.execute(
        select(Mission).where((Mission.room_number == "502") | (Mission.slug == "support-the-breath"))
    ).scalar_one_or_none()

    if not mission:
        logger.warning("Room 502 mission not found. Run seed_rooms() first.")
        return {"scenario": 0, "activities": 0}

    # Update Room 502 availability to playable
    mission.availability = "playable"

    # 1. Create or update Scenario
    scenario = db.session.execute(
        select(Scenario).where(Scenario.mission_id == mission.id)
    ).scalar_one_or_none()

    initial_vitals = {
        "spo2": 88,
        "rr": 28,
        "hr": 104,
        "distress": 3,
        "secretions": "minimal",
        "breath_sound": "bilateral_basal_crackles",
        "consciousness": "alert_anxious",
    }

    scenario_title = "การให้ออกซิเจนบำบัดและการปรับขนาดยาสำหรับคุณอนงค์ (Oxygen Therapy & Titration for Ms. Anong)"
    patient_name = "นางอนงค์ (Ms. Anong)"
    clinical_summary = (
        "นางอนงค์ อายุ 62 ปี วันที่ 1 หลังผ่าตัดถุงน้ำดีผ่านกล้อง (Laparoscopic Cholecystectomy) "
        "หายใจในอากาศห้อง บ่นแน่นหน้าอกและหายใจไม่อิ่ม มีอาการกระสับกระส่ายและหายใจเร็ว "
        "มอนิเตอร์ข้างเตียงแสดง O2 saturation (SpO2) 88%, อัตราการหายใจ 28 ครั้ง/นาที, ชีพจร 104 ครั้ง/นาที ฟังปอดได้ยินเสียง crackles ที่ชายปอดทั้งสองข้าง"
    )

    if not scenario:
        scenario = Scenario(
            mission_id=mission.id,
            title=scenario_title,
            patient_name=patient_name,
            patient_age=62,
            patient_gender="หญิง",
            clinical_summary=clinical_summary,
            initial_state_json=initial_vitals,
            difficulty="intermediate",
            is_active=True,
        )
        db.session.add(scenario)
        db.session.flush()
        logger.info("Created Scenario for Room 502 id=%s", scenario.id)
    else:
        scenario.title = scenario_title
        scenario.patient_name = patient_name
        scenario.patient_age = 62
        scenario.patient_gender = "หญิง"
        scenario.clinical_summary = clinical_summary
        scenario.initial_state_json = initial_vitals
        scenario.is_active = True

    # 2. Activities Data (10 activities)
    ACTIVITIES_DATA = [
        # Activity 1: Intro / Meet Patient
        {
            "activity_type": "intro",
            "title": "พบคุณอนงค์ (Meet Ms. Anong) & ข้อมูลผู้ป่วย",
            "instruction": "ทบทวนข้อมูลผู้ป่วย บริบททางคลินิก และสัญญาณชีพระดับฐานบนจอมอนิเตอร์ข้างเตียง",
            "content_json": {
                "patient_name": "นางอนงค์ (Ms. Anong, 62 ปี)",
                "context": (
                    "นางอนงค์ อยู่ในระยะ 24 ชั่วโมงหลังผ่าตัดถุงน้ำดีผ่านกล้อง กดกริ่งเรียกพยาบาลแจ้งว่าหายใจเหนื่อยและรู้สึกวิตกกังวล "
                    "ค่า O2 saturation (SpO2) ลดลงเหลือ 88% ในอากาศห้อง อัตราการหายใจเร็ว 28 ครั้ง/นาที"
                ),
                "goal": "ประเมินสัญญาณภาวะพร่องออกซิเจน เลือกและติดตั้งอุปกรณ์ให้ออกซิเจนที่เหมาะสม ติดตามผลการตอบสนอง และฝึกฝนการเลือกอุปกรณ์ตามสถานการณ์ทางคลินิก",
            },
            "display_order": 1,
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "เริ่มต้นการประเมินทางคลินิก (Clinical Assessment Initiated)",
                    "message": "เริ่มการประเมินระบบหายใจแบบเฉพาะเจาะจงเพื่อระบุสัญญาณทางคลินิกทั้งหมดของภาวะพร่องออกซิเจน",
                    "clinical_rationale": "การตรวจพบภาวะพร่องออกซิเจนหลังผ่าตัดตั้งแต่เนิ่นๆ ช่วยป้องกันภาวะเนื้อเยื่อขาดออกซิเจนและการทำงานหนักของกล้ามเนื้อหัวใจ",
                }
            ],
        },
        # Activity 2: Clinical Cues
        {
            "activity_type": "clinical_cues",
            "title": "ประเมินสัญญาณภาวะพร่องออกซิเจน (Identify Cues of Hypoxemia)",
            "instruction": "เลือกข้อค้นพบจากการประเมินทางคลินิกทั้งหมดที่บ่งชี้ว่าจำเป็นต้องให้ออกซิเจนบำบัด",
            "content_json": {},
            "display_order": 2,
            "options": [
                {"option_key": "spo2_88", "label": "Room Air O2 saturation (SpO2) 88%", "is_correct": True},
                {"option_key": "tachypnea_rr28", "label": "อัตราการหายใจ 28 ครั้ง/นาที", "is_correct": True},
                {"option_key": "tachycardia_hr104", "label": "ชีพจร 104 ครั้ง/นาที", "is_correct": True},
                {"option_key": "dyspnea_anxiety", "label": "รู้สึกเหนื่อย หายใจไม่อิ่ม วิตกกังวลกระสับกระส่าย", "is_correct": True},
                {"option_key": "nausea_postop", "label": "คลื่นไส้เล็กน้อยหลังผ่าตัด", "is_correct": False},
                {"option_key": "normal_urine", "label": "ปัสสาวะออก 45 มล./ชม.", "is_correct": False},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ระบุสัญญาณทางคลินิกถูกต้อง (Accurate Clinical Cue Recognition)",
                    "message": "คุณระบุสัญญาณสำคัญของภาวะพร่องออกซิเจนเฉียบพลันได้อย่างถูกต้อง: O2 saturation (SpO2) 88%, หายใจเร็ว, หัวใจเต้นเร็ว และหายใจเหนื่อย",
                    "clinical_rationale": "หัวใจเต้นเร็วและการหายใจเร็วเป็นกลไกชดเชยหลักของร่างกายเมื่อปริมาณออกซิเจนในหลอดเลือดแดงลดต่ำลง",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "nausea_postop",
                    "feedback_type": "guidance",
                    "title": "อาการทั่วไปหลังผ่าตัด (Incidental Postoperative Finding)",
                    "message": "แม้ว่าอาการคลื่นไส้จะพบได้บ่อยหลังผ่าตัดถุงน้ำดี แต่ไม่ใช่ข้อบ่งชี้โดยตรงในการให้ออกซิเจนบำบัด",
                    "hint": "เน้นตัวบ่งชี้ของการแลกเปลี่ยนก๊าซบกพร่องและการไหลเวียนเลือดไปเลี้ยงเนื้อเยื่อ",
                },
            ],
        },
        # Activity 3: Equipment Select (Choose Initial Oxygen Device)
        {
            "activity_type": "equipment_select",
            "title": "เลือกอุปกรณ์ให้ออกซิเจนเริ่มต้น (Choose Initial Oxygen Delivery Device)",
            "instruction": "เลือกอุปกรณ์ให้ออกซิเจนและอัตราการไหลเริ่มต้นที่เหมาะสมที่สุดสำหรับคุณอนงค์",
            "content_json": {},
            "display_order": 3,
            "options": [
                {
                    "option_key": "nasal_cannula_3l",
                    "label": "สายให้ออกซิเจนทางจมูก (Nasal Cannula) 3 L/min",
                    "is_correct": True,
                },
                {
                    "option_key": "simple_mask_2l",
                    "label": "หน้ากากธรรมดา (Simple Face Mask) 2 L/min",
                    "is_correct": False,
                },
                {
                    "option_key": "nrb_mask_15l",
                    "label": "หน้ากากแบบมีถุงสำรองชนิดไม่ไหลย้อน (Non-Rebreather Mask - NRB) 15 L/min",
                    "is_correct": False,
                },
                {
                    "option_key": "room_air_deep_breath",
                    "label": "ฝึกหายใจอย่างมีประสิทธิภาพ โดยไม่ให้ออกซิเจน",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "เลือกอุปกรณ์เริ่มต้นได้เหมาะสมที่สุด (Optimal First-Line Device Selection)",
                    "message": "Nasal cannula อัตรา 2–4 L/min เหมาะอย่างยิ่งสำหรับภาวะพร่องออกซิเจนระดับเล็กน้อยถึงปานกลางในผู้ป่วยที่รู้สึกตัวดีและไม่มีอาการหายใจลำบากขั้นวิกฤต",
                    "clinical_rationale": "Nasal cannula ให้ออกซิเจนแบบ low-flow (FiO2 24–44%) โดยที่ผู้ป่วยยังสุขสบายและสื่อสารได้",
                    "patient_effect_json": {"distress_delta": -1},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "simple_mask_2l",
                    "feedback_type": "critical",
                    "title": "อันตราย: อัตราการไหลต่ำเกินไปสำหรับหน้ากาก (Safety Hazard: Flow Rate Too Low)",
                    "message": "การใช้ Simple face mask ด้วยอัตราการไหลต่ำกว่า 5 L/min จะทำให้คาร์บอนไดออกไซด์จากการหายใจออกสะสมคั่งอยู่ในหน้ากาก ส่งผลให้ผู้ป่วยสูดดม CO2 ซ้ำ (CO2 rebreathing)",
                    "hint": "Simple face mask ต้องเปิดอัตราการไหลอย่างน้อย 5–10 L/min เสมอเพื่อชะล้างก๊าซ CO2",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "nrb_mask_15l",
                    "feedback_type": "guidance",
                    "title": "ออกซิเจนสูงเกินความจำเป็น (Excessive Oxygen Delivery)",
                    "message": "Non-rebreather mask สงวนไว้สำหรับภาวะพร่องออกซิเจนรุนแรงหรือภาวะฉุกเฉินวิกฤต (เช่น ช็อก, ได้รับก๊าซพิษ, การบาดเจ็บรุนแรง)",
                    "hint": "เริ่มต้นด้วยการปรับขนาดแบบ Low-flow เพื่อหลีกเลี่ยงภาวะเป็นพิษจากออกซิเจนและความอึดอัดของผู้ป่วย",
                },
            ],
        },
        # Activity 4: Sequence (Setup and Administration Flow)
        {
            "activity_type": "sequence",
            "title": "จัดลำดับขั้นตอนการเตรียมและการให้ออกซิเจน (Oxygen Setup Sequence)",
            "instruction": "จัดลำดับขั้นตอนการเตรียมและใส่สาย Nasal Cannula ให้ถูกต้องตามลำดับหัตถการ",
            "content_json": {},
            "display_order": 4,
            "steps": [
                {
                    "step_key": "step_verify_source",
                    "step_text": "ตรวจสอบเกจวัดอัตราการไหล (Flowmeter) เสียบแน่นกับท่อออกซิเจนบนผนังและต่อขวดน้ำให้ความชื้น (Humidifier) แน่นหนา",
                    "correct_order": 1,
                    "rationale": "การตรวจสอบแหล่งก๊าซและระบบความชื้นช่วยป้องกันก๊าซรั่วซึมและการระคายเคืองทางเดินหายใจแห้ง",
                },
                {
                    "step_key": "step_set_flow",
                    "step_text": "ต่อสาย Nasal cannula เข้ากับท่อขวดน้ำให้ความชื้น และหมุนปรับปุ่มเปิดให้กึ่งกลางลูกลอยอยู่ที่ 3 L/min",
                    "correct_order": 2,
                    "rationale": "ต้องตรวจสอบการไหลของก๊าซจากปลายสายเสมอก่อนนำไปใส่ให้ผู้ป่วย",
                },
                {
                    "step_key": "step_verify_gas_flow",
                    "step_text": "ตรวจสอบว่ามีออกซิเจนไหลผ่านปลายสายจริง (ทดสอบสัมผัสแรงลมที่หลังมือ)",
                    "correct_order": 3,
                    "rationale": "การทดสอบลมไหลจริงช่วยป้องกันการใส่สายที่ไม่มีก๊าซไหลหรือสายพับหักงอ",
                },
                {
                    "step_key": "step_insert_prongs",
                    "step_text": "สอดง่ามสาย (Prongs) ทั้งสองข้างเข้าไปในรูจมูก โดยให้ส่วนโค้งโค้งชี้ลงตามแนวโครงสร้างกายวิภาคของโพรงจมูก",
                    "correct_order": 4,
                    "rationale": "ง่ามสายโค้งลงตามกายวิภาคของโพรงจมูกช่วยเพิ่มประสิทธิภาพการไหลและไม่ระคายเคืองเยื่อบุ",
                },
                {
                    "step_key": "step_loop_ears_snug",
                    "step_text": "คล้องสายพาดเหนือบานหูทั้งสองข้าง และเลื่อนตัวปรับใต้คางขึ้นให้กระชับพอดีอย่างนุ่มนวล",
                    "correct_order": 5,
                    "rationale": "ช่วยยึดสายให้กระชับโดยไม่แน่นตึงจนทำให้เกิดแผลกดทับที่ใบหู",
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "การเตรียมและให้ออกซิเจนราบรื่นถูกต้อง (Smooth Administration & Delivery)",
                    "message": "ติดตั้งและให้ออกซิเจนเรียบร้อย! คุณอนงค์เริ่มได้รับออกซิเจนอย่างสบายและมีประสิทธิภาพ",
                    "clinical_rationale": "การจัดวางง่ามสายและทดสอบลมไหลช่วยให้ออกซิเจนส่งถึงผู้ป่วยอย่างต่อเนื่องและสุขสบาย",
                    "patient_effect_json": {"spo2_set": 95, "hr_set": 82, "rr_set": 18, "distress_set": 0},
                }
            ],
        },
        # Activity 5: Safety Check (Fire Precautions & Cylinder Safety)
        {
            "activity_type": "safety_check",
            "title": "ความปลอดภัยในการใช้ออกซิเจนและการป้องกันอัคคีภัย (Oxygen Safety & Fire Precautions)",
            "instruction": "เลือกข้อควรระวังความปลอดภัยที่จำเป็นทั้งหมดระหว่างการให้ออกซิเจนบำบัดในหอผู้ป่วย",
            "content_json": {},
            "display_order": 5,
            "options": [
                {"option_key": "no_smoking_signs", "label": "ติดป้ายเตือน 'ห้ามสูบบุหรี่' และห้ามจุดประกายไฟหรือเปลวไฟในห้อง", "is_correct": True},
                {"option_key": "sterile_water_level", "label": "ตรวจสอบระดับน้ำกลั่นปลอดเชื้อ (Sterile water) ในกระบอกความชื้นให้ไม่น้อยกว่าระดับ Min", "is_correct": True},
                {"option_key": "grounded_electrical", "label": "ตรวจสอบอุปกรณ์ไฟฟ้าข้างเตียงทั้งหมดให้มีสายดินและอยู่ในสภาพปลอดภัยไม่มีประกายไฟ", "is_correct": True},
                {"option_key": "avoid_petroleum", "label": "หลีกเลี่ยงสารหล่อลื่นที่มีส่วนผสมของน้ำมันปิโตรเลียม บริเวณใบหน้าและจมูก", "is_correct": True},
                {"option_key": "vaseline_nares", "label": "ทาวาสลีนชุ่มๆ ในรูจมูกเพื่อป้องกันเยื่อบุแห้ง", "is_correct": False},
                {"option_key": "oil_flowmeter", "label": "หยอดน้ำมันหล่อลื่นที่เกจ flowmeter เพื่อให้หมุนคล่องขึ้น", "is_correct": False},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ตรวจสอบความปลอดภัยครบถ้วน (Safety Protocols Fully Verified)",
                    "message": "คุณตรวจสอบการป้องกันไฟ ระดับน้ำให้ความชื้น และการหลีกเลี่ยงสารไฮโดรคาร์บอนติดไฟได้อย่างถูกต้อง",
                    "clinical_rationale": "ออกซิเจนช่วยเร่งการลุกไหม้อย่างรุนแรง การสัมผัสกับสารปิโตรเลียมหรือน้ำมันในบรรยากาศออกซิเจนเข้มข้นก่อความเสี่ยงไฟลุกไหม้รุนแรง",
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "vaseline_nares",
                    "feedback_type": "critical",
                    "title": "อันตรายจากเพลิงไหม้: ผลิตภัณฑ์ปิโตรเลียมใกล้ออกซิเจน (Fire Hazard: Petroleum Products)",
                    "message": "วาสลีน (Petroleum jelly) เป็นสารไฮโดรคาร์บอนติดไฟง่าย ในบรรยากาศที่มีออกซิเจนเข้มข้นจะติดไฟและลุกไหม้ใบหน้าอย่างรุนแรง",
                    "hint": "เลือกใช้เจลหล่อลื่นสูตรน้ำ (Water-soluble lubricant เช่น K-Y jelly) เสมอในการดูแลความชุ่มชื้นเยื่อบุระหว่างให้ออกซิเจน",
                },
            ],
        },
        # Activity 6: Troubleshooting / Trend Monitoring (Watch the Monitor)
        {
            "activity_type": "troubleshooting",
            "title": "เฝ้าระวังมอนิเตอร์และการวิเคราะห์แนวโน้มสัญญาณชีพ (Watch the Monitor)",
            "instruction": "ประเมินแนวโน้มสัญญาณชีพบังเกิดผล 10 นาทีบนจอมอนิเตอร์ และตัดสินใจเลือกการปฏิบัติทางการพยาบาลที่เหมาะสม",
            "content_json": {},
            "display_order": 6,
            "options": [
                {
                    "option_key": "maintain_and_reassess",
                    "label": "คงออกซิเจน 3 L/min ผ่าน Nasal cannula ต่อไปและเฝ้าระวังต่อเนื่อง ไม่ให้ O2 saturation (SpO2) ลดต่ำกว่า 95%",
                    "is_correct": True,
                },
                {
                    "option_key": "crank_to_10l",
                    "label": "เพิ่มอัตราออกซิเจน Nasal cannula เป็น 10 L/min เพื่อให้ O2 saturation (SpO2) แตะ 100% เร็วขึ้น",
                    "is_correct": False,
                },
                {
                    "option_key": "stop_oxygen_abruptly",
                    "label": "หยุดให้ออกซิเจนทันทีเพราะ O2 saturation (SpO2) แตะ 95% แล้ว",
                    "is_correct": False,
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "บรรลุเป้าหมายการให้ออกซิเจน (Target Oxygenation Achieved)",
                    "message": "สัญญาณชีพของคุณอนงค์คงที่และตอบสนองได้ดี: O2 saturation (SpO2) 95%, หายใจ 18 ครั้ง/นาที, ชีพจร 82 ครั้ง/นาที อาการหายใจเหนื่อยทุเลาลง",
                    "clinical_rationale": "เป้าหมายค่าความอิ่มตัวออกซิเจนในผู้ป่วยผู้ใหญ่ส่วนใหญ่คือ 94–98% การคงขนาด 3 L/min ช่วยรักษาระดับออกซิเจนให้อยู่ในเกณฑ์ปลอดภัยและป้องกันภาวะออกซิเจนเกิน (Hyperoxia)",
                    "patient_effect_json": {"spo2_set": 95, "rr_set": 18, "hr_set": 82, "distress_set": 0},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "crank_to_10l",
                    "feedback_type": "caution",
                    "title": "อัตราการไหลสูงเกินขีดจำกัดของ Nasal Cannula (Excessive Flow)",
                    "message": "อัตราการไหลที่เกิน 6 L/min บน Nasal cannula ไม่ช่วยเพิ่ม FiO2 อย่างมีนัยสำคัญเนื่องจากข้อจำกัดทางกายวิภาคของโพรงจมูก แต่จะทำให้เยื่อบุจมูกแห้งแตก ปวดศีรษะ และเลือดกำเดาไหล",
                    "hint": "อัตราการไหลสูงสุดที่แนะนำสำหรับ Nasal cannula มาตรฐานคือไม่เกิน 6 L/min",
                },
            ],
        },
        # Activity 7: Matching (Device Match Challenge)
        {
            "activity_type": "matching",
            "title": "กิจกรรมจับคู่อุปกรณ์ออกซิเจนตามสถานการณ์ทางคลินิก (Oxygen Device Match Challenge)",
            "instruction": "จับคู่สถานการณ์ผู้ป่วยจำลองทางคลินิกแต่ละข้อกับอุปกรณ์ให้ออกซิเจนที่เหมาะสมที่สุด",
            "content_json": {
                "matches": [
                    {
                        "prompt_key": "case_mild_postop",
                        "prompt_label": "กรณีที่ 1: ผู้ป่วยหลังผ่าตัดอาการคงที่ มีภาวะพร่องออกซิเจนเล็กน้อย",
                        "prompt_text": "ผู้ป่วยอายุ 54 ปี หลังผ่าตัด O2 saturation (SpO2) Room air 92% รู้สึกตัวดี พูดคุยได้ ต้องการดื่มน้ำ",
                        "correct_target_key": "nasal_cannula",
                        "target_label": "สายให้ออกซิเจนทางจมูก Nasal Cannula 3–5 L/min",
                        "rationale": "Nasal cannula ให้ออกซิเจนแบบ low-flow (24–44% FiO2) สุขสบาย สามารถรับประทานอาหาร ดื่มน้ำ และพูดคุยได้",
                        "hint": "เลือกอุปกรณ์ low-flow ที่ไม่เกะกะและเอื้อต่อการรับประทานอาหาร/ดื่มน้ำ",
                    },
                    {
                        "prompt_key": "case_copd_precise",
                        "prompt_label": "กรณีที่ 2: ผู้ป่วยโรคถุงลมโป่งพองกำเริบเฉียบพลัน (COPD EXACERBATION)",
                        "prompt_text": "ผู้ป่วยอายุ 68 ปี โรค COPD กำเริบเฉียบพลัน O2 saturation (SpO2) Room air 89%",
                        "correct_target_key": "nasal_cannula_copd",
                        "target_label": "สายให้ออกซิเจนทางจมูก Nasal Cannula 1–2 L/min",
                        "rationale": "ผู้ป่วย COPD มีภาวะ hypoxic drive การให้ออกซิเจน low-flow ผ่าน Nasal Cannula 1–2 L/min ช่วยรักษาเป้าหมาย SpO2 88–92% และหลีกเลี่ยงภาวะคั่งก๊าซ CO2 (CO2 narcosis)",
                        "hint": "ผู้ป่วย COPD มีเป้าหมาย SpO2 88–92% ควรเลือกออกซิเจน low-flow อัตรา 1–2 L/min เพื่อหลีกเลี่ยงการกดการหายใจ",
                    },
                    {
                        "prompt_key": "case_severe_hypoxemia",
                        "prompt_label": "กรณีที่ 3: ภาวะพร่องออกซิเจนรุนแรงเฉียบพลัน (Acute Severe Hypoxemic Distress)",
                        "prompt_text": "ผู้ป่วยอายุ 45 ปี สูดควันไฟในเหตุเพลิงไหม้ หายใจลำบาก อาการวิกฤต ค่า O2 saturation (SpO2) Room air 81%",
                        "correct_target_key": "nrb_mask",
                        "target_label": "หน้ากากแบบมีถุงสำรองไม่ไหลย้อน Non-Rebreather Mask (10–15 L/min)",
                        "rationale": "Non-rebreather mask สามารถให้ออกซิเจนความเข้มข้นสูง (FiO2 60–90%) ผ่านถุง Reservoir bag สำหรับการกู้ชีพในภาวะฉุกเฉินวิกฤต",
                        "hint": "มองหาอุปกรณ์ที่มีถุงสำรองออกซิเจนความเข้มข้นสูงสำหรับภาวะวิกฤตฉุกเฉิน",
                    },
                    {
                        "prompt_key": "case_tracheostomy",
                        "prompt_label": "กรณีที่ 4: ผู้ป่วย on Tracheostomy tube",
                        "prompt_text": "ผู้ป่วยอายุ 60 ปี on Tracheostomy tube กระสับกระส่าย หายใจ 26 ครั้ง/นาที ค่า O2 saturation (SpO2) Room air 90%",
                        "correct_target_key": "tracheostomy_collar",
                        "target_label": "หน้ากากครอบคอ Oxygen Collar (T-collar / Trach mask)",
                        "rationale": "Oxygen collar (Tracheostomy collar) ครอบบนท่อเจาะคอโดยตรงเพื่อให้ออกซิเจนและความชื้นสูง ไม่รบกวนทางเดินหายใจส่วนบนและป้องกันเยื่อบุหลอดลมแห้ง",
                        "hint": "ผู้ป่วยที่หายใจผ่านท่อเจาะคอ (Tracheostomy) ต้องใช้อุปกรณ์ใดครอบบริเวณคอเพื่อส่งออกซิเจนและความชื้นโดยตรง?",
                    },
                ],
                "target_options": [
                    {"key": "nasal_cannula", "label": "Nasal Cannula 3–5 L/min", "image": "equipment/nasal_cannula.jpg"},
                    {"key": "nasal_cannula_copd", "label": "Nasal Cannula 1–2 L/min", "image": "equipment/nasal_cannula.jpg"},
                    {"key": "tracheostomy_collar", "label": "Oxygen Collar (หน้ากากครอบคอ / Trach mask)", "image": "equipment/tracheostomy_collar.jpg"},
                    {"key": "nrb_mask", "label": "Non-Rebreather Mask (10–15 L/min, FiO₂ 60–90%)", "image": "equipment/nrb_mask.jpg"},
                ],
            },
            "display_order": 7,
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "เชี่ยวชาญระบบการให้ออกซิเจน (Mastery of Oxygen Delivery Systems)",
                    "message": "ยอดเยี่ยมมาก! คุณจับคู่สถานการณ์ทางคลินิกของผู้ป่วยแต่ละรายกับอุปกรณ์ให้ออกซิเจนได้อย่างถูกต้องสมบูรณ์แบบ",
                    "clinical_rationale": "การเลือกอุปกรณ์ตามความแม่นยำของ FiO2 รูปแบบการหายใจ และความเร่งด่วนทางคลินิกช่วยให้การรักษาปลอดภัยและตรงจุด",
                    "patient_effect_json": {"spo2_set": 88, "hr_set": 104, "rr_set": 26, "distress_set": 2},
                }
            ],
        },
        # Activity 8: Decision (Sudden Desaturation Challenge)
        {
            "activity_type": "decision",
            "title": "สถานการณ์ท้าทาย: ภาวะออกซิเจนตกเฉียบพลัน (Sudden Desaturation Challenge)",
            "instruction": "สัญญาณเตือนบนเครื่องวัดออกซิเจนดังขึ้นฉุกเฉิน: ค่า O2 saturation (SpO2) ของคุณอนงค์ตกฮวบจาก 95% เหลือ 88% ในฐานะพยาบาลผู้รับผิดชอบ การปฏิบัติการพยาบาลที่ต้องทำเป็นลำดับแรกคืออะไร?",
            "content_json": {
                "is_emergency": True,
                "alarm_badge": "CRITICAL BEDSIDE ALARM",
                "alarm_code": "⚠️ ALARM: SPO2 LOW LIMIT (< 90%)",
                "telemetry": {
                    "spo2": "88%",
                    "spo2_trend": "ตกฮวบจาก 95%",
                    "hr": "104 bpm",
                    "rr": "24 /min",
                    "patient_status": "นอนตะแคง / สีหน้ากังวล",
                },
                "scenario_description": "ขณะที่คุณกำลังบันทึกเวชระเบียน ทันใดนั้นสัญญาณเตือน SpO₂ Low Limit จากเครื่องวัดข้างเตียงส่งเสียงร้องเตือนดังถี่ๆ ต่อเนื่อง! ตัวเลข SpO₂ แสดงค่าสีแดงกระพริบตกฮวบจาก 95% ลงมาอยู่ที่ 88% สัญญาณชีพ HR 104 bpm, RR 24 ครั้ง/นาที เมื่อคุณรีบเดินมาที่ข้างเตียง พบว่าคุณอนงค์กำลังพลิกตะแคงตัว สีหน้าดูวิตกกังวล และสังเกตเห็นว่าสายออกซิเจนไม่อยู่ในจมูกผู้ป่วย",
                "challenge_question": "ในฐานะพยาบาลผู้รับผิดชอบ การปฏิบัติการพยาบาลที่ถูกต้องและต้องทำเป็น \"ลำดับแรก (First Action)\" คืออะไร?",
            },
            "display_order": 8,
            "options": [
                {
                    "option_key": "check_patient_and_tubing",
                    "label": "เข้าประเมินคุณอนงค์ทันที: ตรวจดูลักษณะการหายใจ ระดับความรู้สึกตัว และตรวจสอบตำแหน่งสาย Nasal cannula ว่าง่ามสายหลุดหรือท่อหักงอ/หลุดจากข้อต่อหรือไม่",
                    "is_correct": True,
                    "description": "ประเมินผู้ป่วยและอุปกรณ์ก่อนเสมอ (Assess Patient & Circuit First) เพื่อระบุและแก้ไขสาเหตุที่แท้จริงอย่างรวดเร็ว",
                },
                {
                    "option_key": "increase_flow_rate_blindly",
                    "label": "รีบปรับหมุนเพิ่มอัตราการไหลของออกซิเจน (Flow meter) จาก 3 L/min เป็น 6–8 L/min ทันที เพื่อเร่งให้ค่า SpO₂ กลับขึ้นมาเกิน 95% โดยเร็ว",
                    "is_correct": False,
                    "description": "การปรับเพิ่มอัตราการไหลโดยยังไม่ตรวจดูสายออกซิเจน หากสายหลุดอยู่จะไม่สามารถช่วยผู้ป่วยได้และแก้ปัญหาไม่ตรงจุด",
                },
                {
                    "option_key": "call_code_intubation",
                    "label": "รีบเปลี่ยนเป็นหน้ากาก Non-Rebreather Mask 10 L/min และกดกริ่งเรียกทีมแพทย์ฉุกเฉิน (Code Blue) ทันทีเพราะคิดว่าระบบหายใจล้มเหลว",
                    "is_correct": False,
                    "description": "การยกระดับการรักษาฉุกเฉินขั้นสูงสุดโดยยังไม่ได้ตรวจประเมินผู้ป่วยและอุปกรณ์ขั้นพื้นฐานเป็นการกระทำที่เกินจำเป็น",
                },
                {
                    "option_key": "silence_alarm_wait",
                    "label": "กดปิดเสียงเตือน (Silence Alarm) แล้วย้าย Probe ไปหนีบนิ้วอื่น จากนั้นรอสังเกตอาการ 10–15 นาที เพื่อดูว่าค่าจะดีขึ้นเองหรือไม่",
                    "is_correct": False,
                    "description": "การปิดเสียงเตือนและรอคอยโดยไม่เข้าตรวจดูตัวผู้ป่วยทันที เสี่ยงทำให้เกิดภาวะขาดออกซิเจนรุนแรงและเป็นอันตรายถึงชีวิต",
                },
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "trigger_key": "check_patient_and_tubing",
                    "title": "การแก้ไขปัญหาอย่างเป็นระบบยอดเยี่ยม (Systematic Troubleshooting Success)",
                    "message": "คุณรีบเข้าประเมินข้างเตียงและพบว่าง่ามสาย Nasal cannula เลื่อนหลุดจากรูจมูกเนื่องจากการพลิกตัว เมื่อจัดใส่ง่ามสายกลับเข้าที่เดิมและตรวจสายท่อไม่ให้หักงอ ค่า O2 saturation (SpO2) ก็กลับขึ้นมาเป็น 95% ทันที!",
                    "clinical_rationale": "กฎทองคำทางการพยาบาล: ตรวจประเมินผู้ป่วยและอุปกรณ์ก่อนเสมอ (Assess Patient & Circuit First) ก่อนตัดสินใจปรับเพิ่มยาหรือยกระดับการรักษา",
                    "patient_effect_json": {"spo2_set": 95, "hr_set": 82, "rr_set": 18, "distress_set": 0},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "increase_flow_rate_blindly",
                    "feedback_type": "guidance",
                    "title": "การปรับเพิ่มออกซิเจนโดยไม่ตรวจดูผู้ป่วย (Unverified Flow Adjustment Hazard)",
                    "message": "การปรับเพิ่ม Flow meter ไม่ได้ผล! เนื่องจากง่ามสายออกซิเจนหลุดออกจากรูจมูก การเร่งเปิดออกซิเจนจึงมีแต่เสียงแก๊สพุ่งแต่ไม่เข้าสู่ทางเดินหายใจ และผู้ป่วยยังคงมีภาวะพร่องออกซิเจน",
                    "clinical_rationale": "เมื่อค่า SpO2 ตกเฉียบพลัน ต้องตรวจดูตัวผู้ป่วยและการเชื่อมต่อของอุปกรณ์เป็นลำดับแรกเสมอ การหมุนเพิ่ม flow โดยไม่ตรวจสายมักเสียเวลาและไม่แก้ต้นเหตุ",
                    "hint": "ตรวจดูผู้ป่วย ท่าทาง และการเชื่อมต่อของสายออกซิเจนก่อนรีบหมุนปรับอัตราการไหล",
                    "patient_effect_json": {"distress_delta": 1},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "call_code_intubation",
                    "feedback_type": "guidance",
                    "title": "การยกระดับการรักษาเร็วเกินจำเป็น (Premature Escalation)",
                    "message": "การเรียกทีมกู้ชีพและเปลี่ยนใส่อุปกรณ์ความเข้มข้นสูงทันทีโดยยังไม่ได้ตรวจดูตัวผู้ป่วยเป็นการตื่นตระหนกเกินจำเป็น สาเหตุที่พบบ่อยที่สุดของภาวะออกซิเจนตกเฉียบพลันหลังผ่าตัดคือสายหลุดหรือสายหักงอ",
                    "clinical_rationale": "ต้องประเมิน ABC (Airway, Breathing, Circuit) ขั้นพื้นฐานก่อนตัดสินใจยกระดับการรักษาฉุกเฉิน",
                    "hint": "ตรวจดูผู้ป่วย ท่าทาง และการเชื่อมต่อของสายออกซิเจนก่อนเป็นอันดับแรก",
                    "patient_effect_json": {"distress_delta": 1},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "silence_alarm_wait",
                    "feedback_type": "guidance",
                    "title": "ความล่าช้าในการจัดการภาวะพร่องออกซิเจน (Delayed Assessment Hazard)",
                    "message": "การกดปิดเสียงเตือนแล้วรอคอยโดยไม่เข้าประเมินผู้ป่วยและอุปกรณ์ทันที เป็นอันตรายอย่างยิ่งเพราะอาจทำให้ผู้ป่วยขาดออกซิเจนต่อเนื่องจนหมดสติได้",
                    "clinical_rationale": "ห้ามเพิกเฉยต่อสัญญาณเตือน (Alarm Fatigue) ต้องเข้าตรวจประเมินผู้ป่วยข้างเตียงทันทีที่สัญญาณเตือนดัง",
                    "hint": "อย่ารอคอย เข้าตรวจประเมินผู้ป่วยข้างเตียงทันที",
                    "patient_effect_json": {"distress_delta": 1},
                },
            ],
        },
        # Activity 9: Aftercare (Comfort & Skin Protection)
        {
            "activity_type": "aftercare",
            "title": "ความสุขสบาย การปกป้องผิวหนัง และการสื่อสาร (Comfort & Skin Protection)",
            "instruction": "เลือกการพยาบาลที่ช่วยปกป้องผิวหนังและส่งเสริมความสุขสบายทางจิตใจระหว่างการให้ออกซิเจนบำบัด",
            "content_json": {},
            "display_order": 9,
            "options": [
                {"option_key": "ear_padding", "label": "ใส่แผ่นรองนุ่มๆ เหนือใบหูทั้งสองข้างเพื่อป้องกันแผลกดทับจากสายออกซิเจน", "is_correct": True},
                {"option_key": "nares_water_lube", "label": "ตรวจดูรูจมูกและทาสารหล่อลื่นสูตรน้ำหากเยื่อบุจมูกแห้ง", "is_correct": True},
                {"option_key": "reassure_anxiety", "label": "อธิบายให้คุณอนงค์ทราบว่าระดับออกซิเจนอยู่ในเกณฑ์ปลอดภัยแล้วเพื่อคลายความวิตกกังวล", "is_correct": True},
                {"option_key": "document_care", "label": "บันทึกทางการพยาบาล: อัตราออกซิเจน (3 L/min NC), ค่า O2 saturation (SpO2) 95%, อัตราหายใจ (18 ครั้ง/นาที) และสภาพผิวหนัง", "is_correct": True},
                {"option_key": "tape_prongs_tight", "label": "ใช้พลาสเตอร์เหนียวปิดตรึงสายออกซิเจนแน่นหนาแนบกับแก้มและใบหู", "is_correct": False},
            ],
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "การดูแลแบบองค์รวมครอบคลุม (Comprehensive Patient-Centered Care)",
                    "message": "การดูแลยอดเยี่ยมมาก ผิวหนังของคุณอนงค์ได้รับการปกป้อง ความวิตกกังวลลดลง และการบันทึกข้อมูลครบถ้วนสมบูรณ์",
                    "clinical_rationale": "แผลกดทับบริเวณหลังใบหูจากสายออกซิเจนเป็นภาวะแทรกซ้อนในโรงพยาบาลที่พบบ่อยแต่ป้องกันได้",
                    "patient_effect_json": {"spo2_set": 95, "hr_set": 80, "rr_set": 18, "distress_set": 0},
                },
                {
                    "trigger_type": "on_hazard",
                    "trigger_key": "tape_prongs_tight",
                    "feedback_type": "caution",
                    "title": "อันตรายจากการฉีกขาดของผิวหนัง (Skin Shear Hazard)",
                    "message": "การติดพลาสเตอร์เหนียวแน่นเกินไปอาจทำให้ผิวหนังชั้นนอกลอกและฉีกขาดในผู้สูงอายุ",
                    "hint": "ใช้ตัวปรับใต้คางของสายร่วมกับแผ่นรองนุ่มแทนการใช้เทปกาวเหนียวติดแน่น",
                },
            ],
        },
        # Activity 10: Debrief (Shift Reflection)
        {
            "activity_type": "debrief",
            "title": "สะท้อนคิดและสรุปบทเรียน (Shift Reflection & Debriefing)",
            "instruction": "สะท้อนคิดจากสถานการณ์นี้: สิ่งสำคัญที่สุดที่คุณได้เรียนรู้เกี่ยวกับการเลือกอุปกรณ์ให้ออกซิเจน การติดตามแนวโน้ม และความปลอดภัยคืออะไร?",
            "content_json": {
                "prompt": "แบ่งปันสิ่งที่คุณได้เรียนรู้เกี่ยวกับการเลือกอุปกรณ์ให้ออกซิเจน การปรับขนาด และการดูแลความปลอดภัยของผู้ป่วย",
            },
            "display_order": 10,
            "feedback_rules": [
                {
                    "trigger_type": "on_success",
                    "title": "ภารกิจห้อง 502 สำเร็จ — ได้รับเหรียญผู้พิทักษ์ออกซิเจน (Oxygen Guardian)!",
                    "message": "ยินดีด้วยที่คุณช่วยเหลือการหายใจของคุณอนงค์สำเร็จเรียบร้อย และเชี่ยวชาญหลักการให้ออกซิเจนบำบัดอย่างปลอดภัย",
                    "clinical_rationale": "ออกซิเจนถือเป็นยาที่มีข้อบ่งชี้ เป้าหมายการปรับขนาด และข้อควรระวังความปลอดภัยเฉพาะที่ต้องปฏิบัติตามอย่างเคร่งครัด",
                    "patient_effect_json": {
                        "spo2_set": 96,
                        "rr_set": 18,
                        "hr_set": 80,
                        "distress_set": 0,
                        "consciousness_set": "alert",
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

    # 3. Seed Oxygen Guardian Badge
    badge = db.session.execute(
        select(Badge).where(Badge.slug == "oxygen-guardian")
    ).scalar_one_or_none()

    if not badge:
        badge = Badge(
            slug="oxygen-guardian",
            name="ผู้พิทักษ์ออกซิเจน (Oxygen Guardian)",
            description="มีส่วนร่วมในการประเมินภาวะพร่องออกซิเจน การเลือกอุปกรณ์ให้ออกซิเจนอย่างปลอดภัย และการเฝ้าระวังแนวโน้ม",
            icon="oxygen",
            mission_id=mission.id,
        )
        db.session.add(badge)
        logger.info("Created Badge 'ผู้พิทักษ์ออกซิเจน (Oxygen Guardian)'")
    else:
        badge.name = "ผู้พิทักษ์ออกซิเจน (Oxygen Guardian)"
        badge.description = "มีส่วนร่วมในการประเมินภาวะพร่องออกซิเจน การเลือกอุปกรณ์ให้ออกซิเจนอย่างปลอดภัย และการเฝ้าระวังแนวโน้ม"
        badge.icon = "oxygen"
        badge.mission_id = mission.id

    db.session.commit()
    logger.info("Room 502 content seeding complete. %s activities configured.", len(ACTIVITIES_DATA))
    return {"scenario": scenario.id, "activities": len(ACTIVITIES_DATA)}
