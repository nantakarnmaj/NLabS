"""MissionRun, ActivityProgress, and ActivityAttempt models for tracking replayable playthroughs."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from app.extensions import db


class MissionRun(db.Model):
    """A distinct playthrough run of a mission by a learner session."""

    __tablename__ = "mission_runs"

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
    scenario_id = db.Column(
        db.Integer,
        db.ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Status: 'in_progress', 'completed', 'abandoned'
    status = db.Column(db.String(32), default="in_progress", nullable=False)
    current_activity_id = db.Column(
        db.Integer,
        db.ForeignKey("activities.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Current active patient state (spo2, rr, hr, distress, secretions, etc.)
    patient_state_json = db.Column(db.JSON, default=dict, nullable=False)
    # Monotonic revision counter for conflict detection
    state_revision = db.Column(db.Integer, default=1, nullable=False)
    started_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
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

    # Relationships
    session = relationship("StudentSession", backref=db.backref("runs", cascade="all, delete-orphan", lazy="dynamic"))
    mission = relationship("Mission")
    scenario = relationship("Scenario")
    current_activity = relationship("Activity", foreign_keys=[current_activity_id])
    activity_progresses = relationship(
        "ActivityProgress",
        back_populates="mission_run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    attempts = relationship(
        "ActivityAttempt",
        back_populates="mission_run",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<MissionRun id={self.id} mission={self.mission_id} status={self.status} rev={self.state_revision}>"


class ActivityProgress(db.Model):
    """Completion evidence for a specific activity within a mission run."""

    __tablename__ = "activity_progress"

    id = db.Column(db.Integer, primary_key=True)
    mission_run_id = db.Column(
        db.Integer,
        db.ForeignKey("mission_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id = db.Column(
        db.Integer,
        db.ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_completed = db.Column(db.Boolean, default=True, nullable=False)
    completion_evidence_json = db.Column(db.JSON, default=dict, nullable=False)
    completed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    mission_run = relationship("MissionRun", back_populates="activity_progresses")
    activity = relationship("Activity")

    __table_args__ = (
        UniqueConstraint("mission_run_id", "activity_id", name="uq_run_activity_progress"),
    )

    def __repr__(self) -> str:
        return f"<ActivityProgress run={self.mission_run_id} act={self.activity_id}>"


class ActivityAttempt(db.Model):
    """Log of a student's submission for an activity within a mission run."""

    __tablename__ = "activity_attempts"

    id = db.Column(db.Integer, primary_key=True)
    mission_run_id = db.Column(
        db.Integer,
        db.ForeignKey("mission_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id = db.Column(
        db.Integer,
        db.ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number = db.Column(db.Integer, default=1, nullable=False)
    response_json = db.Column(db.JSON, nullable=False)
    result_type = db.Column(db.String(32), nullable=False)  # 'success', 'retry', 'guidance'
    idempotency_key = db.Column(db.String(64), nullable=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    mission_run = relationship("MissionRun", back_populates="attempts")
    activity = relationship("Activity")

    def __repr__(self) -> str:
        return f"<ActivityAttempt run={self.mission_run_id} act={self.activity_id} num={self.attempt_number} res={self.result_type}>"
