from sqlalchemy import Boolean, Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    nickname = Column(String(50), nullable=False)
    role = Column(String(10), nullable=False, default="user")
    token_version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    original_username = Column(String(50), nullable=True)
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    disabled_reason = Column(String(200), nullable=True)
    force_password_change = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Bidirectional relationships
    answer_records = relationship("AnswerRecord", back_populates="user")
    level_progresses = relationship("LevelProgress", back_populates="user")
    stats = relationship("UserStats", back_populates="user", uselist=False)
    achievements = relationship("UserAchievement", back_populates="user")
    pvp_memberships = relationship("PvpRoomMember", back_populates="user")
    created_rooms = relationship(
        "PvpRoom", back_populates="creator", foreign_keys="PvpRoom.created_by"
    )
    broadcasts = relationship(
        "PvpBroadcast", back_populates="author", foreign_keys="PvpBroadcast.created_by"
    )
    play_sessions = relationship("PlaySession", back_populates="user")
    review_decisions = relationship(
        "ScoreReviewDecision",
        back_populates="user",
        foreign_keys="ScoreReviewDecision.user_id",
    )
