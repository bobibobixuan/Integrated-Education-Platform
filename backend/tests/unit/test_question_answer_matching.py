from types import SimpleNamespace

from backend.app.services.question_service import is_submitted_answer_correct


def test_choice_question_accepts_option_text_when_answer_is_letter():
    question = SimpleNamespace(
        type="选择题",
        answer="A",
        options=[
            {"letter": "A", "text": "自然语言"},
            {"letter": "B", "text": "机器语言"},
        ],
    )

    assert is_submitted_answer_correct(question, "自然语言") is True


def test_choice_question_accepts_option_letter_when_answer_is_text():
    question = SimpleNamespace(
        type="选择题",
        answer="自然语言",
        options=[
            {"letter": "A", "text": "自然语言"},
            {"letter": "B", "text": "机器语言"},
        ],
    )

    assert is_submitted_answer_correct(question, "A") is True


def test_choice_question_rejects_wrong_option_text():
    question = SimpleNamespace(
        type="选择题",
        answer="A",
        options=[
            {"letter": "A", "text": "自然语言"},
            {"letter": "B", "text": "机器语言"},
        ],
    )

    assert is_submitted_answer_correct(question, "机器语言") is False


def test_non_choice_question_still_uses_direct_answer_matching():
    question = SimpleNamespace(
        type="填空题",
        answer="python",
        options=None,
    )

    assert is_submitted_answer_correct(question, "Python") is True
