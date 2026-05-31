from pydantic import BaseModel, Field


class QuestionOut(BaseModel):
    id: int
    level_id: int
    unit_id: int = 0
    type: str
    content: str
    options: list[dict] | None = None
    question_order: int = 0
    total_questions: int = 0
    knowledge_meaning: str = ""
    knowledge_rule: str = ""
    knowledge_error: str = ""
    knowledge_example: str = ""
    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    question_id: int
    submitted_answer: str
    play_session_id: str = ""
    client_time_spent: float = 0.0


class AnswerResult(BaseModel):
    success: bool
    is_correct: bool
    correct_answer: str = ""
    knowledge: dict | None = None
    stars_earned: int = 0
    new_combo: int = 0
    is_extreme_pass: bool = False
    is_dual_pass: bool = False
