"""Equipment Station service handling matching pictures with names and packing procedure baskets."""

from __future__ import annotations

from typing import Any

# Master catalog of clinical respiratory equipment
EQUIPMENT_CATALOG: dict[str, dict[str, Any]] = {
    "nasal_cannula": {
        "id": "nasal_cannula",
        "name_th": "สายให้ออกซิเจนทางจมูก",
        "name_en": "Nasal Cannula",
        "image": "images/equipment/nasal_cannula.jpg",
        "description": "สายยาง 2 แฉกสำหรับสอดเข้ารูจมูก ให้ออกซิเจนความเข้มข้นต่ำ (Low-flow 1-6 LPM)",
    },
    "simple_mask": {
        "id": "simple_mask",
        "name_th": "หน้ากากออกซิเจนแบบธรรมดา",
        "name_en": "Simple Face Mask",
        "image": "images/equipment/simple_mask.jpg",
        "description": "หน้ากากครอบจมูกและปาก ให้ออกซิเจน 5-10 LPM (FiO2 40-60%)",
    },
    "venturi_mask": {
        "id": "venturi_mask",
        "name_th": "หน้ากากเวนจูรี่",
        "name_en": "Venturi Mask",
        "image": "images/equipment/venturi_mask.jpg",
        "description": "หน้ากากควบคุมความเข้มข้นออกซิเจนที่แน่นอน (High-flow FiO2 24-50%) สำหรับผู้ป่วย COPD",
    },
    "nrb_mask": {
        "id": "nrb_mask",
        "name_th": "หน้ากากออกซิเจนพร้อมถุงสำรอง",
        "name_en": "Non-Rebreathing Mask (NRB)",
        "image": "images/equipment/nrb_mask.jpg",
        "description": "หน้ากากพร้อมถุง Reservoir bag และ One-way valve ให้ความเข้มข้นออกซิเจนสูง 10-15 LPM (FiO2 >80%)",
    },
    "o2_flowmeter": {
        "id": "o2_flowmeter",
        "name_th": "เกจปรับอัตราไหลของออกซิเจน",
        "name_en": "Oxygen Flowmeter",
        "image": "images/equipment/o2_flowmeter.png",
        "description": "มาตรวัดควบคุมอัตราการไหลของก๊าซออกซิเจน (หน่วยเป็นลิตรต่อนาที: L/min)",
    },
    "humidifier_bottle": {
        "id": "humidifier_bottle",
        "name_th": "กระบอกน้ำให้ความชื้น",
        "name_en": "Humidifier Bottle",
        "image": "images/equipment/humidifier_bottle.png",
        "description": "กระบอกบรรจุน้ำกลั่นสเตอร์ไรด์เพื่อเพิ่มความชื้นให้กับก๊าซออกซิเจน ป้องกันเยื่อบุทางเดินหายใจแห้ง",
    },
    "sterile_water": {
        "id": "sterile_water",
        "name_th": "น้ำกลั่นสเตอร์ไรด์",
        "name_en": "Sterile Water for Inhalation / Flush",
        "image": "images/equipment/sterile_water.png",
        "description": "น้ำกลั่นปราศจากเชื้อ ปราศจากสารไพโรเจน สำหรับเติมกระบอกความชื้นและล้างสายดูดเสมหะ",
    },
    "pulse_oximeter": {
        "id": "pulse_oximeter",
        "name_th": "เครื่องวัดความอิ่มตัวออกซิเจนที่ปลายนิ้ว",
        "name_en": "Pulse Oximeter",
        "image": "images/equipment/pulse_oximeter.jpg",
        "description": "อุปกรณ์หนีบปลายนิ้วเพื่อประเมินค่า SpO2 และชีพจร (Heart Rate) แบบต่อเนื่อง",
    },
    "nebulizer_chamber": {
        "id": "nebulizer_chamber",
        "name_th": "กระเปาะพ่นยาละอองฝอย",
        "name_en": "Nebulizer Chamber / Cup",
        "image": "images/equipment/nebulizer_chamber.png",
        "description": "กระเปาะบรรจุยาพ่นขยายหลอดลมพร้อมแผ่นกระจายละอองฝอย เพื่อสร้างละอองอนุภาคขนาดเล็กเข้าสู่ปอด",
    },
    "nebulizer_mask": {
        "id": "nebulizer_mask",
        "name_th": "หน้ากากพ่นยาพร้อมสายออกซิเจน",
        "name_en": "Nebulizer Mask with Tubing",
        "image": "images/equipment/nebulizer_mask.jpg",
        "description": "หน้ากากพ่นยาละอองฝอยพร้อมสายออกซิเจน (Tubing) สำหรับต่อกับกระเปาะพ่นยาและ Oxygen Flowmeter",
    },
    "air_compressor": {
        "id": "air_compressor",
        "name_th": "เครื่องอัดอากาศ",
        "name_en": "Air Compressor Nebulizer Pump",
        "image": "images/equipment/air_compressor.png",
        "description": "เครื่องปั๊มอัดอากาศทางการแพทย์สำหรับขับเคลื่อนยาพ่นฝอยละออง โดยไม่เพิ่มความเข้มข้นออกซิเจนในเลือดเกินจำเป็น",
    },
    "medication_vial": {
        "id": "medication_vial",
        "name_th": "ยาพ่นขยายหลอดลมตามคำสั่งแพทย์",
        "name_en": "Bronchodilator Nebule (Ventolin/Berodual)",
        "image": "images/equipment/bronchodilator_nebule.jpg",
        "description": "ยาพ่นขยายหลอดลมหลอดพลาสติกเดี่ยว (Single dose) ตรวจสอบตามหลัก 10 Rights ก่อนเปิดใช้",
    },
    "stethoscope": {
        "id": "stethoscope",
        "name_th": "หูฟังของแพทย์/พยาบาล (สเตทโทสโคป)",
        "name_en": "Stethoscope",
        "image": "images/equipment/stethoscope.png",
        "description": "ใช้ฟังเสียงหายใจและเสียงปอด (Breath sounds) เพื่อประเมิน Wheezing หรือ Rhonchi ก่อนและหลังทำหัตถการ",
    },
    "suction_catheter": {
        "id": "suction_catheter",
        "name_th": "สายดูดเสมหะปราศจากเชื้อ",
        "name_en": "Sterile Suction Catheter",
        "image": "images/equipment/suction_catheter.jpg",
        "description": "สายดูดเสมหะปลอดเชื้อในซองปิดสนิท ขนาดเหมาะสมกับผู้ป่วย (ไม่เกิน 1/2 ของขนาดท่อหลอดลมคอ)",
    },
    "sterile_gloves": {
        "id": "sterile_gloves",
        "name_th": "ถุงมือสเตอร์ไรด์ปราศจากเชื้อ",
        "name_en": "Sterile Surgical Gloves",
        "image": "images/equipment/sterile_gloves.svg",
        "description": "ถุงมือผ่าตัดปลอดเชื้อสำหรับจับสายดูดเสมหะด้วยมือข้างเด่น ป้องกันการติดเชื้อเข้าสู่ทางเดินหายใจ (Aseptic technique)",
    },
    "suction_machine": {
        "id": "suction_machine",
        "name_th": "เครื่องดูดเสมหะและสายต่อ",
        "name_en": "Suction Machine & Tubing",
        "image": "images/equipment/suction_machine.jpg",
        "description": "เครื่องสร้างแรงดูดสุญญากาศ พร้อมสายยางต่อ (Connecting tube) ปรับแรงดูดในผู้ใหญ่ 100-120 mmHg",
    },
    "suction_bottle": {
        "id": "suction_bottle",
        "name_th": "ขวดรองรับเสมหะ",
        "name_en": "Suction Collection Bottle",
        "image": "images/equipment/ward_suction_bottle.png",
        "description": "ขวดสุญญากาศสำหรับกักเก็บเสมหะและของเหลวที่ดูดออกมาเพื่อสังเกตสี ลักษณะ และปริมาณ",
    },
    "gauze_pads": {
        "id": "gauze_pads",
        "name_th": "ผ้าก๊อซปราศจากเชื้อ",
        "name_en": "Sterile Gauze Pads (4x4)",
        "image": "images/equipment/gauze_pads.svg",
        "description": "ผ้าก๊อซปลอดเชื้อสำหรับเช็ดปลายสายดูดเสมหะ และทำความสะอาดรอบช่องเปิดหลอดลมคอ",
    },
}

# Procedure Basket Configurations
PROCEDURE_BASKETS: dict[str, dict[str, Any]] = {
    "oxygen": {
        "id": "oxygen",
        "title": "ตะกร้าที่ 1: หัตถการให้ออกซิเจน (Oxygen Therapy)",
        "room_ref": "502",
        "room_name": "Room 502 (คุณมาลี)",
        "badge_name": "Oxygen Pack Master",
        "description": "จัดเตรียมอุปกรณ์สำหรับการให้ออกซิเจนทางจมูก (Nasal Cannula) และประเมินสัญญาณชีพ",
        "target_procedure": "การให้ออกซิเจนทางจมูก (Nasal Cannula) อัตรา 2-4 ลิตร/นาที",
        "required_item_ids": [
            "nasal_cannula",
            "o2_flowmeter",
            "humidifier_bottle",
            "sterile_water",
            "pulse_oximeter",
        ],
        "distractor_item_ids": [
            "suction_catheter",
            "medication_vial",
            "air_compressor",
        ],
        "clinical_tips": "การให้ออกซิเจนทางจมูก ต้องมีกระบอกน้ำให้ความชื้นบรรจุน้ำกลั่นสเตอร์ไรด์ และเครื่องวัด SpO2 เพื่อติดตามผลเสมอ ไม่ใช้สายดูดเสมหะหรือยาพ่นในหัตถการนี้",
    },
    "nebulization": {
        "id": "nebulization",
        "title": "ตะกร้าที่ 2: หัตถการพ่นยาละอองฝอย (Nebulization Therapy)",
        "room_ref": "503",
        "room_name": "Room 503 (คุณมะลิ)",
        "badge_name": "Nebulizer Pack Master",
        "description": "จัดเตรียมชุดพ่นยาละอองฝอยต่อออกซิเจนผนัง (Oxygen Flowmeter 6-8 L/min) พร้อมประเมินเสียงปอด",
        "target_procedure": "การพ่นยาขยายหลอดลมผ่านออกซิเจน (Oxygen-driven Nebulization 6-8 L/min)",
        "required_item_ids": [
            "nebulizer_chamber",
            "nebulizer_mask",
            "o2_flowmeter",
            "medication_vial",
            "stethoscope",
            "pulse_oximeter",
        ],
        "distractor_item_ids": [
            "air_compressor",
            "suction_machine",
            "humidifier_bottle",
            "simple_mask",
        ],
        "clinical_tips": "การพ่นยาละอองฝอยผ่าน Oxygen wall ต้องใช้ Oxygen Flowmeter ปรับอัตราไหล 6-8 ลิตร/นาที ต่อสายตรงเข้ากระเปาะพ่นยา (ไม่ผ่านกระบอกน้ำให้ความชื้น) และประเมินเสียงปอดและ SpO2 ทั้งก่อน-หลังพ่นยาเสมอ",
    },
    "suction": {
        "id": "suction",
        "title": "ตะกร้าที่ 3: หัตถการดูดเสมหะ (Airway Suctioning)",
        "room_ref": "501",
        "room_name": "Room 501 (คุณสมชาย)",
        "badge_name": "Suction Pack Master",
        "description": "จัดเตรียมอุปกรณ์ดูดเสมหะทางท่อหลอดลมคอด้วยเทคนิคปลอดเชื้อ (Aseptic Technique) อย่างถูกต้องครบถ้วน",
        "target_procedure": "การดูดเสมหะทางท่อหลอดลมคอ (Tracheostomy Tube Suctioning)",
        "required_item_ids": [
            "suction_catheter",
            "sterile_gloves",
            "suction_machine",
            "suction_bottle",
            "sterile_water",
            "gauze_pads",
        ],
        "distractor_item_ids": [
            "nasal_cannula",
            "nebulizer_chamber",
            "venturi_mask",
        ],
        "clinical_tips": "การดูดเสมหะทางท่อเจาะคอต้องยึดหลัก Sterile Technique เคร่งครัด ต้องมีถุงมือสเตอร์ไรด์ สายดูดปลอดเชื้อ น้ำกลั่นสเตอร์ไรด์ล้างสาย และผ้าก๊อซเช็ดทำความสะอาด",
    },
}


def get_basket_details(basket_id: str) -> dict[str, Any] | None:
    """Retrieve full configuration and shuffled items for a given procedure basket."""
    cfg = PROCEDURE_BASKETS.get(basket_id)
    if not cfg:
        return None

    all_item_ids = cfg["required_item_ids"] + cfg["distractor_item_ids"]
    items = [EQUIPMENT_CATALOG[item_id] for item_id in all_item_ids if item_id in EQUIPMENT_CATALOG]

    return {
        **cfg,
        "equipment_items": items,
        "total_required": len(cfg["required_item_ids"]),
    }


def verify_basket_submission(basket_id: str, packed_ids: list[str]) -> dict[str, Any]:
    """Verify packed items in procedure basket, detecting missing essentials and distractors."""
    cfg = PROCEDURE_BASKETS.get(basket_id)
    if not cfg:
        return {"success": False, "error": "ไม่พบข้อมูลตะกร้าหัตถการนี้"}

    required_set = set(cfg["required_item_ids"])
    distractor_set = set(cfg["distractor_item_ids"])
    packed_set = set(packed_ids)

    missing_ids = list(required_set - packed_set)
    extra_distractor_ids = list(packed_set & distractor_set)
    correct_packed_ids = list(packed_set & required_set)

    is_complete = len(missing_ids) == 0 and len(extra_distractor_ids) == 0

    # Build human-readable clinical rationale feedback
    feedback_messages = []
    if is_complete:
        feedback_messages.append(
            f"ยอดเยี่ยมมาก! คุณจัดเตรียมอุปกรณ์ใน {cfg['title']} ได้ถูกต้องครบถ้วนทั้ง {len(required_set)} รายการ และไม่มีอุปกรณ์แปลกปลอมปะปน"
        )
    else:
        if missing_ids:
            missing_names = [EQUIPMENT_CATALOG[m]["name_th"] for m in missing_ids if m in EQUIPMENT_CATALOG]
            feedback_messages.append(
                f"⚠️ ยังขาดอุปกรณ์จำเป็น {len(missing_ids)} ชิ้น: {', '.join(missing_names)}"
            )
        if extra_distractor_ids:
            extra_names = [EQUIPMENT_CATALOG[e]["name_th"] for e in extra_distractor_ids if e in EQUIPMENT_CATALOG]
            feedback_messages.append(
                f"❌ มีอุปกรณ์ที่ไม่จำเป็น/ไม่ถูกต้องในหัตถการนี้ปะปนมา {len(extra_distractor_ids)} ชิ้น: {', '.join(extra_names)}"
            )

    return {
        "success": True,
        "is_complete": is_complete,
        "score_percent": int((len(correct_packed_ids) / len(required_set)) * 100) if required_set else 0,
        "correct_count": len(correct_packed_ids),
        "total_required": len(required_set),
        "missing_items": [EQUIPMENT_CATALOG[m] for m in missing_ids if m in EQUIPMENT_CATALOG],
        "distractor_items": [EQUIPMENT_CATALOG[e] for e in extra_distractor_ids if e in EQUIPMENT_CATALOG],
        "feedback": " ".join(feedback_messages),
        "clinical_tips": cfg["clinical_tips"],
    }
