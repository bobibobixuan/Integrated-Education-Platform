from backend.app.models.user import User
from backend.app.models.unit import Unit, Level
from backend.app.models.question import Question


def create_user(db, username="testuser", password_hash="hash", nickname="Test", role="user", is_active=True):
    user = User(username=username, password_hash=password_hash, nickname=nickname, role=role, is_active=is_active)
    db.add(user)
    db.flush()
    return user


def create_unit(db, name="Test Unit", sort_order=1):
    unit = Unit(name=name, sort_order=sort_order)
    db.add(unit)
    db.flush()
    return unit


def create_level(db, unit_id, name="Test Level", sort_order=1):
    level = Level(unit_id=unit_id, name=name, sort_order=sort_order)
    db.add(level)
    db.flush()
    return level


def create_question(db, level_id, type="选择题", content="test?", answer="A", sort_order=1):
    question = Question(level_id=level_id, title="test", type=type, content=content, answer=answer, sort_order=sort_order)
    db.add(question)
    db.flush()
    return question
