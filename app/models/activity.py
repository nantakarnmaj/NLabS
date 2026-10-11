"""Activity, ActivityOption, ProcedureStep, and Feedback models."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from app.extensions import db


class Activity(db.Model):
    """Learning activity within a clinical scenario."""

    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(
        db.Integer,
        db.ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_type = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    instruction = db.Column(db.Text, nullable=False)
    # Generic content configuration (prompt details, evaluation parameters, etc.)
    content_json = db.Column(db.JSON, default=dict, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_required = db.Column(db.Boolean, default=True, nullable=False)
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
    scenario = relationship("Scenario", back_populates="activities")
    options = relationship(
        "ActivityOption",
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="ActivityOption.display_order.asc()",
        lazy="selectin",
    )
    procedure_steps = relationship(
        "ProcedureStep",
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="ProcedureStep.correct_order.asc()",
        lazy="selectin",
    )
    feedback_rules = relationship(
        "Feedback",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def initial_procedure_steps(self) -> list[ProcedureStep]:
        """Return procedure steps scrambled for sequence activities, guaranteed not in solved order."""
        import random

        steps = list(self.procedure_steps)
        if len(steps) <= 1:
            return steps

        seed_val = (self.id or 42) * 101 + 13
        rng = random.Random(seed_val)
        scrambled = list(steps)
        for _ in range(20):
            rng.shuffle(scrambled)
            if [s.step_key for s in scrambled] != [s.step_key for s in steps]:
                break
        return scrambled

    def __repr__(self) -> str:
        return f"<Activity id={self.id} type={self.activity_type} title={self.title}>"


class ActivityOption(db.Model):
    """Selectable options for cues, equipment, and decision activities."""

    __tablename__ = "activity_options"

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(
        db.Integer,
        db.ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_key = db.Column(db.String(64), nullable=False)
    label = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(256), nullable=True)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    metadata_json = db.Column(db.JSON, default=dict, nullable=False)

    activity = relationship("Activity", back_populates="options")

    __table_args__ = (
        UniqueConstraint("activity_id", "option_key", name="uq_activity_option_key"),
    )

    def __repr__(self) -> str:
        return f"<ActivityOption id={self.id} key={self.option_key} correct={self.is_correct}>"


class ProcedureStep(db.Model):
    """Step in a procedural sequencing activity."""

    __tablename__ = "procedure_steps"

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(
        db.Integer,
        db.ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_key = db.Column(db.String(64), nullable=False)
    step_text = db.Column(db.Text, nullable=False)
    correct_order = db.Column(db.Integer, nullable=False)
    rationale = db.Column(db.Text, nullable=True)
    critical_step = db.Column(db.Boolean, default=False, nullable=False)
    image_path = db.Column(db.String(256), nullable=True)

    activity = relationship("Activity", back_populates="procedure_steps")

    __table_args__ = (
        UniqueConstraint("activity_id", "step_key", name="uq_activity_step_key"),
    )

    def __repr__(self) -> str:
        return f"<ProcedureStep id={self.id} key={self.step_key} order={self.correct_order}>"


class Feedback(db.Model):
    """Targeted feedback triggered by learner decisions or sequences."""

    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(
        db.Integer,
        db.ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # trigger_type: 'on_success', 'on_mistake', 'on_selection', 'on_step_inverted'
    trigger_type = db.Column(db.String(64), nullable=False)
    trigger_key = db.Column(db.String(64), nullable=True)
    # feedback_type: 'positive', 'guidance', 'caution', 'critical'
    feedback_type = db.Column(db.String(32), default="guidance", nullable=False)
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    clinical_rationale = db.Column(db.Text, nullable=True)
    hint = db.Column(db.Text, nullable=True)
    # Simulated patient effects triggered by this feedback event (e.g. {"spo2_delta": -4})
    patient_effect_json = db.Column(db.JSON, default=dict, nullable=True)

    activity = relationship("Activity", back_populates="feedback_rules")

    def __repr__(self) -> str:
        return f"<Feedback id={self.id} type={self.feedback_type} title={self.title}>"
