from pydantic import BaseModel, Field


class PvpRoomMutationIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    group_size: int = Field(..., ge=2, le=12)
    member_user_ids: list[int] = []
    question_unit_ids: list[int] = []
    question_count: int = Field(..., ge=2, le=50)
    battle_time_limit_seconds: int = 0


class StudentPvpRoomCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    group_size: int = Field(..., ge=2, le=12)
    question_unit_ids: list[int] = Field(..., min_length=1)
    question_count: int = Field(..., ge=2, le=50)
    battle_time_limit_seconds: int = 0


class PvpReadyUpdateIn(BaseModel):
    is_ready: bool


class PvpBattleAnswerIn(BaseModel):
    play_session_id: str
    question_id: int
    submitted_answer: str
    client_time_spent: float = 0.0


class PvpBattleQuestionOut(BaseModel):
    id: int
    level_id: int
    type: str
    content: str
    options: list[dict] | None = None
    question_order: int = 0
    total_questions: int = 0


class PvpBattleAnswerOut(BaseModel):
    success: bool
    is_correct: bool
    correct_answer: str = ""
    battle_power_delta: int = 0
    current_battle_power: int = 0
    session_status: str = ""
    question_count: int = 0
    knowledge: dict | None = None
    next_question: PvpBattleQuestionOut | None = None


class PvpBattleSessionOut(BaseModel):
    room: dict
    play_session_id: str
    session_status: str
    question_count: int
    current_question: PvpBattleQuestionOut | None = None


class PvpBattleFinalizeIn(BaseModel):
    play_session_id: str


class PvpRoomLogOut(BaseModel):
    id: int
    room_id: int | None = None
    message: str
    category: str = "system"
    created_at: str | None = None


class PvpRoomOut(BaseModel):
    id: int
    title: str
    description: str = ""
    group_size: int
    status: str
    mode: str = "ffa"
    ranking_metric: str = "battle_power"
    question_unit_ids: list[int] = []
    question_count: int = 10
    battle_time_limit_seconds: int = 0
    member_count: int = 0
    ready_count: int = 0
    members: list[dict] = []
    logs: list[dict] | None = None
    created_at: str | None = None
    server_now: str | None = None
    countdown_started_at: str | None = None
    auto_start_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    battle_started_at: str | None = None
    battle_expires_at: str | None = None


class StudentPvpRoomOut(BaseModel):
    room: PvpRoomOut | None = None
