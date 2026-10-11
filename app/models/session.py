"""StudentSession model for pseudonymous browser sessions."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.extensions import db


class StudentSession(db.Model):
    """Anonymous/pseudonymous session record bound to a browser via hashed token."""

    __tablename__ = "student_sessions"

    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(64), unique=True, index=True, nullable=False)
    nickname = db.Column(db.String(64), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_active_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    # Relationships
    progress_records = relationship(
        "MissionProgress",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    @property
    def is_expired(self) -> bool:
        """Check whether the session has passed its expiration time."""
        now = datetime.now(timezone.utc)
        # Handle SQLite naive datetimes by ensuring comparison is timezone-aware
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

    def __repr__(self) -> str:
        return f"<StudentSession id={self.id} expires={self.expires_at}>"
