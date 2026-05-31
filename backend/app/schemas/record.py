from pydantic import BaseModel


# ── Play Session ──

class StartSessionIn(BaseModel):
    level_id: int
    mode: str = "adventure"  # adventure | extreme | practice


class StartSessionOut(BaseModel):
    play_session_id: str
    started_at: str
    question_count: int


class NextQuestionIn(BaseModel):
    play_session_id: str


class NextQuestionOut(BaseModel):
    question_id: int
    content: str
    question_type: str
    options: list[dict] | None = None
    question_order: int
    total_questions: int


class AnswerSubmitIn(BaseModel):
    play_session_id: str
    question_id: int
    submitted_answer: str
    client_time_spent: float = 0.0


class AnswerSubmitResponse(BaseModel):
    success: bool
    is_correct: bool = False
    correct_answer: str = ""
    score_added: int = 0
    new_achievements: list[dict] = []


# ── Records ──

class RecordOut(BaseModel):
    id: int
    question_id: int
    user_answer: str
    is_correct: bool
    time_spent: float
    mode: str
    created_at: str | None = None
    model_config = {"from_attributes": True}


class LevelProgressOut(BaseModel):
    level_id: int
    stars: int
    unlocked: bool
    best_combo: int
    model_config = {"from_attributes": True}


class UserStatsOut(BaseModel):
    total_questions: int
    total_correct: int
    total_score: int
    power_score: int
    max_combo: int
    practice_count: int
    extreme_passes: int
    extreme_dual_passes: int
    model_config = {"from_attributes": True}


class SyncStatsIn(BaseModel):
    practice_increment: int = 0       # 每次进入练习+1
    extreme_pass_increment: int = 0   # 通过极限挑战+1
    extreme_dual_pass_increment: int = 0  # 双单元极限+1
