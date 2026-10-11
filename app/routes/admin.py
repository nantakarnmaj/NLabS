"""Admin management routes for user roster, importing students and faculty."""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from functools import wraps
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import select, func

from app.extensions import db
from app.models.user import User, UserRole
from app.routes.auth import get_current_user, is_valid_nursingmu_email, detect_role_from_username

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator to require authenticated administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            flash("กรุณาเข้าสู่ระบบด้วยบัญชีผู้ดูแลระบบ (Admin) ก่อนเข้าใช้งาน", "error")
            return redirect(url_for("auth.login"))
        if not current_user.is_admin():
            flash("เฉพาะผู้ดูแลระบบ (Admin) เท่านั้นที่สามารถเข้าถึงส่วนนี้ได้", "error")
            return redirect(url_for("main.ward"))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("", methods=["GET"])
@admin_required
def index():
    """Redirect to user management by default."""
    return redirect(url_for("admin.users"))


@admin_bp.route("/users", methods=["GET"])
@admin_required
def users():
    """Display user management and roster dashboard."""
    search_query = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "").strip()

    stmt = select(User).order_by(User.created_at.desc())
    if role_filter in [r.value for r in UserRole]:
        stmt = stmt.where(User.role == role_filter)
    if search_query:
        search_pattern = f"%{search_query}%"
        stmt = stmt.where(
            (User.name.ilike(search_pattern))
            | (User.email.ilike(search_pattern))
            | (User.student_id.ilike(search_pattern))
        )

    user_list = db.session.execute(stmt).scalars().all()

    # User statistics
    total_users = db.session.execute(select(func.count(User.id))).scalar_one()
    student_count = db.session.execute(
        select(func.count(User.id)).where(User.role == UserRole.STUDENT.value)
    ).scalar_one()
    faculty_count = db.session.execute(
        select(func.count(User.id)).where(User.role == UserRole.FACULTY.value)
    ).scalar_one()
    admin_count = db.session.execute(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN.value)
    ).scalar_one()

    tenant_domain = current_app.config.get("M365_TENANT_DOMAIN", "nursingmu.org")

    return render_template(
        "admin/users.html",
        users=user_list,
        total_users=total_users,
        student_count=student_count,
        faculty_count=faculty_count,
        admin_count=admin_count,
        search_query=search_query,
        role_filter=role_filter,
        tenant_domain=tenant_domain,
    )


@admin_bp.route("/users/add", methods=["POST"])
@admin_required
def add_user():
    """Add a single user manually."""
    identifier = request.form.get("identifier", "").strip()
    name = request.form.get("name", "").strip()
    role = request.form.get("role", UserRole.STUDENT.value).strip()
    tenant_domain = current_app.config.get("M365_TENANT_DOMAIN", "nursingmu.org")

    if not identifier:
        flash("กรุณาระบุรหัสนักศึกษา หรืออีเมล", "error")
        return redirect(url_for("admin.users"))

    # Normalize email
    if "@" in identifier:
        email = identifier.lower()
    else:
        email = f"{identifier.lower()}@{tenant_domain}"

    student_id = identifier if not "@" in identifier else identifier.split("@")[0]
    display_name = name or student_id

    # Check existing
    existing = db.session.execute(select(User).where(User.email == email)).scalars().first()
    if existing:
        existing.name = display_name
        existing.role = role
        existing.student_id = student_id
        db.session.commit()
        flash(f"อัปเดตข้อมูลผู้ใช้ {display_name} ({email}) เรียบร้อยแล้ว", "success")
    else:
        new_user = User(
            email=email,
            name=display_name,
            role=role,
            student_id=student_id,
            department="คณะพยาบาลศาสตร์",
            last_login_at=None,
        )
        db.session.add(new_user)
        db.session.commit()
        flash(f"เพิ่มผู้ใช้ {display_name} ({email}) สำเร็จ", "success")

    return redirect(url_for("admin.users"))


@admin_bp.route("/users/import", methods=["POST"])
@admin_required
def import_users():
    """Bulk import students and faculty from text or CSV file."""
    default_role = request.form.get("default_role", UserRole.STUDENT.value).strip()
    batch_text = request.form.get("batch_text", "").strip()
    uploaded_file = request.files.get("file")
    tenant_domain = current_app.config.get("M365_TENANT_DOMAIN", "nursingmu.org")

    content_lines: list[str] = []

    # Read from uploaded file if provided
    if uploaded_file and uploaded_file.filename:
        try:
            stream = io.StringIO(uploaded_file.stream.read().decode("utf-8-sig", errors="replace"))
            content_lines = stream.readlines()
        except Exception as e:
            logger.error("Error reading uploaded import file: %s", e)
            flash("ไม่สามารถอ่านไฟล์ที่อัปโหลดได้ โปรดตรวจสอบว่าเป็นไฟล์ UTF-8 Text หรือ CSV", "error")
            return redirect(url_for("admin.users"))
    elif batch_text:
        content_lines = batch_text.splitlines()

    if not content_lines:
        flash("กรุณากรอกข้อความรายชื่อ หรือเลือกไฟล์ CSV เพื่อนำเข้า", "error")
        return redirect(url_for("admin.users"))

    created_count = 0
    updated_count = 0
    skipped_count = 0

    for line_num, raw_line in enumerate(content_lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Split by comma, tab, or semicolon
        if "\t" in line:
            parts = [p.strip().strip('"').strip("'") for p in line.split("\t")]
        elif ";" in line:
            parts = [p.strip().strip('"').strip("'") for p in line.split(";")]
        elif "," in line:
            # Use csv reader to respect quotes
            try:
                reader = csv.reader([line])
                parts = [p.strip() for p in next(reader)]
            except Exception:
                parts = [p.strip().strip('"').strip("'") for p in line.split(",")]
        else:
            # Single item per line
            parts = [line]

        if not parts or not parts[0]:
            continue

        raw_id = parts[0]
        # Ignore header line if present
        if raw_id.lower() in ["id", "username", "email", "student_id", "รหัส", "ชื่อผู้ใช้", "รหัสนักศึกษา"]:
            continue

        # Determine email and student_id
        if "@" in raw_id:
            email = raw_id.lower()
            student_id = raw_id.split("@")[0]
        else:
            email = f"{raw_id.lower()}@{tenant_domain}"
            student_id = raw_id

        # Determine name
        if len(parts) >= 2 and parts[1]:
            name = parts[1]
        else:
            name = student_id

        # Determine role
        if len(parts) >= 3 and parts[2].lower() in [r.value for r in UserRole]:
            role = parts[2].lower()
        else:
            detected = detect_role_from_username(raw_id)
            if detected != UserRole.STUDENT.value:
                role = detected
            else:
                role = default_role

        # Upsert into database
        existing = db.session.execute(select(User).where(User.email == email)).scalars().first()
        if existing:
            existing.name = name
            existing.role = role
            existing.student_id = student_id
            updated_count += 1
        else:
            new_user = User(
                email=email,
                name=name,
                role=role,
                student_id=student_id,
                department="คณะพยาบาลศาสตร์",
                last_login_at=None,
            )
            db.session.add(new_user)
            created_count += 1

    try:
        db.session.commit()
        total_processed = created_count + updated_count
        flash(
            f"นำเข้ารายชื่อสำเร็จทั้งหมด {total_processed} คน (เพิ่มใหม่ {created_count} คน, อัปเดต {updated_count} คน)",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to commit imported users: %s", e)
        flash(f"เกิดข้อผิดพลาดในการบันทึกรายชื่อ: {e}", "error")

    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    """Delete a user account."""
    current_user = get_current_user()
    if current_user and current_user.id == user_id:
        flash("ไม่สามารถลบบัญชีผู้ดูแลระบบที่กำลังใช้งานอยู่ได้", "error")
        return redirect(url_for("admin.users"))

    user = db.session.get(User, user_id)
    if not user:
        flash("ไม่พบข้อมูลผู้ใช้นี้ในระบบ", "error")
        return redirect(url_for("admin.users"))

    user_name = user.name
    db.session.delete(user)
    db.session.commit()
    flash(f"ลบผู้ใช้ {user_name} เรียบร้อยแล้ว", "success")
    return redirect(url_for("admin.users"))
