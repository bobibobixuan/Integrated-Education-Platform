import json
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.unit import Unit, Level
from backend.app.models.question import Question
from backend.app.models.record import (
    AnswerRecord, LevelProgress, UserStats, PlaySession, SessionQuestion, ScoreReviewDecision,
)


def calc_stars(correct_count: int, total_count: int, threshold_str: str = "[60,80,100]") -> int:
    if total_count <= 0:
        return 0
    percentage = correct_count * 100 / total_count
    thresholds = json.loads(threshold_str) if isinstance(threshold_str, str) else threshold_str
    stars = 0
    for t in thresholds:
        if percentage >= t:
            stars += 1
    return stars


def calc_combo(is_correct: bool, current_combo: int) -> int:
    return current_combo + 1 if is_correct else 0


def is_extreme_pass(is_correct: bool, time_spent: float, threshold: float = 10.0) -> bool:
    return is_correct and time_spent <= threshold


def calc_power_bonus(is_correct: bool, combo: int, time_spent: float) -> int:
    if not is_correct:
        return 0
    base = 100
    if time_spent <= 5:
        base += 10
    if combo >= 2:
        base += min(combo - 1, 5) * 10
    return base


# ── Power scoring (DB-aware) ──


def _get_level_question_count(db: Session, level_id: int) -> int:
    return (
        db.query(Question)
        .filter(Question.level_id == level_id, Question.is_active == True)
        .count()
    )


def _is_session_suspicious(db: Session, play_session_id: str, level_id: int) -> bool:
    total_q = _get_level_question_count(db, level_id)
    threshold = min(5, total_q)

    records = (
        db.query(AnswerRecord)
        .filter(AnswerRecord.play_session_id == play_session_id)
        .join(SessionQuestion, SessionQuestion.question_id == AnswerRecord.question_id)
        .filter(SessionQuestion.play_session_id == play_session_id)
        .order_by(SessionQuestion.question_order)
        .all()
    )

    if len(records) < threshold:
        return False

    times = [r.time_spent for r in records[-threshold:]]
    if times and all(abs(t - 2.0) < 1e-6 for t in times):
        return False
    try:
        return statistics.stdev(times) < 0.3
    except statistics.StatisticsError:
        return False


def calc_level_power(db: Session, user_id: int, level_id: int) -> dict:
    total_q = _get_level_question_count(db, level_id)
    sessions = (
        db.query(PlaySession)
        .filter(PlaySession.user_id == user_id, PlaySession.level_id == level_id)
        .all()
    )

    review_decisions = {}
    for rd in (
        db.query(ScoreReviewDecision)
        .filter(ScoreReviewDecision.user_id == user_id, ScoreReviewDecision.level_id == level_id)
        .all()
    ):
        if rd.scope == "level" and rd.decision == "clear":
            return {"clear": 0, "perfect": 0, "speed": 0, "combo": 0, "total": 0, "is_suspicious": False}
        review_decisions[rd.play_session_id] = rd.decision

    best_total = 0
    best_result = {"clear": 0, "perfect": 0, "speed": 0, "combo": 0, "total": 0, "is_suspicious": False}
    best_max_combo = 0

    for ps in sessions:
        if ps.status != "completed":
            continue

        decision = review_decisions.get(ps.play_session_id, None)
        if decision == "exclude":
            continue

        is_suspicious_val = ps.is_suspicious
        if decision == "approve":
            is_suspicious_val = False

        if not is_suspicious_val:
            is_suspicious_val = _is_session_suspicious(db, ps.play_session_id, level_id)

        records = (
            db.query(AnswerRecord)
            .filter(AnswerRecord.play_session_id == ps.play_session_id)
            .join(SessionQuestion, SessionQuestion.question_id == AnswerRecord.question_id)
            .filter(SessionQuestion.play_session_id == ps.play_session_id)
            .order_by(SessionQuestion.question_order)
            .all()
        )

        correct_count = sum(1 for r in records if r.is_correct)
        pass_threshold = int(total_q * 0.8) if total_q > 0 else 0

        clear = 100 if correct_count >= pass_threshold else 0
        perfect = 100 if correct_count == total_q and total_q > 0 else 0
        speed = 0
        combo = 0

        if not is_suspicious_val:
            times = [r.time_spent for r in records]
            if times:
                avg_time = sum(times) / len(times)
                if avg_time <= 30:
                    speed = 50

            current_combo = 0
            max_combo = 0
            for r in records:
                if r.is_correct:
                    current_combo += 1
                    max_combo = max(max_combo, current_combo)
                else:
                    current_combo = 0
            if max_combo >= total_q:
                combo = 50
                best_max_combo = max(best_max_combo, max_combo)

        total = clear + perfect + speed + combo
        if total > best_total:
            best_total = total
            best_result = {
                "clear": clear, "perfect": perfect, "speed": speed, "combo": combo,
                "total": total, "is_suspicious": is_suspicious_val,
            }

    return best_result


def calc_total_power(db: Session, user_id: int) -> tuple[int, list[dict]]:
    levels = (
        db.query(Level)
        .filter(Level.is_active == True)
        .all()
    )
    total = 0
    breakdown = []
    for level in levels:
        unit = db.query(Unit).filter(Unit.id == level.unit_id).first()
        result = calc_level_power(db, user_id, level.id)
        total += result["total"]
        breakdown.append({
            "level_id": level.id,
            "unit_name": unit.name if unit else "",
            "level_name": level.name,
            **result,
        })

    stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()
    if stats:
        stats.power_score = total
        db.flush()

    return total, breakdown


def calc_weekly_activity(db: Session, user_id: int) -> int:
    total_seconds = (
        db.query(func.coalesce(func.sum(AnswerRecord.time_spent), 0))
        .filter(AnswerRecord.user_id == user_id)
        .scalar()
    )
    return int(round(total_seconds or 0))
