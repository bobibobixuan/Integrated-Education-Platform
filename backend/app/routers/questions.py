from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.deps import get_db
from backend.app.models.unit import Level
from backend.app.models.question import Question
from backend.app.schemas.question import QuestionOut
from backend.app.routers import questions_router
from backend.app.services.question_service import get_effective_question_type


@questions_router.get("/batch", response_model=list[QuestionOut])
def get_questions_batch(
    ids: str = Query(..., description="逗号分隔的题目ID列表"),
    db: Session = Depends(get_db),
):
    """按ID批量查询题目（错题本用）。"""
    id_list = []
    for part in ids.split(","):
        part = part.strip()
        if part.isdigit():
            id_list.append(int(part))

    if not id_list:
        return []

    questions = (
        db.query(Question)
        .filter(Question.id.in_(id_list), Question.is_active == True)
        .all()
    )

    id_to_level = {}
    level_ids = {q.level_id for q in questions}
    if level_ids:
        levels = db.query(Level).filter(Level.id.in_(level_ids)).all()
        id_to_level = {l.id: l for l in levels}

    results = []
    for q in questions:
        level = id_to_level.get(q.level_id)
        results.append(QuestionOut(
            id=q.id,
            level_id=q.level_id,
            unit_id=level.unit_id if level else 0,
            type=get_effective_question_type(q),
            content=q.content,
            options=q.options,
            question_order=q.sort_order,
            total_questions=0,
            knowledge_meaning=q.knowledge_meaning or "",
            knowledge_rule=q.knowledge_rule or "",
            knowledge_error=q.knowledge_error or "",
            knowledge_example=q.knowledge_example or "",
        ))

    return results


@questions_router.get("/units/{unit_id}", response_model=list[QuestionOut])
def get_unit_questions(unit_id: int, db: Session = Depends(get_db)):
    """返回某个单元下所有活跃关卡的所有活跃题目（练习模式用）。"""
    levels = (
        db.query(Level)
        .filter(Level.unit_id == unit_id, Level.is_active == True)
        .all()
    )

    if not levels:
        return []

    level_ids = [l.id for l in levels]
    id_to_level = {l.id: l for l in levels}

    questions = (
        db.query(Question)
        .filter(Question.level_id.in_(level_ids), Question.is_active == True)
        .order_by(Question.sort_order)
        .all()
    )

    return [
        QuestionOut(
            id=q.id,
            level_id=q.level_id,
            unit_id=unit_id,
            type=get_effective_question_type(q),
            content=q.content,
            options=q.options,
            question_order=q.sort_order,
            total_questions=0,
            knowledge_meaning=q.knowledge_meaning or "",
            knowledge_rule=q.knowledge_rule or "",
            knowledge_error=q.knowledge_error or "",
            knowledge_example=q.knowledge_example or "",
        )
        for q in questions
    ]


@questions_router.get("/levels/{level_id}", response_model=list[QuestionOut])
def get_level_questions(level_id: int, db: Session = Depends(get_db)):
    """获取指定关卡的所有活跃题目。"""
    level = db.query(Level).filter(Level.id == level_id, Level.is_active == True).first()
    if not level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关卡不存在")

    questions = (
        db.query(Question)
        .filter(Question.level_id == level_id, Question.is_active == True)
        .order_by(Question.sort_order)
        .all()
    )

    return [
        QuestionOut(
            id=q.id,
            level_id=level.id,
            unit_id=level.unit_id,
            type=get_effective_question_type(q),
            content=q.content,
            options=q.options,
            question_order=q.sort_order,
            total_questions=len(questions),
            knowledge_meaning=q.knowledge_meaning or "",
            knowledge_rule=q.knowledge_rule or "",
            knowledge_error=q.knowledge_error or "",
            knowledge_example=q.knowledge_example or "",
        )
        for q in questions
    ]


@questions_router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    """按ID获取单道题目。"""
    q = db.query(Question).filter(Question.id == question_id, Question.is_active == True).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

    level = db.query(Level).filter(Level.id == q.level_id).first()

    return QuestionOut(
        id=q.id,
        level_id=q.level_id,
        unit_id=level.unit_id if level else 0,
        type=get_effective_question_type(q),
        content=q.content,
        options=q.options,
        question_order=q.sort_order,
        total_questions=0,
        knowledge_meaning=q.knowledge_meaning or "",
        knowledge_rule=q.knowledge_rule or "",
        knowledge_error=q.knowledge_error or "",
        knowledge_example=q.knowledge_example or "",
    )
