from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.record import PlaySession, SessionQuestion
from backend.app.models.pvp import PvpRoom, PvpRoomMember
from backend.app.models.user import User
from backend.app.routers.pvp import finalize_pvp_session
from backend.app.schemas.pvp import PvpBattleFinalizeIn
from backend.app.services.pvp_service import finalize_room_if_needed, serialize_room, sync_room_runtime_state


def test_auto_start_freezes_battle_times_and_does_not_finalize_before_deadline(db_session: Session):
    now = datetime.now(timezone.utc)
    room = PvpRoom(
        title="Auto Start Room",
        group_size=2,
        status="countdown",
        question_count=2,
        battle_time_limit_seconds=120,
        countdown_started_at=now - timedelta(seconds=10),
        auto_start_at=now - timedelta(seconds=1),
    )
    db_session.add(room)
    db_session.flush()
    db_session.add_all([
        PvpRoomMember(room_id=room.id, user_id=1, seat_order=1, is_ready=True),
        PvpRoomMember(room_id=room.id, user_id=2, seat_order=2, is_ready=True),
    ])
    db_session.flush()

    assert sync_room_runtime_state(db_session, room) is True

    assert room.status == "running"
    assert room.battle_started_at is not None
    assert room.battle_expires_at is not None
    assert room.battle_answer_accept_until is not None
    assert room.battle_expires_at > room.battle_started_at
    assert room.battle_answer_accept_until > room.battle_expires_at
    assert finalize_room_if_needed(db_session, room) is False
    assert room.status == "running"


def test_pvp_room_serialization_marks_naive_sqlite_timestamps_as_utc(db_session: Session):
    naive_now = datetime(2026, 5, 28, 10, 0, 0)
    user = User(username="pvp_time_user", password_hash="x", nickname="PVP Time")
    room = PvpRoom(
        title="Timezone Room",
        group_size=2,
        status="running",
        question_count=2,
        battle_time_limit_seconds=300,
        created_at=naive_now,
        started_at=naive_now,
        battle_started_at=naive_now,
        battle_expires_at=naive_now + timedelta(seconds=300),
    )
    db_session.add_all([user, room])
    db_session.flush()
    db_session.add(PvpRoomMember(room_id=room.id, user_id=user.id, seat_order=1))
    db_session.flush()

    payload = serialize_room(room)

    assert payload["battle_started_at"].endswith("+00:00")
    assert payload["battle_expires_at"].endswith("+00:00")


def test_finalize_session_rejects_early_unanswered_client_timeout(db_session: Session):
    now = datetime.now(timezone.utc)
    user = User(username="pvp_guard_user", password_hash="x", nickname="PVP Guard")
    room = PvpRoom(
        title="Guard Room",
        group_size=2,
        status="running",
        question_count=2,
        battle_time_limit_seconds=300,
        battle_started_at=now,
        battle_expires_at=now + timedelta(seconds=300),
        battle_answer_accept_until=now + timedelta(seconds=315),
    )
    db_session.add_all([user, room])
    db_session.flush()
    member = PvpRoomMember(room_id=room.id, user_id=user.id, seat_order=1)
    session = PlaySession(
        play_session_id="early-finalize-session",
        user_id=user.id,
        mode="pvp",
        pvp_room_id=room.id,
        status="active",
        started_at=now,
        expires_at=now + timedelta(seconds=360),
    )
    db_session.add_all([member, session])
    db_session.flush()
    db_session.add_all([
        SessionQuestion(
            play_session_id=session.play_session_id,
            question_id=1,
            question_order=0,
        ),
        SessionQuestion(
            play_session_id=session.play_session_id,
            question_id=2,
            question_order=1,
        ),
    ])
    db_session.flush()

    with pytest.raises(HTTPException) as exc:
        finalize_pvp_session(
            PvpBattleFinalizeIn(play_session_id=session.play_session_id),
            db=db_session,
            user=user,
        )

    assert exc.value.status_code == 409
    assert member.live_answered_count == 0
    assert session.status == "active"
    assert db_session.query(SessionQuestion).filter_by(play_session_id=session.play_session_id).first().answered_at is None


def test_finalize_session_allows_settlement_once_battle_expires_at(db_session: Session):
    now = datetime.now(timezone.utc)
    user = User(username="pvp_expired_user", password_hash="x", nickname="PVP Expired")
    room = PvpRoom(
        title="Expired Room",
        group_size=2,
        status="running",
        question_count=2,
        battle_time_limit_seconds=300,
        battle_started_at=now - timedelta(seconds=301),
        battle_expires_at=now - timedelta(seconds=1),
        battle_answer_accept_until=now + timedelta(seconds=14),
    )
    db_session.add_all([user, room])
    db_session.flush()
    member = PvpRoomMember(room_id=room.id, user_id=user.id, seat_order=1)
    session = PlaySession(
        play_session_id="expired-finalize-session",
        user_id=user.id,
        mode="pvp",
        pvp_room_id=room.id,
        status="active",
        started_at=now - timedelta(seconds=301),
        expires_at=now + timedelta(seconds=60),
    )
    db_session.add_all([member, session])
    db_session.flush()
    db_session.add_all([
        SessionQuestion(
            play_session_id=session.play_session_id,
            question_id=1,
            question_order=0,
        ),
        SessionQuestion(
            play_session_id=session.play_session_id,
            question_id=2,
            question_order=1,
        ),
    ])
    db_session.flush()

    response = finalize_pvp_session(
        PvpBattleFinalizeIn(play_session_id=session.play_session_id),
        db=db_session,
        user=user,
    )

    assert response.status == "finished"
    assert member.live_answered_count == 2
    assert member.live_wrong_count == 2
    assert session.status == "completed"
