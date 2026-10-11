"""Automated tests for Microsoft 365 Entra ID login portal and role authentication."""

from __future__ import annotations

from sqlalchemy import select
from app.extensions import db
from app.models.user import User, UserRole


def test_login_page_renders_clean_form_without_role_tabs(client):
    """Verify login page renders the clean mockup design with username/password inputs and NO role tabs."""
    res = client.get("/login")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Core elements matching user mockup
    assert "ยินดีต้อนรับสู่ BreathQuest" in html
    assert "ชื่อผู้ใช้ (Username)" in html
    assert "รหัสผ่าน (Password)" in html
    assert "เข้าสู่ระบบ" in html
    assert "@nursingmu.org" in html
    assert "Microsoft 365" in html
    assert "ทดลองใช้งานแบบไม่ระบุตัวตน (Guest Practice Mode)" in html

    # Role selection tabs must NOT be present
    assert "เลือกบทบาท (Role)" not in html
    assert 'role="tablist"' not in html
    assert 'id="role-tabs"' not in html


def test_detect_role_from_username_logic():
    """Verify detect_role_from_username correctly routes usernames to student, faculty, or admin."""
    from app.routes.auth import detect_role_from_username

    # Student patterns
    assert detect_role_from_username("6601234") == "student"
    assert detect_role_from_username("u6609999") == "student"
    assert detect_role_from_username("somying.s@nursingmu.org") == "student"

    # Faculty patterns
    assert detect_role_from_username("aj.prasert") == "faculty"
    assert detect_role_from_username("prof.wilai@nursingmu.org") == "faculty"
    assert detect_role_from_username("dr.suda") == "faculty"
    assert detect_role_from_username("instructor.somchai") == "faculty"

    # Admin patterns
    assert detect_role_from_username("admin") == "admin"
    assert detect_role_from_username("sysadmin@nursingmu.org") == "admin"
    assert detect_role_from_username("admin_nurse") == "admin"


def test_standard_login_auto_detects_student_and_faculty(client, app):
    """Standard credential login automatically assigns appropriate role based on username."""
    # 1. Student login
    res_student = client.post(
        "/auth/login",
        data={"username": "6601234", "password": "password123"},
        follow_redirects=True,
    )
    assert res_student.status_code == 200
    with app.app_context():
        u_student = db.session.execute(
            select(User).where(User.email == "6601234@nursingmu.org")
        ).scalars().first()
        assert u_student is not None
        assert u_student.role == UserRole.STUDENT.value

    # 2. Faculty login
    res_faculty = client.post(
        "/auth/login",
        data={"username": "aj.chatchai", "password": "password123"},
        follow_redirects=True,
    )
    assert res_faculty.status_code == 200
    with app.app_context():
        u_faculty = db.session.execute(
            select(User).where(User.email == "aj.chatchai@nursingmu.org")
        ).scalars().first()
        assert u_faculty is not None
        assert u_faculty.role == UserRole.FACULTY.value


def test_microsoft_login_rejects_invalid_domain(client):
    """Attempting login with external email (e.g. @gmail.com) must be rejected."""
    res = client.post(
        "/auth/microsoft",
        data={"email": "hacker@gmail.com", "role": "student"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "อีเมลต้องลงท้ายด้วย @nursingmu.org เท่านั้น" in html


def test_microsoft_login_accepts_valid_nursingmu_email(client, app):
    """Attempting login with @nursingmu.org succeeds and creates/authenticates student."""
    res = client.post(
        "/auth/microsoft",
        data={"email": "somying.s@nursingmu.org", "role": "student"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "/ward" in res.request.path

    with app.app_context():
        user = db.session.execute(
            select(User).where(User.email == "somying.s@nursingmu.org")
        ).scalars().first()
        assert user is not None
        assert user.role == UserRole.STUDENT.value
        assert user.is_student() is True


def test_microsoft_login_faculty_role(client, app):
    """Faculty login via Microsoft 365 sets faculty role and session."""
    res = client.post(
        "/auth/microsoft",
        data={"email": "aj.prasert@nursingmu.org", "role": "faculty"},
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        user = db.session.execute(
            select(User).where(User.email == "aj.prasert@nursingmu.org")
        ).scalars().first()
        assert user is not None
        assert user.role == UserRole.FACULTY.value
        assert user.is_faculty() is True


def test_emergency_local_admin_login(client, app):
    """Emergency local admin login succeeds with credentials."""
    # Invalid password fails
    res_fail = client.post(
        "/auth/admin/login",
        data={"username": "admin", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert res_fail.status_code == 200
    assert "ชื่อผู้ใช้หรือรหัสผ่านผู้ดูแลระบบไม่ถูกต้อง" in res_fail.get_data(as_text=True)

    # Valid emergency credentials succeed
    res_ok = client.post(
        "/auth/admin/login",
        data={"username": "admin", "password": "nursingmu2026"},
        follow_redirects=True,
    )
    assert res_ok.status_code == 200
    assert "/ward" in res_ok.request.path


def test_logout_clears_session(client):
    """Logging out clears session and redirects to home."""
    # First log in
    client.post(
        "/auth/microsoft",
        data={"email": "test.logout@nursingmu.org", "role": "student"},
    )
    # Then log out
    res = client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "ออกจากระบบเรียบร้อยแล้ว" in html


def test_faculty_and_student_custom_password_rules(client, app):
    """Verify Faculty (Nsmu+09) and Student (Nsmu+b<cohort>) password requirements."""
    # 1. Faculty with wrong password fails
    res_fac_fail = client.post(
        "/auth/login",
        data={"username": "aj.somporn", "password": "WrongPassword"},
        follow_redirects=True,
    )
    assert res_fac_fail.status_code == 200
    assert "รหัสผ่านอาจารย์ไม่ถูกต้อง" in res_fac_fail.get_data(as_text=True)

    # Faculty with correct Nsmu+09 succeeds
    res_fac_ok = client.post(
        "/auth/login",
        data={"username": "aj.somporn", "password": "Nsmu+09"},
        follow_redirects=True,
    )
    assert res_fac_ok.status_code == 200
    assert "/ward" in res_fac_ok.request.path

    # 2. Student 6809001 with wrong password fails
    res_std_fail = client.post(
        "/auth/login",
        data={"username": "6809001", "password": "WrongPassword"},
        follow_redirects=True,
    )
    assert res_std_fail.status_code == 200
    assert "รหัสผ่านนักศึกษาไม่ถูกต้อง" in res_std_fail.get_data(as_text=True)
    assert "Nsmu+b68" in res_std_fail.get_data(as_text=True)

    # Student 6809001 with Nsmu+b68 succeeds
    res_std_ok = client.post(
        "/auth/login",
        data={"username": "6809001", "password": "Nsmu+b68"},
        follow_redirects=True,
    )
    assert res_std_ok.status_code == 200
    assert "/ward" in res_std_ok.request.path

