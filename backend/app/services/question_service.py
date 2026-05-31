from __future__ import annotations
import re
from typing import Any

QUESTION_TYPE_ALIASES = {
    "choice": "选择题", "single_choice": "选择题", "single-choice": "选择题", "选择题": "选择题",
    "multi": "多选题", "multi_choice": "多选题", "multi-choice": "多选题", "多选题": "多选题",
    "truefalse": "判断题", "true_false": "判断题", "boolean": "判断题", "judge": "判断题", "判断题": "判断题",
    "fill": "填空题", "blank": "填空题", "fill_blank": "填空题", "填空题": "填空题",
}
FILL_ANSWER_SEPARATOR_RE = re.compile(r"[;；]+")
JUDGEMENT_TRUE_TOKENS = {"a", "true", "对", "正确", "是", "√", "1", "t", "yes", "y"}
JUDGEMENT_FALSE_TOKENS = {"b", "false", "错", "错误", "否", "×", "0", "f", "no", "n"}


def normalize_question_type(raw_type: Any) -> str:
    key = str(raw_type or "").strip()
    normalized = QUESTION_TYPE_ALIASES.get(key)
    if not normalized:
        raise ValueError(f"无效的题目类型 '{raw_type}'")
    return normalized


def normalize_question_options(raw_options: Any, question_type: str) -> list[dict[str, str]] | None:
    if question_type not in ("选择题", "多选题"):
        return None
    if not isinstance(raw_options, list) or len(raw_options) < 2:
        raise ValueError("选择题至少需要 2 个选项")
    normalized: list[dict[str, str]] = []
    for i, item in enumerate(raw_options):
        if not isinstance(item, dict):
            raise ValueError(f"第 {i + 1} 个选项格式错误")
        letter = str(item.get("letter") or item.get("label") or "").strip()
        text = str(item.get("text") or "").strip()
        if not letter or not text:
            raise ValueError(f"第 {i + 1} 个选项缺少 letter/text")
        normalized.append({"letter": letter, "text": text})
    return normalized


def _normalize_answer_token(value: Any) -> str:
    return str(value or "").strip().lower()


def split_fill_answer_variants(value: Any) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    parts = [part.strip() for part in FILL_ANSWER_SEPARATOR_RE.split(raw)]
    return [part.lower() for part in parts if part.strip()]


def normalize_judgement_token(value: Any) -> str:
    token = _normalize_answer_token(value)
    if token in JUDGEMENT_TRUE_TOKENS:
        return "a"
    if token in JUDGEMENT_FALSE_TOKENS:
        return "b"
    return token


def _looks_like_multi_answer(answer: Any) -> bool:
    raw = str(answer or "").strip().upper()
    if len(raw) <= 1:
        return False
    return raw.isascii() and raw.isalpha()


def get_effective_question_type(question_or_type: Any, answer: Any | None = None, options: Any | None = None) -> str:
    if hasattr(question_or_type, "type"):
        raw_type = getattr(question_or_type, "type", "")
        raw_answer = getattr(question_or_type, "answer", "")
        raw_options = getattr(question_or_type, "options", None)
    else:
        raw_type = question_or_type
        raw_answer = answer
        raw_options = options

    normalized = normalize_question_type(raw_type)
    if normalized == "选择题" and isinstance(raw_options, list) and _looks_like_multi_answer(raw_answer):
        return "多选题"
    return normalized


def _is_choice_question(question_type: Any) -> bool:
    key = str(question_type or "").strip()
    return QUESTION_TYPE_ALIASES.get(key) == "选择题"


def is_submitted_answer_correct(question: Any, submitted_answer: Any) -> bool:
    submitted = _normalize_answer_token(submitted_answer)
    expected = _normalize_answer_token(getattr(question, "answer", ""))
    if not submitted or not expected:
        return False

    if submitted == expected:
        return True

    # Multi-select: compare sorted letters (e.g., "AB" == "BA")
    question_type_normalized = get_effective_question_type(question)
    if question_type_normalized == "多选题":
        return sorted(submitted) == sorted(expected)

    if question_type_normalized == "填空题":
        accepted_answers = split_fill_answer_variants(getattr(question, "answer", ""))
        return submitted in accepted_answers

    if question_type_normalized == "判断题":
        return normalize_judgement_token(submitted_answer) == normalize_judgement_token(getattr(question, "answer", ""))

    if question_type_normalized != "选择题":
        return False

    options = getattr(question, "options", None)
    if not isinstance(options, list):
        return False

    selected_index: int | None = None
    correct_index: int | None = None

    for index, item in enumerate(options):
        if not isinstance(item, dict):
            continue
        letter = _normalize_answer_token(item.get("letter"))
        text = _normalize_answer_token(item.get("text"))
        if submitted in {letter, text}:
            selected_index = index
        if expected in {letter, text}:
            correct_index = index

    return selected_index is not None and selected_index == correct_index


def build_question_title(title: Any, content: Any) -> str:
    title_text = str(title or "").strip()
    if title_text:
        return title_text
    content_text = str(content or "").strip()
    return content_text[:36] if len(content_text) <= 36 else content_text[:36] + "..."
