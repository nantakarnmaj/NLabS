"""Tests for Admin authentication (Nsit+2026), access control, and user roster import."""

from __future__ import annotations

from sqlalchemy import select
from app.extensions import db
from app.models.user import User, UserRole


def test_admin_login_with_nsit_password(client, app):
    """Verify admin logs in with username 'admin' and password 'Nsit+2026'."""
    # 1. Incorrect password must fail
    res_wrong = client.post(
        "/auth/login",
        data={"username": "admin", "password": "WrongPassword123"},
        follow_redirects=True,
    )
    assert res_wrong.status_code == 200
    assert "รหัสผ่านผู้ดูแลระบบไม่ถูกต้อง" in res_wrong.get_data(as_text=True)

    # 2. Correct password 'Nsit+2026' succeeds and redirects to admin dashboard
    res_ok = client.post(
        "/auth/login",
        data={"username": "admin", "password": "Nsit+2026"},
        follow_redirects=True,
    )
    assert res_ok.status_code == 200
    assert "/admin/users" in res_ok.request.path
    html = res_ok.get_data(as_text=True)
    assert "จัดการรายชื่ออาจารย์และนักศึกษา" in html
    assert "ผู้ดูแลระบบ" in html


def test_admin_access_control_unauthenticated_and_student_blocked(client):
    """Unauthenticated users or student accounts cannot access /admin/users."""
    # Unauthenticated -> redirect to login
    res_guest = client.get("/admin/users", follow_redirects=True)
    assert res_guest.status_code == 200
    assert "กรุณาเข้าสู่ระบบด้วยบัญชีผู้ดูแลระบบ" in res_guest.get_data(as_text=True)

    # Student login -> blocked from admin
    client.post(
        "/auth/login",
        data={"username": "6601999", "password": "anypassword"},
    )
    res_student = client.get("/admin/users", follow_redirects=True)
    assert res_student.status_code == 200
    assert "เฉพาะผู้ดูแลระบบ (Admin) เท่านั้น" in res_student.get_data(as_text=True)


def test_admin_add_single_user(client, app):
    """Admin can manually add a student and an instructor."""
    # Log in as admin
    client.post(
        "/auth/login",
        data={"username": "admin", "password": "Nsit+2026"},
    )

    # Add student
    res_student = client.post(
        "/admin/users/add",
        data={
            "identifier": "6608888",
            "name": "นางสาววิไลลักษณ์ พยาบาลฝึกหัด",
            "role": "student",
        },
        follow_redirects=True,
    )
    assert res_student.status_code == 200
    assert "เพิ่มผู้ใช้ นางสาววิไลลักษณ์ พยาบาลฝึกหัด" in res_student.get_data(as_text=True)

    with app.app_context():
        u = db.session.execute(select(User).where(User.email == "6608888@nursingmu.org")).scalars().first()
        assert u is not None
        assert u.name == "นางสาววิไลลักษณ์ พยาบาลฝึกหัด"
        assert u.role == UserRole.STUDENT.value

    # Add faculty
    res_faculty = client.post(
        "/admin/users/add",
        data={
            "identifier": "aj.kamon",
            "name": "อ.กมล เวชศาสตร์",
            "role": "faculty",
        },
        follow_redirects=True,
    )
    assert res_faculty.status_code == 200
    assert "เพิ่มผู้ใช้ อ.กมล เวชศาสตร์" in res_faculty.get_data(as_text=True)

    with app.app_context():
        u_fac = db.session.execute(select(User).where(User.email == "aj.kamon@nursingmu.org")).scalars().first()
        assert u_fac is not None
        assert u_fac.role == UserRole.FACULTY.value


def test_admin_batch_import_users(client, app):
    """Admin can import multiple students and faculty via text lines."""
    client.post(
        "/auth/login",
        data={"username": "admin", "password": "Nsit+2026"},
    )

    batch_payload = (
        "6607001, สมชาย สุขเกษม, student\n"
        "6607002, สมหญิง มั่นคง, student\n"
        "aj.orapin, ดร.อรพินท์ ศาสตร์พยาบาล, faculty\n"
        "6607003, มานะ อดทน\n"
    )

    res = client.post(
        "/admin/users/import",
        data={
            "default_role": "student",
            "batch_text": batch_payload,
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "นำเข้ารายชื่อสำเร็จทั้งหมด 4 คน" in res.get_data(as_text=True)

    with app.app_context():
        s1 = db.session.execute(select(User).where(User.email == "6607001@nursingmu.org")).scalars().first()
        assert s1 is not None
        assert s1.name == "สมชาย สุขเกษม"
        assert s1.role == "student"

        f1 = db.session.execute(select(User).where(User.email == "aj.orapin@nursingmu.org")).scalars().first()
        assert f1 is not None
        assert f1.name == "ดร.อรพินท์ ศาสตร์พยาบาล"
        assert f1.role == "faculty"

        s3 = db.session.execute(select(User).where(User.email == "6607003@nursingmu.org")).scalars().first()
        assert s3 is not None
        assert s3.name == "มานะ อดทน"
        assert s3.role == "student"  # default role applied
