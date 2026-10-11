"""Scenario model representing clinical case scenarios."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.extensions import db


class Scenario(db.Model):
    """Clinical scenario associated with a mission."""

    __tablename__ = "scenarios"

    id = db.Column(db.Integer, primary_key=True)
    mission_id = db.Column(
        db.Integer,
        db.ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(128), nullable=False)
    patient_name = db.Column(db.String(128), nullable=False)
    patient_age = db.Column(db.Integer, nullable=False)
    patient_gender = db.Column(db.String(32), nullable=True)
    clinical_summary = db.Column(db.Text, nullable=False)
    # Baseline patient vitals and state stored as JSON
    initial_state_json = db.Column(db.JSON, nullable=False)
    difficulty = db.Column(db.String(32), default="intermediate", nullable=False)
    # Review & approval metadata
    approval_status = db.Column(db.String(32), default="draft", nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
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
    mission = relationship("Mission", backref=db.backref("scenarios", cascade="all, delete-orphan", lazy="dynamic"))
    activities = relationship(
        "Activity",
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by="Activity.display_order.asc()",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Scenario id={self.id} mission={self.mission_id} patient={self.patient_name}>"
