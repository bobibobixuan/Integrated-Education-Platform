from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class PvpRoom(Base):
    __tablename__ = "pvp_rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False, default="")
    group_size = Column(Integer, nullable=False, default=4)
    status = Column(String(50), nullable=False, default="pending")
    mode = Column(String(30), nullable=False, default="ffa")
    ranking_metric = Column(String(30), nullable=False, default="battle_power")
    question_unit_ids = Column(String(500), nullable=False, default="[]")
    question_count = Column(Integer, nullable=False, default=10)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    countdown_started_at = Column(DateTime(timezone=True), nullable=True)
    auto_start_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    battle_time_limit_seconds = Column(Integer, nullable=False, default=0)
    battle_started_at = Column(DateTime(timezone=True), nullable=True)
    battle_expires_at = Column(DateTime(timezone=True), nullable=True)
    battle_answer_accept_until = Column(DateTime(timezone=True), nullable=True)

    creator = relationship(
        "User", back_populates="created_rooms", foreign_keys=[created_by]
    )
    members = relationship(
        "PvpRoomMember",
        back_populates="room",
        cascade="all, delete-orphan",
        order_by="PvpRoomMember.seat_order",
    )
    broadcasts = relationship(
        "PvpBroadcast",
        back_populates="room",
        cascade="all, delete-orphan",
        order_by="PvpBroadcast.created_at.desc()",
    )
    play_sessions = relationship("PlaySession", back_populates="room")


class PvpRoomMember(Base):
    __tablename__ = "pvp_room_members"
    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_pvp_room_member"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("pvp_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seat_order = Column(Integer, nullable=False, default=0)
    team = Column(String(20), nullable=False, default="left")
    is_ready = Column(Boolean, nullable=False, default=False)
    live_battle_power = Column(Integer, nullable=False, default=0)
    live_correct_count = Column(Integer, nullable=False, default=0)
    live_wrong_count = Column(Integer, nullable=False, default=0)
    live_answered_count = Column(Integer, nullable=False, default=0)
    current_streak = Column(Integer, nullable=False, default=0)
    best_streak = Column(Integer, nullable=False, default=0)
    last_answer_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("PvpRoom", back_populates="members")
    user = relationship("User", back_populates="pvp_memberships")


class PvpBroadcast(Base):
    __tablename__ = "pvp_broadcasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("pvp_rooms.id"), nullable=True)
    message = Column(String(1000), nullable=False)
    category = Column(String(50), nullable=False, default="system")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("PvpRoom", back_populates="broadcasts")
    author = relationship(
        "User", back_populates="broadcasts", foreign_keys=[created_by]
    )
