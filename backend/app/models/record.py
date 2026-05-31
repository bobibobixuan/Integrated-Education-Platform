from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class AnswerRecord(Base):
    __tablename__ = "answer_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    user_answer = Column(String(500), nullable=False, default="")
    is_correct = Column(Boolean, nullable=False, index=True)
    time_spent = Column(Float, nullable=False, default=0.0)
    mode = Column(String(20), nullable=False, default="adventure")
    play_session_id = Column(String(36), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    question_version = Column(Integer, nullable=False, default=1)
    correct_answer_snapshot = Column(String(500), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        UniqueConstraint("play_session_id", "question_id", name="uq_session_question"),
    )

    user = relationship("User", back_populates="answer_records")
    question = relationship("Question", back_populates="answer_records")


class LevelProgress(Base):
    __tablename__ = "level_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)
    stars = Column(Integer, nullable=False, default=0)
    unlocked = Column(Boolean, nullable=False, default=True)
    best_combo = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "level_id", name="uq_user_level"),
    )

    user = relationship("User", back_populates="level_progresses")
    level = relationship("Level", back_populates="progresses")


class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    total_questions = Column(Integer, nullable=False, default=0)
    total_correct = Column(Integer, nullable=False, default=0)
    total_score = Column(Integer, nullable=False, default=0)
    power_score = Column(Integer, nullable=False, default=0)
    max_combo = Column(Integer, nullable=False, default=0)
    practice_count = Column(Integer, nullable=False, default=0)
    extreme_passes = Column(Integer, nullable=False, default=0)
    extreme_dual_passes = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="stats", uselist=False)


class SessionQuestion(Base):
    __tablename__ = "session_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    play_session_id = Column(String(36), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    question_order = Column(Integer, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    answered_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "play_session_id", "question_id", name="uq_sq_session_question"
        ),
        UniqueConstraint(
            "play_session_id", "question_order", name="uq_sq_session_order"
        ),
    )

    question = relationship("Question", back_populates="session_questions")


class PlaySession(Base):
    __tablename__ = "play_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    play_session_id = Column(String(36), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=True)
    mode = Column(String(20), nullable=False, default="adventure")
    pvp_room_id = Column(Integer, ForeignKey("pvp_rooms.id"), nullable=True, index=True)
    best_combo = Column(Integer, nullable=False, default=0)
    is_suspicious = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="active")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Partial unique index uq_active_session is created via raw SQL in migrations

    user = relationship("User", back_populates="play_sessions")
    level = relationship("Level", back_populates="play_sessions")
    room = relationship(
        "PvpRoom", back_populates="play_sessions", foreign_keys=[pvp_room_id]
    )


class ScoreReviewDecision(Base):
    __tablename__ = "score_review_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)
    play_session_id = Column(String(36), nullable=False, index=True)
    scope = Column(String(10), nullable=False, default="session")
    decision = Column(String(10), nullable=False, default="pending")
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(String(200), nullable=True)

    user = relationship(
        "User", back_populates="review_decisions", foreign_keys=[user_id]
    )
    level = relationship(
        "Level", back_populates="review_decisions", foreign_keys=[level_id]
    )
    decider = relationship(
        "User", foreign_keys=[decided_by]
    )
