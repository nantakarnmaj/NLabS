"""Mission and MissionPrerequisite models."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.extensions import db


class Mission(db.Model):
    """Clinical mission entity representing a simulated ward room."""

    __tablename__ = "missions"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, index=True, nullable=False)
    room_number = db.Column(db.String(16), unique=True, index=True, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    subtitle = db.Column(db.String(256), nullable=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(64), nullable=True)
    # Availability can be 'preview', 'coming_soon', or 'playable'
    availability = db.Column(db.String(32), default="coming_soon", nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
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
    prerequisites = relationship(
        "MissionPrerequisite",
        foreign_keys="MissionPrerequisite.mission_id",
        back_populates="mission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    required_by = relationship(
        "MissionPrerequisite",
        foreign_keys="MissionPrerequisite.prerequisite_mission_id",
        back_populates="prerequisite_mission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    progress_records = relationship(
        "MissionProgress",
        back_populates="mission",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Mission {self.room_number}: {self.slug} ({self.availability})>"


class MissionPrerequisite(db.Model):
    """Prerequisite relationship between missions."""

    __tablename__ = "mission_prerequisites"

    id = db.Column(db.Integer, primary_key=True)
    mission_id = db.Column(
        db.Integer,
        db.ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prerequisite_mission_id = db.Column(
        db.Integer,
        db.ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mission = relationship("Mission", foreign_keys=[mission_id], back_populates="prerequisites")
    prerequisite_mission = relationship("Mission", foreign_keys=[prerequisite_mission_id], back_populates="required_by")

    __table_args__ = (
        UniqueConstraint("mission_id", "prerequisite_mission_id", name="uq_mission_prerequisite"),
        CheckConstraint("mission_id != prerequisite_mission_id", name="ck_mission_no_self_prerequisite"),
    )

    def __repr__(self) -> str:
        return f"<MissionPrerequisite mission={self.mission_id} requires={self.prerequisite_mission_id}>"
