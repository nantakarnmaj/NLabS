"""Equipment Station routes for matching equipment pictures with names and packing procedure baskets."""

from __future__ import annotations

import logging
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)
from app.services.session_service import get_current_session, get_or_create_session
from app.services.equipment_service import (
    PROCEDURE_BASKETS,
    EQUIPMENT_CATALOG,
    get_basket_details,
    verify_basket_submission,
)

logger = logging.getLogger(__name__)

equipment_bp = Blueprint("equipment", __name__, url_prefix="/equipment-station")


@equipment_bp.route("", methods=["GET"])
def station_index():
    """Render the clinical equipment matching and basket preparation station."""
    session = get_current_session()
    basket_id = request.args.get("basket", "oxygen").lower()
    if basket_id not in PROCEDURE_BASKETS:
        basket_id = "oxygen"

    import random

    active_basket = get_basket_details(basket_id)
    shuffled_name_items = list(active_basket["equipment_items"]) if active_basket else []
    # Deterministic or random shuffle so images and names do not align in same order
    rng = random.Random()
    rng.shuffle(shuffled_name_items)

    return render_template(
        "equipment_station.html",
        session=session,
        baskets=PROCEDURE_BASKETS,
        active_basket_id=basket_id,
        active_basket=active_basket,
        shuffled_name_items=shuffled_name_items,
        catalog=EQUIPMENT_CATALOG,
    )


@equipment_bp.route("/verify", methods=["POST"])
def verify_basket():
    """Verify packed equipment in procedure basket and return clinical feedback."""
    data = request.get_json(silent=True) or {}
    basket_id = data.get("basket_id", "").strip().lower()
    packed_ids = data.get("packed_ids", [])

    if not basket_id or basket_id not in PROCEDURE_BASKETS:
        return jsonify({"success": False, "error": "ระบุตะกร้าหัตถการไม่ถูกต้อง"}), 400

    if not isinstance(packed_ids, list):
        return jsonify({"success": False, "error": "รูปแบบรายการอุปกรณ์ไม่ถูกต้อง"}), 400

    result = verify_basket_submission(basket_id, packed_ids)
    return jsonify(result)
