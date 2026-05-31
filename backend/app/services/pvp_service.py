import asyncio
import json
import random
import uuid
from datetime import timedelta
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.app.database import SessionLocal
from backend.app.models.pvp import PvpBroadcast, PvpRoom, PvpRoomMember
from backend.app.models.question import Question
from backend.app.models.record import PlaySession, SessionQuestion
from backend.app.models.unit import Level
from backend.app.services.question_service import get_effective_question_type
from backend.app.ws.manager import manager


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def calc_effective_time_limit(room: "PvpRoom") -> int:
    """返回有效时间限制（秒）。0 时自动按题量计算。"""
    if room.battle_time_limit_seconds and room.battle_time_limit_seconds > 0:
        return int(room.battle_time_limit_seconds)
    return int(room.question_count) * 30


def freeze_battle_times(room: "PvpRoom") -> None:
    """一次性冻结起止时间和宽限窗口。幂等：三字段全存在则跳过；部分存在则报错。"""
    fields = (room.battle_started_at, room.battle_expires_at, room.battle_answer_accept_until)
    if all(f is not None for f in fields):
        return
    if any(f is not None for f in fields):
        raise RuntimeError(
            f"房间 {room.id} 战斗时间字段半初始化: "
            f"started_at={room.battle_started_at!r} "
            f"expires_at={room.battle_expires_at!r} "
            f"accept_until={room.battle_answer_accept_until!r}"
        )
    now = utcnow()
    effective_limit = calc_effective_time_limit(room)
    room.battle_started_at = now
    room.battle_expires_at = now + timedelta(seconds=effective_limit)
    room.battle_answer_accept_until = room.battle_expires_at + timedelta(seconds=15)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _isoformat_utc(value: datetime | None) -> str | None:
    normalized = _as_utc(value)
    return normalized.isoformat() if normalized else None


def get_online_student_ids() -> set[int]:
    return set(manager.student_connections.keys())


def _normalize_question_options(raw_options):
    if not raw_options:
        return None
    return json.loads(raw_options) if isinstance(raw_options, str) else raw_options


def load_room_with_members(db: Session, room_id: int) -> PvpRoom | None:
    return (
        db.query(PvpRoom)
        .options(joinedload(PvpRoom.members).joinedload(PvpRoomMember.user))
        .filter(PvpRoom.id == room_id)
        .first()
    )


def parse_room_unit_ids(room: PvpRoom) -> list[int]:
    raw = room.question_unit_ids or "[]"
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("房间题库配置损坏：question_unit_ids 不是合法 JSON") from exc
    else:
        parsed = raw

    if not isinstance(parsed, list):
        raise ValueError("房间题库配置损坏：question_unit_ids 必须是数组")

    clean = set()
    for item in parsed:
        try:
            unit_id = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"房间题库配置损坏：存在无法解析的单元 ID {item!r}") from exc
        if unit_id <= 0:
            raise ValueError(f"房间题库配置损坏：单元 ID 必须大于 0，收到 {unit_id}")
        clean.add(unit_id)
    return sorted(clean)


def load_room_logs(db: Session, room_id: int, limit: int = 40) -> list[PvpBroadcast]:
    return (
        db.query(PvpBroadcast)
        .filter(PvpBroadcast.room_id == room_id)
        .order_by(PvpBroadcast.created_at.desc(), PvpBroadcast.id.desc())
        .limit(limit)
        .all()
    )


def append_room_log(
    db: Session,
    room_id: int,
    message: str,
    created_by: int | None = None,
    category: str = "system",
) -> PvpBroadcast:
    item = PvpBroadcast(
        room_id=room_id,
        message=message,
        created_by=created_by,
        category=category,
    )
    db.add(item)
    db.flush()
    return item


def reset_room_battle_state(room: PvpRoom) -> None:
    for member in room.members:
        member.live_battle_power = 0
        member.live_correct_count = 0
        member.live_wrong_count = 0
        member.live_answered_count = 0
        member.current_streak = 0
        member.best_streak = 0
        member.last_answer_at = None
    room.battle_started_at = None
    room.battle_expires_at = None
    room.battle_answer_accept_until = None


def all_members_ready(room: PvpRoom) -> bool:
    return bool(room.members) and all(bool(member.is_ready) for member in room.members)


def sync_room_runtime_state(db: Session, room: PvpRoom) -> bool:
    if room.status != "countdown" or room.auto_start_at is None:
        return False

    auto_start_at = _as_utc(room.auto_start_at)
    if auto_start_at > utcnow():
        return False

    room.status = "running"
    room.started_at = utcnow()
    room.finished_at = None
    room.countdown_started_at = None
    room.auto_start_at = None
    reset_room_battle_state(room)
    freeze_battle_times(room)
    append_room_log(db, room.id, f"房间「{room.title}」倒计时结束，混战已自动开始。", room.created_by, category="battle")
    return True


async def _auto_start_room_when_due(room_id: int, expected_auto_start_at: datetime) -> None:
    delay = max((_as_utc(expected_auto_start_at) - utcnow()).total_seconds(), 0)
    if delay > 0:
        await asyncio.sleep(delay)

    db = SessionLocal()
    try:
        room = load_room_with_members(db, room_id)
        if room is None:
            return

        current_auto_start_at = _as_utc(room.auto_start_at)
        if room.status != "countdown" or current_auto_start_at is None:
            return

        if abs((current_auto_start_at - _as_utc(expected_auto_start_at)).total_seconds()) > 0.5:
            return

        affected_user_ids = {member.user_id for member in room.members}
        if not sync_room_runtime_state(db, room):
            return

        db.commit()
    finally:
        db.close()

    schedule_pvp_room_change(affected_user_ids)


def schedule_room_auto_start(room_id: int, auto_start_at: datetime | None) -> None:
    expected_auto_start_at = _as_utc(auto_start_at)
    if expected_auto_start_at is None:
        return
    manager.schedule(_auto_start_room_when_due(room_id, expected_auto_start_at))


def get_room_question_pool(db: Session, room: PvpRoom) -> list[Question]:
    unit_ids = parse_room_unit_ids(room)
    if not unit_ids:
        unit_ids = [
            row[0]
            for row in db.query(Level.unit_id).filter(Level.is_active == True).distinct().all()
        ]
    level_ids = [
        row[0]
        for row in db.query(Level.id)
        .filter(Level.unit_id.in_(unit_ids), Level.is_active == True)
        .all()
    ]
    if not level_ids:
        return []
    return (
        db.query(Question)
        .filter(Question.level_id.in_(level_ids), Question.is_active == True)
        .all()
    )


def ensure_room_has_enough_questions(db: Session, room: PvpRoom) -> None:
    question_pool = get_room_question_pool(db, room)
    if len(question_pool) < int(room.question_count or 0):
        raise ValueError(f"题库不足，当前只找到 {len(question_pool)} 道题，少于房间要求的 {room.question_count} 道")


def _load_session_questions(db: Session, play_session_id: str) -> list[Question]:
    ordered_ids = [
        row.question_id
        for row in db.query(SessionQuestion)
        .filter(SessionQuestion.play_session_id == play_session_id)
        .order_by(SessionQuestion.question_order)
        .all()
    ]
    if not ordered_ids:
        return []

    question_map = {
        item.id: item
        for item in db.query(Question).filter(Question.id.in_(ordered_ids)).all()
    }
    return [question_map[qid] for qid in ordered_ids if qid in question_map]


def get_session_question_count(db: Session, play_session_id: str) -> int:
    return (
        db.query(SessionQuestion)
        .filter(SessionQuestion.play_session_id == play_session_id)
        .count()
    )


def load_current_session_question(db: Session, play_session_id: str) -> SessionQuestion | None:
    return (
        db.query(SessionQuestion)
        .filter(
            SessionQuestion.play_session_id == play_session_id,
            SessionQuestion.answered_at == None,
        )
        .order_by(SessionQuestion.question_order)
        .first()
    )


def build_pvp_question_payload(question: Question, question_order: int, total_questions: int) -> dict:
    return {
        "id": question.id,
        "level_id": question.level_id,
        "unit_id": question.level.unit_id if question.level else 0,
        "category": question.level.name if question.level else "",
        "category_id": question.level.sort_order if question.level else 0,
        "type": get_effective_question_type(question),
        "content": question.content,
        "options": _normalize_question_options(question.options),
        "question_order": int(question_order),
        "total_questions": int(total_questions),
    }


def build_pvp_answer_reveal_payload(question: Question) -> dict:
    return {
        "correct_answer": question.answer,
        "knowledge": {
            "meaning": question.knowledge_meaning,
            "rule": question.knowledge_rule,
            "error": question.knowledge_error,
            "example": question.knowledge_example,
        },
    }


def build_current_pvp_question_payload(
    db: Session,
    play_session_id: str,
    total_questions: int | None = None,
) -> dict | None:
    current_sq = load_current_session_question(db, play_session_id)
    if current_sq is None:
        return None

    if current_sq.delivered_at is None:
        current_sq.delivered_at = utcnow()
        db.flush()

    question = db.query(Question).filter(Question.id == current_sq.question_id).first()
    if question is None:
        raise LookupError("当前对战题目不存在")

    resolved_total = total_questions if total_questions is not None else get_session_question_count(db, play_session_id)
    return build_pvp_question_payload(question, current_sq.question_order, resolved_total)


def _is_session_from_current_battle(room: PvpRoom, session: PlaySession) -> bool:
    room_started_at = _as_utc(room.battle_started_at)
    session_started_at = _as_utc(session.started_at)
    if room_started_at is None or session_started_at is None:
        return session.status == "active"
    return abs((session_started_at - room_started_at).total_seconds()) <= 1


def _load_existing_pvp_session(db: Session, room: PvpRoom, user_id: int) -> tuple[PlaySession, list[Question]] | None:
    sessions = (
        db.query(PlaySession)
        .filter(
            PlaySession.user_id == user_id,
            PlaySession.pvp_room_id == room.id,
            PlaySession.mode == "pvp",
            PlaySession.status.in_(["active", "completed"]),
        )
        .order_by(PlaySession.started_at.desc(), PlaySession.id.desc())
        .all()
    )
    for session in sessions:
        if not _is_session_from_current_battle(room, session):
            continue
        questions = _load_session_questions(db, session.play_session_id)
        if not questions:
            continue
        return session, questions
    return None


def ensure_pvp_battle_session(db: Session, room: PvpRoom, user_id: int) -> tuple[PlaySession, list[Question]]:
    existing = _load_existing_pvp_session(db, room, user_id)
    if existing:
        return existing

    question_pool = get_room_question_pool(db, room)
    if len(question_pool) < int(room.question_count or 0):
        raise ValueError(f"题库不足，当前只找到 {len(question_pool)} 道题，少于房间要求的 {room.question_count} 道")

    randomizer = random.SystemRandom()
    selected_questions = randomizer.sample(question_pool, int(room.question_count))
    randomizer.shuffle(selected_questions)

    db.query(PlaySession).filter(
        PlaySession.user_id == user_id,
        PlaySession.mode == "pvp",
        PlaySession.status == "active",
    ).update({"status": "abandoned"}, synchronize_session=False)

    play_session_id = str(uuid.uuid4())
    session = PlaySession(
        play_session_id=play_session_id,
        user_id=user_id,
        level_id=None,  # PVP sessions span multiple levels
        mode="pvp",
        pvp_room_id=room.id,
        status="active",
        started_at=room.battle_started_at,
        expires_at=(room.battle_expires_at + timedelta(seconds=60))
            if room.battle_expires_at else utcnow() + timedelta(minutes=30),
    )
    db.add(session)
    try:
        db.flush()

        for index, question in enumerate(selected_questions):
            db.add(
                SessionQuestion(
                    play_session_id=play_session_id,
                    question_id=question.id,
                    question_order=index,
                )
            )
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = _load_existing_pvp_session(db, room, user_id)
        if existing:
            return existing
        raise

    return session, selected_questions


def calculate_answer_battle_delta(is_correct: bool, effective_time: float, current_streak: int) -> int:
    if is_correct:
        delta = 100
        if effective_time <= 5:
            delta += 10
        delta += min(max(current_streak - 1, 0), 5) * 10
        return delta
    return -45


def update_member_battle_state(member: PvpRoomMember, is_correct: bool, effective_time: float, delta_override: int | None = None) -> int:
    member.live_answered_count += 1
    if is_correct:
        member.live_correct_count += 1
        member.current_streak += 1
        member.best_streak = max(member.best_streak, member.current_streak)
    else:
        member.live_wrong_count += 1
        member.current_streak = 0

    delta = delta_override if delta_override is not None else calculate_answer_battle_delta(is_correct, effective_time, member.current_streak)
    member.live_battle_power += delta
    member.last_answer_at = utcnow()
    return delta


def serialize_member(member: PvpRoomMember, online_user_ids: set[int]) -> dict:
    answered = int(member.live_answered_count or 0)
    correct = int(member.live_correct_count or 0)
    wrong = int(member.live_wrong_count or 0)
    accuracy = round(correct * 100 / answered, 1) if answered > 0 else 0.0
    return {
        "user_id": member.user.id,
        "username": member.user.username,
        "nickname": member.user.nickname,
        "seat_order": member.seat_order,
        "is_ready": bool(member.is_ready),
        "battle_power": int(member.live_battle_power or 0),
        "correct_count": correct,
        "wrong_count": wrong,
        "answered_count": answered,
        "accuracy": accuracy,
        "best_streak": int(member.best_streak or 0),
        "last_answer_at": _isoformat_utc(member.last_answer_at),
        "is_online": member.user.id in online_user_ids,
    }


def rank_members(member_payloads: list[dict], ranking_metric: str = "battle_power") -> list[dict]:
    if ranking_metric == "correct_count":
        key = lambda item: (
            -int(item["correct_count"]),
            -int(item["battle_power"]),
            int(item["wrong_count"]),
            int(item["seat_order"]),
        )
    else:
        key = lambda item: (
            -int(item["battle_power"]),
            -int(item["correct_count"]),
            int(item["wrong_count"]),
            int(item["seat_order"]),
        )
    ranked = sorted(member_payloads, key=key)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
    return ranked


def is_room_battle_time_expired(room: PvpRoom, now: datetime | None = None) -> bool:
    if room.status != "running":
        return False
    current = now or utcnow()
    expires_at = _as_utc(room.battle_expires_at)
    return expires_at is not None and current >= expires_at


def _all_members_finished(room: PvpRoom) -> bool:
    target = int(room.question_count or 0)
    return bool(room.members) and all(int(member.live_answered_count or 0) >= target for member in room.members)


def _apply_timeout_penalties(room: PvpRoom, now: datetime) -> None:
    target = int(room.question_count or 0)
    for member in room.members:
        answered = int(member.live_answered_count or 0)
        missing = max(0, target - answered)
        if missing <= 0:
            continue
        member.live_wrong_count = int(member.live_wrong_count or 0) + missing
        member.live_answered_count = answered + missing
        member.current_streak = 0
        member.live_battle_power = int(member.live_battle_power or 0) - (30 * missing)
        member.last_answer_at = now


def _complete_room_sessions(db: Session, room: PvpRoom, now: datetime) -> None:
    sessions = (
        db.query(PlaySession)
        .filter(
            PlaySession.pvp_room_id == room.id,
            PlaySession.mode == "pvp",
            PlaySession.status == "active",
        )
        .all()
    )
    for session in sessions:
        unanswered = (
            db.query(SessionQuestion)
            .filter(
                SessionQuestion.play_session_id == session.play_session_id,
                SessionQuestion.answered_at == None,
            )
            .all()
        )
        for sq in unanswered:
            sq.answered_at = now
        session.status = "completed"
        if session.completed_at is None:
            session.completed_at = now


def finalize_room_if_needed(db: Session, room: PvpRoom, actor_id: int | None = None) -> bool:
    if room.status != "running":
        return False

    now = utcnow()
    timed_out = is_room_battle_time_expired(room, now)
    everyone_finished = _all_members_finished(room)
    if not timed_out and not everyone_finished:
        return False

    if timed_out:
        _apply_timeout_penalties(room, now)

    _complete_room_sessions(db, room, now)

    room.status = "finished"
    room.finished_at = now
    room.auto_start_at = None
    room.countdown_started_at = None

    members_ranked = rank_members(
        [serialize_member(member, get_online_student_ids()) for member in room.members],
        ranking_metric=room.ranking_metric or "battle_power",
    )
    podium = "，".join(
        f"第 {member['rank']} 名 {member['nickname']}（{member['battle_power']}）"
        for member in members_ranked[:3]
    ) or "暂无排名"
    reason = "总时长结束，系统已自动结算本场对战。" if timed_out else "全部成员已完成答题，本场对战已自动结束。"
    append_room_log(db, room.id, f"{reason} 最终排名：{podium}。", actor_id, category="result")
    return True


def serialize_room(room: PvpRoom, include_logs: bool = False, db: Session | None = None) -> dict:
    online_user_ids = get_online_student_ids()
    ranked_members = rank_members([serialize_member(member, online_user_ids) for member in room.members], ranking_metric=room.ranking_metric or "battle_power")
    payload = {
        "id": room.id,
        "title": room.title,
        "description": room.description,
        "group_size": room.group_size,
        "status": room.status,
        "mode": room.mode,
        "ranking_metric": room.ranking_metric,
        "question_unit_ids": parse_room_unit_ids(room),
        "question_count": int(room.question_count or 0),
        "battle_time_limit_seconds": int(room.battle_time_limit_seconds or 0),
        "member_count": len(ranked_members),
        "ready_count": sum(1 for item in ranked_members if item["is_ready"]),
        "members": ranked_members,
        "created_at": _isoformat_utc(room.created_at),
        "server_now": _isoformat_utc(utcnow()),
        "countdown_started_at": _isoformat_utc(room.countdown_started_at),
        "auto_start_at": _isoformat_utc(room.auto_start_at),
        "started_at": _isoformat_utc(room.started_at),
        "finished_at": _isoformat_utc(room.finished_at),
        "battle_started_at": _isoformat_utc(room.battle_started_at),
        "battle_expires_at": _isoformat_utc(room.battle_expires_at),
    }
    if include_logs and db is not None:
        payload["logs"] = [
            {
                "id": item.id,
                "room_id": item.room_id,
                "message": item.message,
                "category": item.category,
                "created_at": _isoformat_utc(item.created_at),
            }
            for item in load_room_logs(db, room.id)
        ]
    return payload


def find_active_membership_for_user(db: Session, user_id: int) -> PvpRoomMember | None:
    return (
        db.query(PvpRoomMember)
        .join(PvpRoom, PvpRoom.id == PvpRoomMember.room_id)
        .options(joinedload(PvpRoomMember.room).joinedload(PvpRoom.members).joinedload(PvpRoomMember.user))
        .filter(
            PvpRoomMember.user_id == user_id,
            PvpRoom.status.in_(["waiting", "countdown", "running"]),
        )
        .order_by(PvpRoom.created_at.desc(), PvpRoom.id.desc())
        .first()
    )


def find_latest_membership_for_user(db: Session, user_id: int) -> PvpRoomMember | None:
    return (
        db.query(PvpRoomMember)
        .join(PvpRoom, PvpRoom.id == PvpRoomMember.room_id)
        .options(joinedload(PvpRoomMember.room).joinedload(PvpRoom.members).joinedload(PvpRoomMember.user))
        .filter(PvpRoomMember.user_id == user_id)
        .order_by(PvpRoom.created_at.desc(), PvpRoom.id.desc())
        .first()
    )


def _load_admin_room_payloads(db: Session) -> list[dict]:
    rooms = db.query(PvpRoom).order_by(PvpRoom.created_at.desc(), PvpRoom.id.desc()).all()
    changed = False
    room_ids = [room.id for room in rooms]
    for room in rooms:
        if sync_room_runtime_state(db, room):
            changed = True
        if finalize_room_if_needed(db, room):
            changed = True
    if changed:
        db.commit()
        rooms = [load_room_with_members(db, room_id) for room_id in room_ids]
    else:
        rooms = [load_room_with_members(db, room_id) for room_id in room_ids]
    return [serialize_room(room, include_logs=True, db=db) for room in rooms if room is not None]


def _load_student_room_payload(db: Session, user_id: int) -> dict | None:
    membership = find_active_membership_for_user(db, user_id)
    if not membership or not membership.room:
        latest_membership = find_latest_membership_for_user(db, user_id)
        if latest_membership and latest_membership.room and latest_membership.room.status == "finished":
            return serialize_room(latest_membership.room, include_logs=True, db=db)
        return None

    room = membership.room
    if sync_room_runtime_state(db, room):
        db.commit()
        membership = find_active_membership_for_user(db, user_id)
        room = membership.room if membership else None
    elif finalize_room_if_needed(db, room):
        db.commit()
        membership = find_active_membership_for_user(db, user_id)
        room = membership.room if membership else None
    if not room:
        return None
    return serialize_room(room, include_logs=True, db=db)


def build_student_room_payload(db: Session, user_id: int) -> dict | None:
    return _load_student_room_payload(db, user_id)


def build_pvp_battle_session_payload(db: Session, user_id: int) -> dict:
    membership = find_active_membership_for_user(db, user_id)
    if not membership or not membership.room:
        raise LookupError("你当前没有进行中的竞技房间")

    room = membership.room
    if sync_room_runtime_state(db, room):
        db.commit()
        membership = find_active_membership_for_user(db, user_id)
        room = membership.room if membership else None
        if room is None:
            raise LookupError("你当前没有进行中的竞技房间")
    elif finalize_room_if_needed(db, room):
        db.commit()
        raise ValueError("本场对战已结束")

    if room.status != "running":
        raise ValueError("房间尚未开始")

    session, questions = ensure_pvp_battle_session(db, room, user_id)
    question_count = len(questions)
    current_question = build_current_pvp_question_payload(db, session.play_session_id, total_questions=question_count)
    if current_question is None and session.status == "active":
        session.status = "completed"
        session.completed_at = utcnow()
    db.commit()
    room = load_room_with_members(db, room.id)
    session = (
        db.query(PlaySession)
        .filter(PlaySession.play_session_id == session.play_session_id)
        .first()
    )

    return {
        "type": "pvp_battle_session",
        "room": serialize_room(room, include_logs=True, db=db),
        "play_session_id": session.play_session_id,
        "session_status": session.status,
        "question_count": question_count,
        "current_question": current_question,
        "server_now": _isoformat_utc(utcnow()),
        "battle_started_at": _isoformat_utc(room.battle_started_at),
        "battle_expires_at": _isoformat_utc(room.battle_expires_at),
        "battle_answer_accept_until": _isoformat_utc(room.battle_answer_accept_until),
    }


async def _broadcast_pvp_room_change(target_user_ids: set[int]) -> None:
    db = SessionLocal()
    try:
        admin_payloads = _load_admin_room_payloads(db)
        student_payloads = {
            user_id: _load_student_room_payload(db, user_id)
            for user_id in target_user_ids
        }
    finally:
        db.close()

    await manager.send_to_admins({
        "type": "pvp_rooms",
        "rooms": admin_payloads,
    })
    for user_id, room_payload in student_payloads.items():
        await manager.send_to_student(user_id, {
            "type": "pvp_room_state",
            "room": room_payload,
        })


def schedule_pvp_room_change(target_user_ids: set[int]) -> None:
    manager.schedule(_broadcast_pvp_room_change(set(target_user_ids)))


async def _broadcast_student_pvp_room_state(user_id: int) -> None:
    db = SessionLocal()
    try:
        room_payload = _load_student_room_payload(db, user_id)
    finally:
        db.close()

    await manager.send_to_student(user_id, {
        "type": "pvp_room_state",
        "room": room_payload,
    })


def schedule_pvp_student_refresh_for_user(user_id: int) -> None:
    manager.schedule(_broadcast_student_pvp_room_state(user_id))


async def _broadcast_student_pvp_battle_session(user_id: int) -> None:
    db = SessionLocal()
    try:
        try:
            payload = build_pvp_battle_session_payload(db, user_id)
        except LookupError as exc:
            payload = {"type": "pvp_error", "detail": str(exc)}
        except ValueError as exc:
            payload = {"type": "pvp_error", "detail": str(exc)}
    finally:
        db.close()

    await manager.send_to_student(user_id, payload)


def schedule_pvp_battle_snapshot_refresh_for_users(target_user_ids: set[int]) -> None:
    for user_id in set(target_user_ids):
        manager.schedule(_broadcast_student_pvp_battle_session(user_id))


def schedule_pvp_presence_refresh_for_user(user_id: int) -> None:
    db = SessionLocal()
    try:
        membership = find_active_membership_for_user(db, user_id)
        if membership and membership.room:
            target_user_ids = {member.user_id for member in membership.room.members}
        else:
            target_user_ids = {user_id}
    finally:
        db.close()
    schedule_pvp_room_change(target_user_ids)


def add_student_to_room(db: Session, room: PvpRoom, user_id: int) -> PvpRoomMember:
    """Add a student to a PVP room. Validates: not in another active room, room not full, room is waiting."""
    if room.status != "waiting":
        raise ValueError("房间已开始或已结束，无法加入")

    if len(room.members) >= room.group_size:
        raise ValueError("房间已满")

    existing = find_active_membership_for_user(db, user_id)
    if existing:
        raise ValueError("你已在另一个对战房间中")

    seat_order = len(room.members) + 1
    member = PvpRoomMember(
        room_id=room.id,
        user_id=user_id,
        seat_order=seat_order,
        team="solo",
        is_ready=0,
    )
    db.add(member)
    db.flush()
    return member
