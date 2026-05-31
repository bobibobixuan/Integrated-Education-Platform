import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case, text
from sqlalchemy.exc import IntegrityError

from backend.app.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.models.unit import Unit, Level
from backend.app.models.question import Question
from backend.app.models.record import AnswerRecord, LevelProgress, UserStats, PlaySession, SessionQuestion
from backend.app.schemas.record import (
    RecordOut, LevelProgressOut, UserStatsOut,
    StartSessionIn, StartSessionOut,
    NextQuestionIn, NextQuestionOut,
    AnswerSubmitIn, AnswerSubmitResponse,
    SyncStatsIn,
)
from backend.app.routers import records_router
from backend.app.services.achievement_service import evaluate_user_achievements, serialize_new_achievements
from backend.app.services.rate_limiter import check_action_rate_limit
from backend.app.services.scoring_service import calc_total_power
from backend.app.services.question_service import get_effective_question_type, is_submitted_answer_correct
from backend.app.utils import utcnow, as_utc


def _normalize_options(raw_options):
    if raw_options is None:
        return None
    if isinstance(raw_options, list):
        return raw_options
    return None


def _upsert_level_progress(db: Session, user_id: int, level_id: int, correct_count: int, total_questions: int, best_combo: int) -> None:
    progress = db.query(LevelProgress).filter(
        LevelProgress.user_id == user_id,
        LevelProgress.level_id == level_id,
    ).first()
    if not progress:
        progress = LevelProgress(user_id=user_id, level_id=level_id)
        db.add(progress)

    progress.unlocked = True
    if total_questions > 0:
        accuracy = correct_count / total_questions
        if accuracy >= 1.0:
            progress.stars = max(progress.stars or 0, 3)
        elif accuracy >= 0.6:
            progress.stars = max(progress.stars or 0, 2)
        elif accuracy >= 0.3:
            progress.stars = max(progress.stars or 0, 1)
    progress.best_combo = max(progress.best_combo or 0, best_combo)


@records_router.get("/summary", response_model=UserStatsOut)
def get_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stats = db.query(UserStats).filter(UserStats.user_id == user.id).first()
    if not stats:
        return UserStatsOut(
            total_questions=0,
            total_correct=0,
            total_score=0,
            power_score=0,
            max_combo=0,
            practice_count=0,
            extreme_passes=0,
            extreme_dual_passes=0,
        )
    return UserStatsOut.model_validate(stats)


@records_router.get("/progress", response_model=list[LevelProgressOut])
def get_level_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    progresses = (
        db.query(LevelProgress)
        .filter(LevelProgress.user_id == user.id)
        .all()
    )
    return [
        LevelProgressOut(
            level_id=lp.level_id,
            stars=lp.stars,
            unlocked=lp.unlocked,
            best_combo=lp.best_combo,
        )
        for lp in progresses
    ]


@records_router.get("/recent", response_model=list[RecordOut])
def get_recent_records(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    records = (
        db.query(AnswerRecord)
        .filter(AnswerRecord.user_id == user.id)
        .order_by(AnswerRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return [RecordOut.model_validate(r) for r in records]


@records_router.get("/wrong")
def get_wrong_questions(
    limit: int = 200,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    records = (
        db.query(AnswerRecord)
        .filter(AnswerRecord.user_id == user.id, AnswerRecord.is_correct == False)
        .order_by(AnswerRecord.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for r in records:
        q = r.question
        level = q.level if q else None
        unit = level.unit if level else None
        result.append({
            "id": r.id,
            "question_id": r.question_id,
            "question_content": q.content if q else "题目已移除",
            "question_type": get_effective_question_type(q) if q else "未知",
            "user_answer": r.user_answer,
            "correct_answer": q.answer if q else "未知",
            "unit_id": unit.id if unit else 0,
            "unit_name": unit.name if unit else "未知单元",
            "level_id": level.id if level else 0,
            "level_name": level.name if level else "未知关卡",
            "timestamp": r.created_at.isoformat() if r.created_at else "",
            "knowledge": {
                "meaning": q.knowledge_meaning,
                "rule": q.knowledge_rule,
                "error": q.knowledge_error,
                "example": q.knowledge_example,
            } if q else None,
        })
    return result


# ── Play Session ──

@records_router.post("/start-session", response_model=StartSessionOut)
def start_session(body: StartSessionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not check_action_rate_limit(f"start_session:{user.id}", max_requests=10, window_seconds=60):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="操作太频繁，请稍后再试")

    level = db.query(Level).filter(Level.id == body.level_id, Level.is_active == True).first()
    if not level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关卡不存在")

    now = utcnow()
    old_sessions = (
        db.query(PlaySession)
        .filter(PlaySession.user_id == user.id, PlaySession.level_id == body.level_id)
        .all()
    )
    for s in old_sessions:
        if s.status == "active":
            expires_at = as_utc(s.expires_at)
            if expires_at and expires_at < now:
                s.status = "expired"
            else:
                s.status = "abandoned"

    play_session_id = str(uuid.uuid4())
    expires_at = now + timedelta(minutes=30)

    ps = PlaySession(
        play_session_id=play_session_id,
        user_id=user.id,
        level_id=body.level_id,
        mode=body.mode or "adventure",
        status="active",
        expires_at=expires_at,
    )
    db.add(ps)

    questions = (
        db.query(Question)
        .filter(Question.level_id == body.level_id, Question.is_active == True)
        .order_by(Question.sort_order)
        .all()
    )
    for i, q in enumerate(questions):
        sq = SessionQuestion(
            play_session_id=play_session_id,
            question_id=q.id,
            question_order=i,
        )
        db.add(sq)

    db.commit()
    return StartSessionOut(
        play_session_id=play_session_id,
        started_at=now.isoformat(),
        question_count=len(questions),
    )


@records_router.post("/next-question", response_model=NextQuestionOut)
def next_question(body: NextQuestionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ps = (
        db.query(PlaySession)
        .filter(PlaySession.play_session_id == body.play_session_id, PlaySession.user_id == user.id)
        .first()
    )
    if not ps:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session 不存在")
    if ps.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session 已结束")

    current_sq = (
        db.query(SessionQuestion)
        .filter(
            SessionQuestion.play_session_id == body.play_session_id,
            SessionQuestion.answered_at == None,
        )
        .order_by(SessionQuestion.question_order)
        .first()
    )
    if not current_sq:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="所有题目已答完")

    if current_sq.delivered_at is None:
        db.execute(
            text(
                "UPDATE session_questions SET delivered_at = CURRENT_TIMESTAMP "
                "WHERE id = :id AND delivered_at IS NULL"
            ),
            {"id": current_sq.id},
        )
        db.commit()
        db.refresh(current_sq)

    q = db.query(Question).filter(Question.id == current_sq.question_id).first()
    total = (
        db.query(SessionQuestion)
        .filter(SessionQuestion.play_session_id == body.play_session_id)
        .count()
    )
    options = _normalize_options(q.options)

    return NextQuestionOut(
        question_id=q.id,
        content=q.content,
        question_type=get_effective_question_type(q),
        options=options,
        question_order=current_sq.question_order,
        total_questions=total,
    )


@records_router.post("/answer", response_model=AnswerSubmitResponse)
def submit_answer(body: AnswerSubmitIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ps = (
        db.query(PlaySession)
        .filter(
            PlaySession.play_session_id == body.play_session_id,
            PlaySession.user_id == user.id,
        )
        .first()
    )
    if not ps:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session 不存在")
    if ps.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session 已结束")

    now = utcnow()
    expires_at = as_utc(ps.expires_at)
    if expires_at and expires_at < now:
        ps.status = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session 已过期")

    # Rate limit: max 10 answers per 10s per (user, level)
    if not check_action_rate_limit(f"answer_{user.id}_{ps.level_id}", max_requests=10, window_seconds=10):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="提交过于频繁")

    current_sq = (
        db.query(SessionQuestion)
        .filter(
            SessionQuestion.play_session_id == body.play_session_id,
            SessionQuestion.question_id == body.question_id,
            SessionQuestion.answered_at == None,
        )
        .first()
    )
    if not current_sq:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该题目不在当前 session 中或已答过")

    if current_sq.delivered_at is None:
        current_sq.delivered_at = now

    question = db.query(Question).filter(Question.id == body.question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

    is_correct = is_submitted_answer_correct(question, body.submitted_answer)

    delivered_at = as_utc(current_sq.delivered_at)
    server_delta = (now - delivered_at).total_seconds() if delivered_at else body.client_time_spent
    effective_time = max(body.client_time_spent, server_delta)
    if effective_time < 2.0:
        effective_time = 2.0

    record = AnswerRecord(
        user_id=user.id,
        question_id=body.question_id,
        user_answer=body.submitted_answer,
        is_correct=is_correct,
        time_spent=effective_time,
        mode=ps.mode or "adventure",
        play_session_id=body.play_session_id,
        question_version=getattr(question, 'version', 1),
        correct_answer_snapshot=question.answer,
    )
    db.add(record)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(AnswerRecord)
            .filter(
                AnswerRecord.play_session_id == body.play_session_id,
                AnswerRecord.question_id == body.question_id,
            )
            .first()
        )
        return AnswerSubmitResponse(
            success=True,
            is_correct=existing.is_correct,
            correct_answer=existing.correct_answer_snapshot or "",
            score_added=0,
        )

    current_sq.answered_at = now
    db.flush()

    unanswered = (
        db.query(SessionQuestion)
        .filter(
            SessionQuestion.play_session_id == body.play_session_id,
            SessionQuestion.answered_at == None,
        )
        .count()
    )
    if unanswered == 0:
        ps.status = "completed"
        ps.completed_at = now
        session_records = (
            db.query(AnswerRecord)
            .filter(AnswerRecord.play_session_id == body.play_session_id)
            .join(SessionQuestion, SessionQuestion.question_id == AnswerRecord.question_id)
            .filter(SessionQuestion.play_session_id == body.play_session_id)
            .order_by(SessionQuestion.question_order)
            .all()
        )
        correct_count = sum(1 for item in session_records if item.is_correct)
        current_combo = 0
        best_combo = 0
        for item in session_records:
            if item.is_correct:
                current_combo += 1
                best_combo = max(best_combo, current_combo)
            else:
                current_combo = 0
        ps.best_combo = best_combo
        if (ps.mode or "adventure") != "pvp":
            total_q = len(session_records)
            _upsert_level_progress(db, user.id, ps.level_id, correct_count, total_q, best_combo)

    stats = db.query(UserStats).filter(UserStats.user_id == user.id).first()
    if not stats:
        stats = UserStats(user_id=user.id)
        db.add(stats)
        db.flush()

    stats.total_questions += 1
    if is_correct:
        stats.total_correct += 1
        stats.total_score += 100
    stats.max_combo = max(stats.max_combo or 0, ps.best_combo or 0)

    if unanswered == 0 and (ps.mode or "adventure") != "pvp":
        calc_total_power(db, user.id)

    new_achievements = evaluate_user_achievements(db, user.id)
    db.commit()

    return AnswerSubmitResponse(
        success=True,
        is_correct=is_correct,
        correct_answer=question.answer,
        score_added=100 if is_correct else 0,
        new_achievements=serialize_new_achievements(new_achievements),
    )


# ── Stats Sync (practice count, extreme passes) ──

@records_router.post("/stats", response_model=UserStatsOut)
def sync_stats(body: SyncStatsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """同步前端统计：练习次数、极限通关次数等（练习/极限模式前端结算后调用）。"""
    stats = db.query(UserStats).filter(UserStats.user_id == user.id).first()
    if not stats:
        stats = UserStats(user_id=user.id)
        db.add(stats)
        db.flush()

    if body.practice_increment:
        stats.practice_count = (stats.practice_count or 0) + body.practice_increment
    if body.extreme_pass_increment:
        stats.extreme_passes = (stats.extreme_passes or 0) + body.extreme_pass_increment
    if body.extreme_dual_pass_increment:
        stats.extreme_dual_passes = (stats.extreme_dual_passes or 0) + body.extreme_dual_pass_increment

    evaluate_user_achievements(db, user.id)
    db.commit()
    db.refresh(stats)
    return UserStatsOut.model_validate(stats)
