"""Badge and SessionBadge models for formative learning recognition."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from app.extensions import db


class Badge(db.Model):
    """Badge definition acknowledging participation and learning completion."""

    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, index=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(64), nullable=False)
    mission_id = db.Column(
        db.Integer,
        db.ForeignKey("missions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    mission = relationship("Mission")

    def __repr__(self) -> str:
        return f"<Badge id={self.id} slug={self.slug} name={self.name}>"


class SessionBadge(db.Model):
    """Record of a badge awarded to a student session."""

    __tablename__ = "session_badges"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("student_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    badge_id = db.Column(
        db.Integer,
        db.ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mission_run_id = db.Column(
        db.Integer,
        db.ForeignKey("mission_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    awarded_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    session = relationship("StudentSession", backref=db.backref("badges", cascade="all, delete-orphan", lazy="selectin"))
    badge = relationship("Badge", lazy="joined")
    mission_run = relationship("MissionRun")

    __table_args__ = (
        UniqueConstraint("session_id", "badge_id", name="uq_session_badge"),
    )

    def __repr__(self) -> str:
        return f"<SessionBadge session={self.session_id} badge={self.badge_id}>"
