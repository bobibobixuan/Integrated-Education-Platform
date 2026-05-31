from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.deps import get_db
from backend.app.models.unit import Unit, Level
from backend.app.routers import units_router


@units_router.get("/with-levels")
def list_units_with_levels(db: Session = Depends(get_db)):
    """返回所有活跃单元及其嵌套关卡列表。"""
    units = (
        db.query(Unit)
        .filter(Unit.is_active == True)
        .order_by(Unit.sort_order, Unit.id)
        .all()
    )

    result = []
    for u in units:
        levels = sorted(
            [l for l in u.levels if l.is_active],
            key=lambda l: (l.sort_order, l.id),
        )
        result.append({
            "id": u.id,
            "name": u.name,
            "icon": u.icon,
            "subtitle": u.subtitle,
            "description": u.description,
            "learning_goal": u.learning_goal,
            "coach_line": u.coach_line,
            "starter_tip": u.starter_tip,
            "color": u.color,
            "sort_order": u.sort_order,
            "levels": [
                {
                    "id": l.id,
                    "unit_id": l.unit_id,
                    "name": l.name,
                    "icon": l.icon,
                    "bg": l.bg,
                    "questions": l.questions_count,
                    "sort_order": l.sort_order,
                }
                for l in levels
            ],
        })

    return result


@units_router.get("/")
def list_units(db: Session = Depends(get_db)):
    units = db.query(Unit).filter(Unit.is_active == True).order_by(Unit.sort_order).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "icon": u.icon,
            "subtitle": u.subtitle,
            "description": u.description,
            "learning_goal": u.learning_goal,
            "coach_line": u.coach_line,
            "starter_tip": u.starter_tip,
            "color": u.color,
            "levels": len(u.levels),
        }
        for u in units
    ]


@units_router.get("/{unit_id}/levels")
def list_levels(unit_id: int, db: Session = Depends(get_db)):
    levels = (
        db.query(Level)
        .filter(Level.unit_id == unit_id, Level.is_active == True)
        .order_by(Level.sort_order)
        .all()
    )
    return [
        {
            "id": l.id,
            "unit_id": l.unit_id,
            "name": l.name,
            "icon": l.icon,
            "bg": l.bg,
            "questions": l.questions_count,
            "sort_order": l.sort_order,
        }
        for l in levels
    ]
