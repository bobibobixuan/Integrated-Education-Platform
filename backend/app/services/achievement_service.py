from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.achievement import Achievement, UserAchievement
from backend.app.models.record import LevelProgress, UserStats


DEFAULT_ACHIEVEMENTS: tuple[dict[str, Any], ...] = (
    {
        "id": "first_answer",
        "name": "初次出发",
        "icon": "🌱",
        "description": "第一次完成答题，正式踏上学习旅程。",
        "hint": "先去回答任意一道题目。",
        "rarity": "common",
        "category": "启程",
        "condition_type": "total_questions",
        "condition_value": 1,
    },
    {
        "id": "ten_answers",
        "name": "渐入佳境",
        "icon": "📘",
        "description": "累计完成 10 道题，开始形成稳定节奏。",
        "hint": "继续完成更多题目。",
        "rarity": "common",
        "category": "积累",
        "condition_type": "total_questions",
        "condition_value": 10,
    },
    {
        "id": "fifty_answers",
        "name": "勤学不辍",
        "icon": "🔥",
        "description": "累计完成 50 道题，学习状态持续在线。",
        "hint": "多进行几轮闯关或练习。",
        "rarity": "rare",
        "category": "积累",
        "condition_type": "total_questions",
        "condition_value": 50,
    },
    {
        "id": "correct_ten",
        "name": "稳定命中",
        "icon": "🎯",
        "description": "累计答对 10 道题，已经抓住不少关键知识点。",
        "hint": "把正确题目累计到 10 道。",
        "rarity": "common",
        "category": "准确",
        "condition_type": "total_correct",
        "condition_value": 10,
    },
    {
        "id": "combo_master",
        "name": "连击达人",
        "icon": "⚡",
        "description": "单次最高连对达到 5 题，保持住你的节奏。",
        "hint": "尝试连续答对 5 道题。",
        "rarity": "rare",
        "category": "连击",
        "condition_type": "max_combo",
        "condition_value": 5,
    },
    {
        "id": "first_level_clear",
        "name": "首次通关",
        "icon": "🏅",
        "description": "完成任意一个关卡，拿下第一块通关徽章。",
        "hint": "完成一个冒险关卡并获得星级。",
        "rarity": "common",
        "category": "闯关",
        "condition_type": "completed_levels",
        "condition_value": 1,
    },
    {
        "id": "practice_rookie",
        "name": "练习学徒",
        "icon": "🧩",
        "description": "完成一次随机练习，开始主动查漏补缺。",
        "hint": "进入随机练习并完成一次结算。",
        "rarity": "common",
        "category": "练习",
        "condition_type": "practice_count",
        "condition_value": 1,
    },
    {
        "id": "extreme_breakthrough",
        "name": "极限突破",
        "icon": "🚀",
        "description": "完成一次极限挑战，证明你能在压力下稳定输出。",
        "hint": "完成一次极限挑战。",
        "rarity": "epic",
        "category": "挑战",
        "condition_type": "extreme_passes",
        "condition_value": 1,
    },
)

RARITY_ORDER = {
    "common": 0,
    "rare": 1,
    "epic": 2,
    "legendary": 3,
}


def ensure_default_achievements(db: Session) -> None:
    existing_ids = {
        achievement_id
        for (achievement_id,) in db.query(Achievement.id).all()
    }
    for item in DEFAULT_ACHIEVEMENTS:
        if item["id"] in existing_ids:
            continue
        db.add(Achievement(**item))
        existing_ids.add(item["id"])
    db.flush()


def _get_user_stats(db: Session, user_id: int) -> UserStats | None:
    return db.query(UserStats).filter(UserStats.user_id == user_id).first()


def _completed_level_count(db: Session, user_id: int) -> int:
    return (
        db.query(LevelProgress)
        .filter(
            LevelProgress.user_id == user_id,
            LevelProgress.stars > 0,
        )
        .count()
    )


def _achievement_metric(db: Session, user_id: int, condition_type: str) -> int:
    stats = _get_user_stats(db, user_id)
    if condition_type == "completed_levels":
        return _completed_level_count(db, user_id)
    if not stats:
        return 0
    return int(getattr(stats, condition_type, 0) or 0)


def evaluate_user_achievements(db: Session, user_id: int) -> list[Achievement]:
    ensure_default_achievements(db)

    unlocked_ids = {
        achievement_id
        for (achievement_id,) in (
            db.query(UserAchievement.achievement_id)
            .filter(UserAchievement.user_id == user_id)
            .all()
        )
    }
    newly_unlocked: list[Achievement] = []

    all_achievements = sorted(
        db.query(Achievement).all(),
        key=lambda item: (RARITY_ORDER.get(item.rarity, 99), item.id),
    )
    for achievement in all_achievements:
        if achievement.id in unlocked_ids:
            continue
        metric = _achievement_metric(db, user_id, achievement.condition_type)
        if metric < (achievement.condition_value or 0):
            continue
        db.add(
            UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
            )
        )
        unlocked_ids.add(achievement.id)
        newly_unlocked.append(achievement)

    db.flush()
    return newly_unlocked


def build_achievement_wall(db: Session, user_id: int) -> list[dict[str, Any]]:
    ensure_default_achievements(db)
    evaluate_user_achievements(db, user_id)

    unlocked_map = {
        row.achievement_id: row
        for row in (
            db.query(UserAchievement)
            .filter(UserAchievement.user_id == user_id)
            .all()
        )
    }
    all_achievements = sorted(
        db.query(Achievement).all(),
        key=lambda item: (RARITY_ORDER.get(item.rarity, 99), item.id),
    )

    return [
        {
            "id": achievement.id,
            "name": achievement.name,
            "icon": achievement.icon,
            "description": achievement.description,
            "hint": achievement.hint,
            "rarity": achievement.rarity,
            "category": achievement.category,
            "unlocked": achievement.id in unlocked_map,
            "unlocked_at": (
                unlocked_map[achievement.id].unlocked_at.isoformat()
                if achievement.id in unlocked_map and unlocked_map[achievement.id].unlocked_at
                else None
            ),
        }
        for achievement in all_achievements
    ]


def serialize_new_achievements(items: list[Achievement]) -> list[dict[str, Any]]:
    return [
        {
            "id": item.id,
            "name": item.name,
            "icon": item.icon,
            "description": item.description,
            "rarity": item.rarity,
            "category": item.category,
        }
        for item in items
    ]
