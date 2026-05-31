import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.deps import get_db, get_current_user, get_admin_user
from backend.app.models.user import User
from backend.app.models.unit import Unit, Level
from backend.app.models.question import Question
from backend.app.models.pvp import PvpRoom, PvpRoomMember, PvpBroadcast
from backend.app.models.record import AnswerRecord, PlaySession, SessionQuestion
from backend.app.services.pvp_service import (
    update_member_battle_state,
    schedule_room_auto_start,
    schedule_pvp_room_change,
    schedule_pvp_battle_snapshot_refresh_for_users,
    ensure_pvp_battle_session,
    load_current_session_question,
    get_session_question_count,
    serialize_member,
    rank_members,
    get_online_student_ids,
    add_student_to_room,
    build_pvp_battle_session_payload,
    finalize_room_if_needed,
    is_room_battle_time_expired,
    serialize_room as serialize_runtime_room,
    freeze_battle_times,
    reset_room_battle_state,
)
from backend.app.services.question_service import is_submitted_answer_correct
from backend.app.schemas.pvp import (
    PvpRoomMutationIn,
    StudentPvpRoomCreateIn,
    PvpReadyUpdateIn,
    PvpBattleAnswerIn,
    PvpBattleAnswerOut,
    PvpBattleQuestionOut,
    PvpBattleSessionOut,
    PvpBattleFinalizeIn,
    PvpRoomLogOut,
    PvpRoomOut,
    StudentPvpRoomOut,
)
from backend.app.routers import admin_router, pvp_router
from backend.app.utils import utcnow, as_utc


ROOM_ACTIVE_STATUSES = {"waiting", "countdown", "running"}


def _load_room_with_members(db: Session, room_id: int) -> PvpRoom | None:
    return db.query(PvpRoom).filter(PvpRoom.id == room_id).first()


def _ensure_room_exists(db: Session, room_id: int) -> PvpRoom:
    room = _load_room_with_members(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="竞技房间不存在")
    return room


def _serialize_room(room: PvpRoom, db: Session, include_logs: bool = True) -> dict:
    return serialize_runtime_room(room, include_logs=include_logs, db=db)


def _build_room_response(room: PvpRoom, db: Session, include_logs: bool = True) -> PvpRoomOut:
    payload = _serialize_room(room, db, include_logs=include_logs)
    return PvpRoomOut.model_validate(payload)


def _append_room_log(db: Session, room_id: int, message: str, user_id: int | None = None, category: str = "system") -> None:
    broadcast = PvpBroadcast(
        room_id=room_id,
        message=message,
        category=category,
        created_by=user_id,
    )
    db.add(broadcast)


def _find_active_membership_for_user(db: Session, user_id: int) -> PvpRoomMember | None:
    return (
        db.query(PvpRoomMember)
        .join(PvpRoom, PvpRoom.id == PvpRoomMember.room_id)
        .filter(
            PvpRoomMember.user_id == user_id,
            PvpRoom.status.in_(ROOM_ACTIVE_STATUSES),
        )
        .first()
    )


def _ensure_students_not_busy(db: Session, member_ids: list[int], current_room_id: int | None = None) -> None:
    busy_members = (
        db.query(PvpRoomMember)
        .join(PvpRoom, PvpRoom.id == PvpRoomMember.room_id)
        .filter(
            PvpRoomMember.user_id.in_(member_ids),
            PvpRoom.status.in_(list(ROOM_ACTIVE_STATUSES)),
        )
        .all()
    )
    conflicts = [
        member.user_id
        for member in busy_members
        if current_room_id is None or member.room_id != current_room_id
    ]
    if conflicts:
        users = db.query(User).filter(User.id.in_(conflicts)).all()
        names = "、".join(user.nickname for user in users[:5])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"以下学生已在其他对战房间中：{names}",
        )


# ── Admin Endpoints (on admin_router) ──

@admin_router.get("/pvp/rooms", response_model=list[PvpRoomOut])
def admin_list_pvp_rooms(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    rooms = db.query(PvpRoom).order_by(PvpRoom.created_at.desc(), PvpRoom.id.desc()).all()
    return [_build_room_response(room, db) for room in rooms]


@admin_router.post("/pvp/rooms", response_model=PvpRoomOut)
def admin_create_pvp_room(
    body: PvpRoomMutationIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="房间名称不能为空")
    if body.group_size < 2 or body.group_size > 12:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="房间人数必须在 2 到 12 之间")

    member_ids = list(body.member_user_ids)
    if len(member_ids) != len(set(member_ids)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="同一个学生不能重复加入同一房间")
    if len(member_ids) > body.group_size:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="所选学生数量不能超过房间人数上限")

    unit_ids = sorted(set(body.question_unit_ids))
    if not unit_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="至少选择 1 个出题单元")
    if body.question_count < 2 or body.question_count > 50:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="题量必须在 2 到 50 之间")

    battle_time_limit = body.battle_time_limit_seconds
    if battle_time_limit < 0 or battle_time_limit > 3600:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="对战时间限制必须在 0 到 3600 秒之间")

    if member_ids:
        users = db.query(User).filter(User.id.in_(member_ids), User.role == "user", User.is_active == True).all()
        if len(users) != len(member_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="存在无效的学生账号")
        _ensure_students_not_busy(db, member_ids)

    room = PvpRoom(
        title=title,
        description=body.description or "",
        group_size=body.group_size,
        status="waiting",
        mode="ffa",
        ranking_metric="battle_power",
        question_unit_ids=json.dumps(unit_ids, ensure_ascii=False),
        question_count=body.question_count,
        battle_time_limit_seconds=battle_time_limit,
        created_by=admin.id,
    )
    db.add(room)
    db.flush()

    for seat_order, user_id in enumerate(member_ids, start=1):
        db.add(PvpRoomMember(
            room_id=room.id,
            user_id=user_id,
            seat_order=seat_order,
            team="solo",
            is_ready=0,
        ))
    db.flush()

    _append_room_log(db, room.id, f"教师创建了房间「{title}」，已邀请 {len(member_ids)} 名学生加入。", admin.id)
    db.commit()
    return _build_room_response(_ensure_room_exists(db, room.id), db)


@admin_router.put("/pvp/rooms/{room_id}", response_model=PvpRoomOut)
def admin_update_pvp_room(
    room_id: int,
    body: PvpRoomMutationIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    room = _ensure_room_exists(db, room_id)

    member_ids = list(body.member_user_ids)
    if member_ids:
        _ensure_students_not_busy(db, member_ids, current_room_id=room_id)

    room.title = body.title.strip()
    room.description = body.description or ""
    room.group_size = body.group_size
    room.question_unit_ids = json.dumps(sorted(set(body.question_unit_ids)), ensure_ascii=False)
    room.question_count = body.question_count
    room.battle_time_limit_seconds = body.battle_time_limit_seconds

    if room.status == "finished":
        room.status = "waiting"
        room.started_at = None
        room.finished_at = None
        room.battle_started_at = None
        room.battle_expires_at = None
        room.battle_answer_accept_until = None

    # Replace members
    db.query(PvpRoomMember).filter(PvpRoomMember.room_id == room.id).delete()
    for seat_order, user_id in enumerate(member_ids, start=1):
        db.add(PvpRoomMember(
            room_id=room.id,
            user_id=user_id,
            seat_order=seat_order,
            team="solo",
            is_ready=0,
        ))
    db.flush()

    _append_room_log(db, room.id, f"教师更新了房间名单，当前参战人数 {len(member_ids)} 人。", admin.id)
    db.commit()
    return _build_room_response(_ensure_room_exists(db, room_id), db)


@admin_router.post("/pvp/rooms/{room_id}/start", response_model=PvpRoomOut)
def admin_start_pvp_room(
    room_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    room = _ensure_room_exists(db, room_id)
    if room.status in ("running", "countdown"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="房间已开始或正在倒计时")

    if len(room.members) < 2:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="至少 2 人才能开始对战")

    now = utcnow()
    room.status = "running"
    room.countdown_started_at = None
    room.auto_start_at = None
    room.started_at = now
    room.finished_at = None
    reset_room_battle_state(room)
    freeze_battle_times(room)

    _append_room_log(db, room.id, f"教师开启了房间「{room.title}」的混战模式。", admin.id, category="battle")
    db.commit()
    schedule_pvp_room_change({member.user_id for member in room.members})
    return _build_room_response(_ensure_room_exists(db, room_id), db)


@admin_router.post("/pvp/rooms/{room_id}/finish", response_model=PvpRoomOut)
def admin_finish_pvp_room(
    room_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    room = _ensure_room_exists(db, room_id)
    if room.status != "running":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="只有进行中的房间才能结束")

    room.status = "finished"
    room.finished_at = utcnow()

    members_ranked = rank_members(
        [serialize_member(m, get_online_student_ids()) for m in room.members],
        ranking_metric=room.ranking_metric or "battle_power",
    )
    podium = "，".join(
        f"第 {m['rank']} 名 {m['nickname']}（{m['battle_power']}）"
        for m in members_ranked[:3]
    ) or "暂无排名"
    _append_room_log(db, room.id, f"教师结束了本场对战。最终排名：{podium}。", admin.id, category="result")
    db.commit()
    schedule_pvp_room_change({member.user_id for member in room.members})
    return _build_room_response(_ensure_room_exists(db, room_id), db)


@admin_router.get("/pvp/logs", response_model=list[PvpRoomLogOut])
def admin_list_pvp_logs(
    room_id: int = Query(..., ge=1),
    limit: int = Query(40, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    _ensure_room_exists(db, room_id)
    broadcasts = (
        db.query(PvpBroadcast)
        .filter(PvpBroadcast.room_id == room_id)
        .order_by(PvpBroadcast.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        PvpRoomLogOut(
            id=b.id,
            room_id=b.room_id,
            message=b.message,
            category=b.category,
            created_at=b.created_at.isoformat() if b.created_at else None,
        )
        for b in reversed(broadcasts)
    ]


# ── Student Endpoints (on pvp_router) ──

@pvp_router.get("/my-room", response_model=StudentPvpRoomOut)
def get_my_pvp_room(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    membership = _find_active_membership_for_user(db, user.id)
    if not membership or not membership.room:
        return StudentPvpRoomOut(room=None)
    return StudentPvpRoomOut(room=_build_room_response(membership.room, db))


@pvp_router.get("/rooms", response_model=list[PvpRoomOut])
def list_student_pvp_rooms(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rooms = (
        db.query(PvpRoom)
        .order_by(PvpRoom.created_at.desc(), PvpRoom.id.desc())
        .limit(12)
        .all()
    )
    return [_build_room_response(room, db, include_logs=False) for room in rooms]


@pvp_router.post("/rooms", response_model=PvpRoomOut)
def student_create_pvp_room(
    body: StudentPvpRoomCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="房间名称不能为空")

    # Check student not already in an active room
    existing = _find_active_membership_for_user(db, user.id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你已在另一个对战房间中，请先退出")

    unit_ids = sorted(set(body.question_unit_ids))
    battle_time_limit = body.battle_time_limit_seconds
    if battle_time_limit < 0 or battle_time_limit > 3600:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="对战时间限制必须在 0 到 3600 秒之间")

    room = PvpRoom(
        title=title,
        description=body.description or "",
        group_size=body.group_size,
        status="waiting",
        mode="ffa",
        ranking_metric="battle_power",
        question_unit_ids=json.dumps(unit_ids, ensure_ascii=False),
        question_count=body.question_count,
        battle_time_limit_seconds=battle_time_limit,
        created_by=user.id,
    )
    db.add(room)
    db.flush()

    db.add(PvpRoomMember(
        room_id=room.id,
        user_id=user.id,
        seat_order=1,
        team="solo",
        is_ready=0,
    ))
    _append_room_log(db, room.id, f"{user.nickname} 创建了竞技房间「{room.title}」。", user.id, category="room")
    db.commit()
    return _build_room_response(_ensure_room_exists(db, room.id), db)


@pvp_router.post("/rooms/{room_id}/join", response_model=StudentPvpRoomOut)
def student_join_pvp_room(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = _ensure_room_exists(db, room_id)
    try:
        add_student_to_room(db, room, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    _append_room_log(db, room.id, f"{user.nickname} 加入了竞技房间。", user.id, category="room")
    db.commit()
    return StudentPvpRoomOut(room=_build_room_response(_ensure_room_exists(db, room_id), db))


@pvp_router.put("/my-room/ready", response_model=StudentPvpRoomOut)
def update_my_pvp_ready(
    body: PvpReadyUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    membership = _find_active_membership_for_user(db, user.id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="你当前没有被分配到竞技房间")

    room = membership.room
    if room.status == "running":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="房间已开始，不能再修改准备状态")
    if room.status == "finished":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="房间已结束，不能再修改准备状态")

    membership.is_ready = 1 if body.is_ready else 0
    _append_room_log(
        db, room.id,
        f"{user.nickname} 已{'准备完成' if body.is_ready else '取消准备'}。",
        user.id, category="ready",
    )

    # Check if all members ready
    all_ready = all(m.is_ready for m in room.members) if room.members else False
    if all_ready:
        room.status = "countdown"
        now = utcnow()
        room.countdown_started_at = now
        room.auto_start_at = now + timedelta(seconds=5)
        schedule_room_auto_start(room.id, room.auto_start_at)
        _append_room_log(db, room.id, f"全员已准备，房间「{room.title}」将在 5 秒后自动开始。", user.id, category="countdown")
    elif room.status == "countdown":
        room.status = "waiting"
        room.countdown_started_at = None
        room.auto_start_at = None
        _append_room_log(db, room.id, f"倒计时已取消，房间「{room.title}」返回等待中。", user.id, category="countdown")

    db.commit()
    schedule_pvp_room_change({member.user_id for member in room.members})
    membership = _find_active_membership_for_user(db, user.id)
    if not membership:
        return StudentPvpRoomOut(room=None)
    return StudentPvpRoomOut(room=_build_room_response(membership.room, db))


@pvp_router.post("/my-room/leave", response_model=StudentPvpRoomOut)
def leave_my_pvp_room(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    membership = _find_active_membership_for_user(db, user.id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="你当前没有被分配到竞技房间")

    room = membership.room
    if room.status in {"countdown", "running"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="对战已进入倒计时或进行中，不能退出房间")

    _append_room_log(db, room.id, f"{user.nickname} 退出了竞技房间。", user.id)
    db.delete(membership)
    db.flush()

    # Check if countdown should cancel
    if room.status == "countdown":
        all_ready = all(m.is_ready for m in room.members) if room.members else False
        if not all_ready:
            room.status = "waiting"
            room.countdown_started_at = None
            room.auto_start_at = None
            _append_room_log(db, room.id, f"倒计时已取消，房间「{room.title}」返回等待中。", user.id, category="countdown")

    affected_user_ids = {member.user_id for member in room.members}
    db.commit()
    schedule_pvp_room_change(affected_user_ids)
    return StudentPvpRoomOut(room=None)


@pvp_router.get("/my-battle", response_model=PvpBattleSessionOut)
def get_my_pvp_battle(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    membership = _find_active_membership_for_user(db, user.id)
    if not membership:
        latest_member = (
            db.query(PvpRoomMember)
            .join(PvpRoom, PvpRoom.id == PvpRoomMember.room_id)
            .filter(
                PvpRoomMember.user_id == user.id,
                PvpRoom.status == "finished",
            )
            .order_by(PvpRoom.created_at.desc(), PvpRoom.id.desc())
            .first()
        )
        if not latest_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="你当前没有活跃的对战房间")

        room = latest_member.room
        session = (
            db.query(PlaySession)
            .filter(
                PlaySession.user_id == user.id,
                PlaySession.mode == "pvp",
                PlaySession.pvp_room_id == room.id,
            )
            .order_by(PlaySession.started_at.desc(), PlaySession.id.desc())
            .first()
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="你当前没有活跃的对战会话")

        return PvpBattleSessionOut(
            room=_serialize_room(room, db, include_logs=False),
            play_session_id=session.play_session_id,
            session_status=session.status,
            question_count=get_session_question_count(db, session.play_session_id),
            current_question=None,
        )

    try:
        payload = build_pvp_battle_session_payload(db, user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return PvpBattleSessionOut.model_validate(payload)


def _load_pvp_finalize_context(db: Session, user_id: int, play_session_id: str) -> tuple[PvpRoom, PvpRoomMember, PlaySession]:
    session = (
        db.query(PlaySession)
        .filter(
            PlaySession.play_session_id == play_session_id,
            PlaySession.user_id == user_id,
            PlaySession.mode == "pvp",
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对战会话不存在")

    room = _ensure_room_exists(db, session.pvp_room_id)
    membership = next((m for m in room.members if m.user_id == user_id), None)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="你已不在该竞技房间中")

    if finalize_room_if_needed(db, room, actor_id=user_id):
        db.commit()
        room = _ensure_room_exists(db, room.id)
        membership = next((m for m in room.members if m.user_id == user_id), None)
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="你已不在该竞技房间中")

    expires_at = as_utc(session.expires_at)
    if expires_at and expires_at < utcnow() and session.status == "active":
        session.status = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="对战会话已过期")

    if session.status not in {"active", "completed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该对战会话已结束")

    return room, membership, session


def _load_pvp_session_context(db: Session, user_id: int, play_session_id: str) -> tuple[PvpRoom, PvpRoomMember, PlaySession]:
    session = (
        db.query(PlaySession)
        .filter(
            PlaySession.play_session_id == play_session_id,
            PlaySession.user_id == user_id,
            PlaySession.mode == "pvp",
        )
        .first()
    )

    # Fallback: if play_session_id doesn't match, find the active session for this user's current room
    if not session:
        membership = _find_active_membership_for_user(db, user_id)
        if membership and membership.room.status == "running":
            session = (
                db.query(PlaySession)
                .filter(
                    PlaySession.user_id == user_id,
                    PlaySession.mode == "pvp",
                    PlaySession.pvp_room_id == membership.room_id,
                    PlaySession.status == "active",
                )
                .order_by(PlaySession.started_at.desc())
                .first()
            )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对战会话不存在")

    room = _ensure_room_exists(db, session.pvp_room_id)
    membership = next((m for m in room.members if m.user_id == user_id), None)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="你已不在该竞技房间中")

    if finalize_room_if_needed(db, room, actor_id=user_id):
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="本场对战已结束")
    if room.status == "finished":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="本场对战已结束")
    if session.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该对战会话已结束")

    expires_at = as_utc(session.expires_at)
    if expires_at and expires_at < utcnow():
        session.status = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="对战会话已过期")

    return room, membership, session


@pvp_router.post("/answer", response_model=PvpBattleAnswerOut)
def submit_pvp_answer(
    body: PvpBattleAnswerIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room, membership, session = _load_pvp_session_context(db, user.id, body.play_session_id)

    # Check for existing answer (idempotent)
    existing = (
        db.query(AnswerRecord)
        .filter(
            AnswerRecord.play_session_id == session.play_session_id,
            AnswerRecord.question_id == body.question_id,
        )
        .first()
    )
    if existing:
        current_sq_unanswered = (
            db.query(SessionQuestion)
            .filter(
                SessionQuestion.play_session_id == session.play_session_id,
                SessionQuestion.answered_at == None,
            )
            .order_by(SessionQuestion.question_order)
            .first()
        )
        question_count = (
            db.query(SessionQuestion)
            .filter(SessionQuestion.play_session_id == session.play_session_id)
            .count()
        )
        next_question = None
        if current_sq_unanswered:
            q = db.query(Question).filter(Question.id == current_sq_unanswered.question_id).first()
            if q:
                next_question = PvpBattleQuestionOut(
                    id=q.id, level_id=q.level_id, type=q.type,
                    content=q.content, options=q.options,
                    question_order=current_sq_unanswered.question_order,
                    total_questions=question_count,
                )
        return PvpBattleAnswerOut(
            success=True,
            is_correct=existing.is_correct,
            correct_answer=existing.correct_answer_snapshot,
            battle_power_delta=0,
            current_battle_power=int(membership.live_battle_power or 0),
            session_status=session.status,
            question_count=question_count,
            knowledge=None,
            next_question=next_question,
        )

    # Get current question for this session
    current_sq = (
        db.query(SessionQuestion)
        .filter(
            SessionQuestion.play_session_id == session.play_session_id,
            SessionQuestion.answered_at == None,
        )
        .order_by(SessionQuestion.question_order)
        .first()
    )
    if not current_sq:
        session.status = "completed"
        if session.completed_at is None:
            session.completed_at = utcnow()
        finalize_room_if_needed(db, room, actor_id=user.id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该对战会话已结束")

    if current_sq.question_id != body.question_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请按当前竞技场题目顺序作答")

    now = utcnow()
    if current_sq.delivered_at is None:
        current_sq.delivered_at = now

    question = db.query(Question).filter(Question.id == body.question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

    # Verify room still running
    db.refresh(room)
    if room.status != "running":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="本场对战已结束")
    if is_room_battle_time_expired(room, now):
        finalize_room_if_needed(db, room, actor_id=user.id)
        db.commit()
        schedule_pvp_room_change({m.user_id for m in room.members})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="本场对战已结束")

    is_correct = is_submitted_answer_correct(question, body.submitted_answer)
    delivered_at = as_utc(current_sq.delivered_at)
    server_delta = (now - delivered_at).total_seconds() if delivered_at else body.client_time_spent
    effective_time = max(body.client_time_spent, server_delta)
    if effective_time < 2.0:
        effective_time = 2.0

    # Calculate battle power delta via shared service
    delta = update_member_battle_state(membership, is_correct, effective_time)

    record = AnswerRecord(
        user_id=user.id,
        question_id=body.question_id,
        user_answer=body.submitted_answer,
        is_correct=is_correct,
        time_spent=effective_time,
        mode="pvp",
        play_session_id=body.play_session_id,
        correct_answer_snapshot=question.answer,
    )
    db.add(record)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该题已作答，请刷新当前对战状态")

    current_sq.answered_at = now
    db.flush()

    _append_room_log(
        db, membership.room_id,
        f"{user.nickname} 回答{'正确' if is_correct else '错误'}，战力 {'+' + str(delta) if delta > 0 else str(delta)}，当前 {membership.live_battle_power}。",
        user.id, category="battle",
    )

    # Check if all questions answered
    unanswered_count = (
        db.query(SessionQuestion)
        .filter(
            SessionQuestion.play_session_id == session.play_session_id,
            SessionQuestion.answered_at == None,
        )
        .count()
    )
    if unanswered_count == 0:
        session.status = "completed"
        session.completed_at = now
        best_combo = 0
        current_combo = 0
        session_records = (
            db.query(AnswerRecord)
            .filter(AnswerRecord.play_session_id == session.play_session_id)
            .join(SessionQuestion, SessionQuestion.question_id == AnswerRecord.question_id)
            .filter(SessionQuestion.play_session_id == session.play_session_id)
            .order_by(SessionQuestion.question_order)
            .all()
        )
        for item in session_records:
            if item.is_correct:
                current_combo += 1
                best_combo = max(best_combo, current_combo)
            else:
                current_combo = 0
        session.best_combo = best_combo

    finalize_room_if_needed(db, room, actor_id=user.id)

    question_count = (
        db.query(SessionQuestion)
        .filter(SessionQuestion.play_session_id == session.play_session_id)
        .count()
    )

    next_question = None
    if session.status == "active":
        next_sq = (
            db.query(SessionQuestion)
            .filter(
                SessionQuestion.play_session_id == session.play_session_id,
                SessionQuestion.answered_at == None,
            )
            .order_by(SessionQuestion.question_order)
            .first()
        )
        if next_sq:
            nq = db.query(Question).filter(Question.id == next_sq.question_id).first()
            if nq:
                next_question = PvpBattleQuestionOut(
                    id=nq.id, level_id=nq.level_id, type=nq.type,
                    content=nq.content, options=nq.options,
                    question_order=next_sq.question_order,
                    total_questions=question_count,
                )

    db.commit()

    # Push updated ranking to all room members
    affected_user_ids = {m.user_id for m in room.members}
    schedule_pvp_room_change(affected_user_ids)
    schedule_pvp_battle_snapshot_refresh_for_users(affected_user_ids)

    return PvpBattleAnswerOut(
        success=True,
        is_correct=is_correct,
        correct_answer=question.answer,
        battle_power_delta=delta,
        current_battle_power=int(membership.live_battle_power or 0),
        session_status=session.status,
        question_count=question_count,
        knowledge={
            "meaning": question.knowledge_meaning or "",
            "rule": question.knowledge_rule or "",
            "error": question.knowledge_error or "",
            "example": question.knowledge_example or "",
        },
        next_question=next_question,
    )


@pvp_router.post("/finalize-session", response_model=PvpRoomOut)
def finalize_pvp_session(
    body: PvpBattleFinalizeIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room, membership, session = _load_pvp_finalize_context(db, user.id, body.play_session_id)

    if room.status == "finished":
        return _build_room_response(_ensure_room_exists(db, room.id), db)

    now = utcnow()
    unanswered = (
        db.query(SessionQuestion)
        .filter(
            SessionQuestion.play_session_id == session.play_session_id,
            SessionQuestion.answered_at == None,
        )
        .all()
    )
    unanswered_count = len(unanswered)
    if unanswered_count > 0 and not is_room_battle_time_expired(room, now):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="本场对战尚未到总时限，不能提前结算未完成题目",
        )

    for sq in unanswered:
        sq.answered_at = now

    if unanswered_count > 0:
        membership.live_wrong_count = int(membership.live_wrong_count or 0) + unanswered_count
        membership.live_answered_count = int(membership.live_answered_count or 0) + unanswered_count
        membership.current_streak = 0
        membership.live_battle_power = int(membership.live_battle_power or 0) - (30 * unanswered_count)
        membership.last_answer_at = now

    session.status = "completed"
    if session.completed_at is None:
        session.completed_at = now
    finalize_room_if_needed(db, room, actor_id=user.id)
    db.commit()
    schedule_pvp_room_change({m.user_id for m in room.members})

    return _build_room_response(_ensure_room_exists(db, room.id), db)
