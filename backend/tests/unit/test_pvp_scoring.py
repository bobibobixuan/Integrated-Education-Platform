"""Unit tests for PvP scoring logic (calculate_answer_battle_delta, update_member_battle_state)."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from backend.app.services.pvp_service import calculate_answer_battle_delta, update_member_battle_state


class TestCalculateAnswerBattleDelta:
    """Pure function tests (no DB needed)."""

    def test_wrong_answer_always_negative_45(self):
        """Wrong answer always returns -45 regardless of speed or streak."""
        assert calculate_answer_battle_delta(is_correct=False, effective_time=2.0, current_streak=0) == -45
        assert calculate_answer_battle_delta(is_correct=False, effective_time=10.0, current_streak=5) == -45
        assert calculate_answer_battle_delta(is_correct=False, effective_time=30.0, current_streak=99) == -45

    def test_correct_answer_base(self):
        """Correct answer with normal speed and no streak: base 100."""
        assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=0) == 100

    def test_correct_answer_fast_bonus(self):
        """Correct answer within 5s: +10 speed bonus."""
        assert calculate_answer_battle_delta(is_correct=True, effective_time=5.0, current_streak=0) == 110
        assert calculate_answer_battle_delta(is_correct=True, effective_time=3.0, current_streak=0) == 110
        assert calculate_answer_battle_delta(is_correct=True, effective_time=0.5, current_streak=0) == 110

    def test_fast_bonus_only_applies_at_or_under_5s(self):
        """5.01s should NOT get speed bonus (just above threshold)."""
        assert calculate_answer_battle_delta(is_correct=True, effective_time=5.01, current_streak=0) == 100

    def test_combo_starts_at_streak_2(self):
        """Combo bonus starts at streak=2: +10, streak=3: +20."""
        assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=0) == 100   # no combo
        assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=1) == 100   # no combo
        assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=2) == 110   # +10
        assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=3) == 120   # +20

    def test_combo_capped_at_five_tiers(self):
        """Combo bonus capped at 5 tiers (streak=6 → +50, streak=10 → +50)."""
        assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=6) == 150   # max combo +50
        assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=10) == 150  # still +50
        assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=100) == 150  # still +50

    def test_speed_and_combo_stack(self):
        """Fast answer + high combo stack additively."""
        assert calculate_answer_battle_delta(is_correct=True, effective_time=3.0, current_streak=5) == 150  # 100 + 10(fast) + 40(combo)
        assert calculate_answer_battle_delta(is_correct=True, effective_time=3.0, current_streak=6) == 160  # 100 + 10(fast) + 50(combo cap)

    def test_exact_streak_boundaries(self):
        """Verify combo values at each streak boundary."""
        for streak, expected_combo_bonus in [(0, 0), (1, 0), (2, 10), (3, 20), (4, 30), (5, 40), (6, 50), (7, 50)]:
            base = 100
            expected = base + expected_combo_bonus
            assert calculate_answer_battle_delta(is_correct=True, effective_time=10.0, current_streak=streak) == expected


class TestUpdateMemberBattleState:
    """Integration-style tests requiring a real ORM PvpRoomMember."""

    @pytest.fixture
    def room(self, db_session: Session):
        from backend.app.models.pvp import PvpRoom
        room = PvpRoom(
            title="Test Room",
            group_size=4,
            question_count=10,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(room)
        db_session.flush()
        return room

    @pytest.fixture
    def member(self, db_session: Session, room, request):
        from backend.app.models.pvp import PvpRoomMember
        member = PvpRoomMember(
            room_id=room.id,
            user_id=1,
            seat_order=0,
        )
        db_session.add(member)
        db_session.flush()
        return member

    def test_first_correct_answer_no_speed_no_combo(self, member):
        """First correct answer: answered_count=1, correct=1, streak=1, delta=100."""
        delta = update_member_battle_state(member, is_correct=True, effective_time=15.0)
        assert delta == 100
        assert member.live_answered_count == 1
        assert member.live_correct_count == 1
        assert member.live_wrong_count == 0
        assert member.current_streak == 1
        assert member.best_streak == 1
        assert member.live_battle_power == 100

    def test_first_answer_wrong(self, member):
        """First answer wrong: answered_count=1, wrong=1, streak=0, delta=-45."""
        delta = update_member_battle_state(member, is_correct=False, effective_time=5.0)
        assert delta == -45
        assert member.live_answered_count == 1
        assert member.live_correct_count == 0
        assert member.live_wrong_count == 1
        assert member.current_streak == 0
        assert member.best_streak == 0
        assert member.live_battle_power == -45

    def test_correct_after_wrong_resets_streak_then_increments(self, member):
        """Wrong breaks streak (to 0), then correct: streak goes 0→1, normal base score."""
        update_member_battle_state(member, is_correct=False, effective_time=5.0)  # streak=0
        delta = update_member_battle_state(member, is_correct=True, effective_time=10.0)  # streak 0→1
        assert delta == 100  # no combo yet (streak=1 → combo_bonus=0)
        assert member.current_streak == 1

    def test_combo_builds_over_multiple_correct(self, member):
        """3 consecutive correct answers: combo builds: streaks 1→2→3, with increasing combo bonus."""
        d1 = update_member_battle_state(member, is_correct=True, effective_time=10.0)  # streak 0→1, delta=100
        assert d1 == 100
        assert member.live_battle_power == 100

        d2 = update_member_battle_state(member, is_correct=True, effective_time=10.0)  # streak 1→2, delta with streak=2 = 110
        assert d2 == 110
        assert member.live_battle_power == 210

        d3 = update_member_battle_state(member, is_correct=True, effective_time=10.0)  # streak 2→3, delta with streak=3 = 120
        assert d3 == 120
        assert member.live_battle_power == 330

    def test_delta_override(self, member):
        """When delta_override is provided, use it instead of calculating."""
        delta = update_member_battle_state(member, is_correct=True, effective_time=10.0, delta_override=999)
        assert delta == 999
        assert member.live_battle_power == 999
        # State mutations still happen
        assert member.live_correct_count == 1
        assert member.current_streak == 1

    def test_last_answer_at_updated(self, member):
        """last_answer_at should be set after update."""
        assert member.last_answer_at is None
        update_member_battle_state(member, is_correct=True, effective_time=5.0)
        assert member.last_answer_at is not None
        assert member.last_answer_at.tzinfo is not None  # timezone-aware
