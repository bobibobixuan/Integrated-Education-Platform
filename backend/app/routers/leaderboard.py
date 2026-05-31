from fastapi import Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.app.deps import get_db, get_optional_user
from backend.app.models.user import User
from backend.app.models.record import UserStats, LevelProgress
from backend.app.routers import leaderboard_router


@leaderboard_router.get("/")
def get_leaderboard(
    type: str = Query("power"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    if type == "weekly":
        return _get_weekly_leaderboard(db, current_user, limit)

    # 战力总榜
    rows = (
        db.query(UserStats, User.nickname, User.id.label("uid"))
        .join(User, UserStats.user_id == User.id)
        .filter(User.is_active == True, User.role != "admin")
        .order_by(
            desc(UserStats.power_score),
            desc(
                func.coalesce(
                    UserStats.total_correct * 100.0 / func.nullif(UserStats.total_questions, 0), 0
                ).label("accuracy")
            ),
            User.id.asc(),
        )
        .limit(limit)
        .all()
    )

    entries = []
    for rank, (stats, nickname, uid) in enumerate(rows, start=1):
        accuracy = (
            round(stats.total_correct / stats.total_questions * 100, 1)
            if stats.total_questions > 0 else 0.0
        )
        completed = (
            db.query(LevelProgress)
            .filter(LevelProgress.user_id == uid, LevelProgress.stars > 0)
            .count()
        )
        total_stars_q = (
            db.query(func.coalesce(func.sum(LevelProgress.stars), 0))
            .filter(LevelProgress.user_id == uid)
            .scalar()
        )
        entries.append({
            "user_id": uid,
            "rank": rank,
            "nickname": nickname,
            "power_score": stats.power_score,
            "accuracy": accuracy,
            "completed_levels": completed,
            "total_stars": total_stars_q,
        })

    # my_rank
    my_entry = next((e for e in entries if current_user and e["user_id"] == current_user.id), None)
    if my_entry is None and current_user:
        my_stats = db.query(UserStats).filter(UserStats.user_id == current_user.id).first()
        if my_stats:
            my_accuracy = (
                round(my_stats.total_correct / my_stats.total_questions * 100, 1)
                if my_stats.total_questions > 0 else 0.0
            )
            my_completed = (
                db.query(LevelProgress)
                .filter(LevelProgress.user_id == current_user.id, LevelProgress.stars > 0)
                .count()
            )
            my_stars = (
                db.query(func.coalesce(func.sum(LevelProgress.stars), 0))
                .filter(LevelProgress.user_id == current_user.id)
                .scalar()
            )
            my_entry = {
                "user_id": current_user.id,
                "rank": 0,
                "nickname": current_user.nickname,
                "power_score": my_stats.power_score,
                "accuracy": my_accuracy,
                "completed_levels": my_completed,
                "total_stars": my_stars,
            }

    return {"entries": entries, "my_rank": my_entry}


def _get_weekly_leaderboard(db: Session, current_user: User | None, limit: int) -> dict:
    from backend.app.services.scoring_service import calc_weekly_activity
    users = (
        db.query(User)
        .filter(User.is_active == True, User.role != "admin")
        .all()
    )

    user_scores = []
    for u in users:
        activity = calc_weekly_activity(db, u.id)
        if activity > 0:
            user_scores.append((u, activity))

    user_scores.sort(key=lambda x: x[1], reverse=True)
    user_scores = user_scores[:limit]

    entries = []
    for rank, (u, activity) in enumerate(user_scores, start=1):
        entries.append({
            "user_id": u.id,
            "rank": rank,
            "nickname": u.nickname,
            "weekly_activity": activity,
        })

    my_entry = next((e for e in entries if current_user and e["user_id"] == current_user.id), None)
    if my_entry is None and current_user:
        my_activity = calc_weekly_activity(db, current_user.id)
        my_entry = {
            "user_id": current_user.id,
            "rank": 0,
            "nickname": current_user.nickname,
            "weekly_activity": my_activity,
        }

    return {"entries": entries, "my_rank": my_entry}
