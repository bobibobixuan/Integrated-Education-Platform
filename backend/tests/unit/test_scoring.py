from backend.app.services.scoring_service import calc_stars, calc_combo, is_extreme_pass, calc_power_bonus


class TestCalcStars:
    def test_zero_questions_returns_zero(self):
        assert calc_stars(0, 0) == 0

    def test_full_score_returns_three_stars(self):
        assert calc_stars(10, 10) == 3

    def test_below_sixty_returns_zero(self):
        assert calc_stars(3, 10) == 0

    def test_above_eighty_below_hundred_returns_two(self):
        assert calc_stars(8, 10) == 2

    def test_exactly_sixty_returns_one(self):
        assert calc_stars(6, 10) == 1


class TestCalcCombo:
    def test_correct_increments_combo(self):
        assert calc_combo(True, 3) == 4

    def test_wrong_resets_combo(self):
        assert calc_combo(False, 5) == 0

    def test_first_correct_sets_combo_to_1(self):
        assert calc_combo(True, 0) == 1


class TestIsExtremePass:
    def test_correct_and_fast_is_extreme(self):
        assert is_extreme_pass(True, 5.0) is True

    def test_correct_but_slow_is_not_extreme(self):
        assert is_extreme_pass(True, 15.0) is False

    def test_wrong_is_not_extreme_even_if_fast(self):
        assert is_extreme_pass(False, 2.0) is False


class TestCalcPowerBonus:
    def test_wrong_answer_returns_zero(self):
        assert calc_power_bonus(False, 3, 5.0) == 0

    def test_correct_no_combo_returns_base(self):
        assert calc_power_bonus(True, 1, 10.0) == 100

    def test_correct_fast_returns_bonus(self):
        assert calc_power_bonus(True, 1, 3.0) == 110

    def test_correct_high_combo_returns_bonus(self):
        result = calc_power_bonus(True, 5, 10.0)
        assert result == 140
