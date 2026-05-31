from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.models.unit import Unit, Level
from backend.app.models.record import LevelProgress, UserStats
from backend.app.services.scoring_service import calc_total_power
from backend.app.routers import scores_router


@scores_router.get("/progress")
def get_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    units = db.query(Unit).filter(Unit.is_active == True).order_by(Unit.sort_order).all()
    result = []

    for unit in units:
        levels = (
            db.query(Level)
            .filter(Level.unit_id == unit.id, Level.is_active == True)
            .order_by(Level.sort_order)
            .all()
        )
        level_progresses = {
            lp.level_id: lp
            for lp in db.query(LevelProgress)
            .filter(LevelProgress.user_id == user.id, LevelProgress.level_id.in_([l.id for l in levels]))
            .all()
        }

        result.append({
            "unit_id": unit.id,
            "unit_name": unit.name,
            "unit_icon": unit.icon,
            "levels": [
                {
                    "level_id": l.id,
                    "name": l.name,
                    "icon": l.icon,
                    "bg": l.bg,
                    "stars": level_progresses[l.id].stars if l.id in level_progresses else 0,
                    "unlocked": level_progresses[l.id].unlocked if l.id in level_progresses else (l.sort_order == 0),
                }
                for l in levels
            ],
        })

    return result


@scores_router.get("/power")
def get_power_score(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total, breakdown = calc_total_power(db, user.id)

    return {
        "power_score": total,
        "weekly_activity": 0,
        "level_breakdown": [
            {
                "level_id": b["level_id"],
                "unit_name": b["unit_name"],
                "level_name": b["level_name"],
                "clear": b["clear"],
                "perfect": b["perfect"],
                "speed": b["speed"],
                "combo": b["combo"],
                "total": b["total"],
            }
            for b in breakdown
        ],
    }


@scores_router.get("/stats")
def get_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stats = db.query(UserStats).filter(UserStats.user_id == user.id).first()
    if not stats:
        return {
            "total_questions": 0,
            "total_correct": 0,
            "accuracy": 0.0,
            "total_score": 0,
            "power_score": 0,
            "max_combo": 0,
            "practice_count": 0,
            "extreme_passes": 0,
            "extreme_dual_passes": 0,
        }
    accuracy = (
        round(stats.total_correct / stats.total_questions * 100, 1)
        if stats.total_questions > 0 else 0.0
    )
    return {
        "total_questions": stats.total_questions,
        "total_correct": stats.total_correct,
        "accuracy": accuracy,
        "total_score": stats.total_score,
        "power_score": stats.power_score,
        "max_combo": stats.max_combo,
        "practice_count": stats.practice_count,
        "extreme_passes": stats.extreme_passes,
        "extreme_dual_passes": stats.extreme_dual_passes,
    }
