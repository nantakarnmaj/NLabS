"""Tests for Equipment Station matching and procedure basket verification."""

from __future__ import annotations

import json
from app.services.equipment_service import PROCEDURE_BASKETS


def test_equipment_station_page_renders_successfully(client):
    """GET /equipment-station renders the station workbench with all baskets."""
    res = client.get("/equipment-station")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    assert "ห้องเตรียมอุปกรณ์หัตถการ" in html
    assert "ตะกร้าที่ 1: หัตถการดูดเสมหะ" in html
    assert "ตะกร้าเตรียมอุปกรณ์หัตถการ" in html
    assert "รูปถ่ายอุปกรณ์จริง" in html


def test_equipment_station_tab_switching(client):
    """Switching query param basket loads corresponding procedure basket."""
    # Nebulization tray
    res_neb = client.get("/equipment-station?basket=nebulization")
    assert res_neb.status_code == 200
    html_neb = res_neb.get_data(as_text=True)
    assert "หัตถการพ่นยาละอองฝอย" in html_neb

    # Suction tray
    res_suction = client.get("/equipment-station?basket=suction")
    assert res_suction.status_code == 200
    html_suction = res_suction.get_data(as_text=True)
    assert "หัตถการดูดเสมหะ" in html_suction


def test_verify_basket_submission_success(client):
    """POST /equipment-station/verify with full correct items returns is_complete True."""
    oxygen_cfg = PROCEDURE_BASKETS["oxygen"]
    correct_ids = oxygen_cfg["required_item_ids"]

    res = client.post(
        "/equipment-station/verify",
        data=json.dumps({
            "basket_id": "oxygen",
            "packed_ids": correct_ids,
        }),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["is_complete"] is True
    assert data["score_percent"] == 100
    assert len(data["missing_items"]) == 0
    assert len(data["distractor_items"]) == 0
    assert "ยอดเยี่ยมมาก" in data["feedback"]


def test_verify_basket_submission_with_missing_and_distractor(client):
    """POST /equipment-station/verify detects missing items and extra distractors."""
    # Submit only 1 required item and 1 distractor
    res = client.post(
        "/equipment-station/verify",
        data=json.dumps({
            "basket_id": "oxygen",
            "packed_ids": ["nasal_cannula", "suction_set"],
        }),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["is_complete"] is False
    assert len(data["missing_items"]) > 0
    assert len(data["distractor_items"]) == 1
    assert data["distractor_items"][0]["id"] == "suction_set"
    assert "ยังขาดอุปกรณ์จำเป็น" in data["feedback"]
    assert "มีอุปกรณ์ที่ไม่จำเป็น" in data["feedback"]


def test_verify_suction_basket_submission_success(client):
    """POST /equipment-station/verify with new suction items returns 100% complete."""
    suction_cfg = PROCEDURE_BASKETS["suction"]
    assert set(suction_cfg["required_item_ids"]) == {
        "suction_set", "sterile_cotton", "alcohol_70", "pulse_oximeter", "stethoscope"
    }

    res = client.post(
        "/equipment-station/verify",
        data=json.dumps({
            "basket_id": "suction",
            "packed_ids": suction_cfg["required_item_ids"],
        }),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["is_complete"] is True
    assert data["score_percent"] == 100
    assert len(data["missing_items"]) == 0
    assert len(data["distractor_items"]) == 0



def test_equipment_station_csp_compliance(client):
    """Ensure equipment station uses external assets and contains no inline scripts or onclicks."""
    res = client.get("/equipment-station")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Assets are linked externally
    assert "equipment.css" in html
    assert "equipment.js" in html

    # Strict CSP compliance
    assert "onclick=" not in html
    assert "<style" not in html

    # Any <script> tag must be json data container only, not executable inline script
    import re
    script_tags = re.findall(r"<script(.*?)>", html, re.IGNORECASE)
    for tag in script_tags:
        is_src = "src=" in tag
        is_json = 'type="application/json"' in tag
        assert is_src or is_json, f"Forbidden inline script tag detected: <script{tag}>"

