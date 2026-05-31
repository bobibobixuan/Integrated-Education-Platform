from pydantic import BaseModel, Field


class AdminUserOut(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    is_active: bool
    created_at: str | None = None
    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    nickname: str | None = None
    role: str | None = None
    is_active: bool | None = None
    force_password_change: bool | None = None
    new_password: str | None = Field(None, min_length=4)


class QuestionUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    type: str | None = None
    answer: str | None = None
    options: list[dict[str, str]] | None = None
    level_id: int | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    knowledge_meaning: str | None = None
    knowledge_rule: str | None = None
    knowledge_error: str | None = None
    knowledge_example: str | None = None


class QuestionCreate(BaseModel):
    title: str = ""
    content: str
    type: str
    answer: str
    options: list[dict[str, str]] | None = None
    level_id: int
    sort_order: int = 0
    knowledge_meaning: str = ""
    knowledge_rule: str = ""
    knowledge_error: str = ""
    knowledge_example: str = ""
