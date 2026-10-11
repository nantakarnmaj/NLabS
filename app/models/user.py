"""User model for authenticated accounts (Student, Faculty, Admin)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from app.extensions import db


class UserRole(str, Enum):
    """User roles within BreathQuest learning portal."""
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"


class User(db.Model):
    """Authenticated user account supporting Microsoft 365 / Entra ID SSO."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=UserRole.STUDENT.value, nullable=False, index=True)
    
    # Microsoft 365 Entra ID subject/object identifier
    m365_oid = db.Column(db.String(255), unique=True, nullable=True, index=True)
    
    # Academic profile details
    student_id = db.Column(db.String(50), nullable=True, index=True)
    department = db.Column(db.String(100), default="คณะพยาบาลศาสตร์", nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    
    # Status flags
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT.value

    def is_faculty(self) -> bool:
        return self.role == UserRole.FACULTY.value

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    def get_role_display_th(self) -> str:
        """Return Thai role label for UI display."""
        mapping = {
            UserRole.STUDENT.value: "นักศึกษาพยาบาล",
            UserRole.FACULTY.value: "อาจารย์ / ผู้สอน",
            UserRole.ADMIN.value: "ผู้ดูแลระบบ",
        }
        return mapping.get(self.role, "ผู้ใช้งาน")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
