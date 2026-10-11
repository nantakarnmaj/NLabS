"""MissionProgress model tracking learner progress through ward missions."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from app.extensions import db


class MissionProgress(db.Model):
    """Lasting mission progress for a student session."""

    __tablename__ = "mission_progress"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("student_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mission_id = db.Column(
        db.Integer,
        db.ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Valid status: 'not_started', 'in_progress', 'completed'
    status = db.Column(db.String(32), default="not_started", nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    session = relationship("StudentSession", back_populates="progress_records")
    mission = relationship("Mission", back_populates="progress_records")

    __table_args__ = (
        UniqueConstraint("session_id", "mission_id", name="uq_session_mission_progress"),
    )

    def __repr__(self) -> str:
        return f"<MissionProgress session={self.session_id} mission={self.mission_id} status={self.status}>"
